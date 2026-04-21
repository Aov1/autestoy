"""串口协议"""

import re
import time

# from multiprocessing import get_all_start_methods
from typing import Any, Generator, Iterable, Self, override

import serial

from autestoy.tools.control import get_line_from_head

from ..export.collect import CollectObj, CollectType, collect
from ..export.term import PROMPT_pattern as prompt_pattern_default
from ..export.term import Term
from ..tools.ansi import remove_ansi
from ..tools.record import CmdRecord, MetaRecord


class SerialConfig:
    def __init__(
        self,
        port: str | None = None,
        baudrate: int = 115200,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: float = 1,
        timeout: float | None = 0.05,
        xonxoff: bool = False,
        rtscts: bool = False,
        write_timeout: float | None = None,
        dsrdtr: bool = False,
        inter_byte_timeout: float | None = None,
        exclusive: bool | None = None,
    ) -> None:
        """对于pyseriel模块Serial类初始化参数的简单复制，并修改一些默认参数"""
        self.port: str | None = port
        self.baudrate: int = baudrate
        self.bytesize: int = bytesize
        self.parity: str = parity
        self.stopbits: float = stopbits
        self.timeout: float | None = timeout
        self.xonxoff: bool = xonxoff
        self.rtscts: bool = rtscts
        self.write_timeout: float | None = write_timeout
        self.dsrdtr: bool = dsrdtr
        self.inter_byte_timeout: float | None = inter_byte_timeout
        self.exclusive: bool | None = exclusive
        self.args: dict[str, Any] = {
            "port": port,
            "baudrate": baudrate,
            "bytesize": bytesize,
            "parity": parity,
            "stopbits": stopbits,
            "timeout": timeout,
            "xonxoff": xonxoff,
            "rtscts": rtscts,
            "write_timeout": write_timeout,
            "dsrdtr": dsrdtr,
            "inter_byte_timeout": inter_byte_timeout,
            "exclusive": exclusive,
        }
        # add
        self.name = f"{self.port}@{str(self.baudrate)}"

    def set_name(self, name: str) -> Self:
        self.name = name
        return self


@collect(CollectType.Serial, CollectObj)
class Serial:
    read_size = 1024

    def __init__(
        self,
        serial_config: SerialConfig,
    ) -> None:
        # info
        self.config = serial_config
        self.name: str = self.config.name
        self.meta_record: MetaRecord = MetaRecord(
            type="Serial",
            name=self.name,
            info=f"[{self.config.port}@{self.config.baudrate}]",
        )
        self.last_cmd: CmdRecord | None = None
        self.cmds: list[CmdRecord] = []
        # open serial
        self.com: serial.Serial = serial.Serial(**self.config.args)

    def send(self, data: bytes) -> None:
        """对于pyserial Serial().write()的简单包装"""
        self.com.write(data)

    def recv_no_block(self, size: int = 1) -> bytes:
        """对于pyserial Serial().read()的简单包装"""
        return self.com.read(size)

    def recv_until(self, re_delimiter: bytes) -> tuple[bytes, re.Match[bytes]]:
        """读取直到遇到指定的字符,支持正则\n
        由于无法访问到pyserial维护的buffer,采取逐行读取,按行进行判断。\n
        会多消耗该行字符\n"""
        buf = b""
        while not (res := re.search(re_delimiter, line := self.com.readline())):
            buf += line
        return buf, res

    def readline_generator(self) -> Generator[tuple[bool, str], None, None]:
        """返回一个生成器，逐行读取串口输出，返回生成器的子类型tuple[bool,str]"""
        buf = b""
        while True:
            buf += self.recv_no_block(Serial.read_size)
            while b"\n" in buf or b"\r\n" in buf:
                buf = buf.replace(b"\r\n", b"\n").replace(b"\r", b"")
                line, buf = buf.split(b"\n", 1)
                yield True, line.decode("utf-8", errors="ignore")
            else:
                yield False, buf.decode("utf-8", errors="ignore")

    def recv_bytes_generator(self) -> Generator[bytes | None, None, None]:
        """返回一个生成器，逐字节读取串口输出，没有获取到字节返回None"""
        while True:
            buf = self.recv_no_block(Serial.read_size)
            if buf:
                yield buf
            else:
                yield None

    def recv_string_generator(self) -> Generator[str | None, None, None]:
        """返回一个生成器，读取串口输出，没有获取到一行返回None"""
        while True:
            buf = self.recv_no_block(Serial.read_size)
            if buf:
                yield buf.decode("utf-8", errors="ignore")
            else:
                yield None


class SerialShell(Serial):
    def __init__(
        self,
        serial_config: SerialConfig,
        user_and_password: tuple[str, str] | None = None,
        prompt_pattern: str = prompt_pattern_default,
    ):
        # 父类初始化
        super().__init__(serial_config)
        # conf
        self.user, self.password = (
            user_and_password if user_and_password is not None else (None, None)
        )
        self.prompt_pattern = re.compile(prompt_pattern)
        self.prompt_now: str | None = None
        # conf
        self.f_get_exit_code: bool = False

        if user_and_password is not None:
            self.prompt_now = self.login()
        else:
            self.prompt_now = self.get_prompt()
        print(f"[DBG]{self.prompt_now = }")

    def conf_get_exit_code(self, enable: bool = False) -> None:
        """配置串口终端是否在命令后获取退出码，默认不获取以适配功能不完全的简单模拟终端"""
        self.f_get_exit_code = enable

    def login(
        self,
        step_timeout: float | None = None,
        re_user: str = r"([lL]ogin)|([Uu]sername)|([Hh]ostname)\s*[:：]",
        re_password: str = r"([Pp]assword)\s*[:：]",
    ) -> str:
        """登录串口终端，返回登录后的提示符\n
        step_timeout: 每个步骤的超时时间，默认为5秒\n
        方法未测试,无环境"""
        username = self.user if self.user is not None else ""
        password = self.password if self.password is not None else ""
        buf = ""
        gen = self.recv_string_generator()
        wait_timeout = step_timeout if step_timeout is not None else 5
        stt = time.time()
        while time.time() - stt < wait_timeout:
            if (line := next(gen)) is not None:
                buf += line
            while "\n" in buf:
                line, buf = get_line_from_head(buf)
            if re.search(re_user, remove_ansi(buf)):
                break
        self.send(username.encode() + b"\n")
        stt = time.time()
        while time.time() - stt < wait_timeout:
            if (line := next(gen)) is not None:
                buf += line
            while "\n" in buf:
                line, buf = get_line_from_head(buf)
            if re.search(re_password, remove_ansi(buf)):
                break
        self.send(password.encode() + b"\n")
        stt = time.time()
        while time.time() - stt < wait_timeout:
            if (line := next(gen)) is not None:
                buf += line
                if prompt := self.prompt_pattern.search(remove_ansi(buf)):
                    return prompt.group()
        raise RuntimeError("login failed")

    def get_prompt(self) -> str | None:
        """当串口作为终端调试工具时获取终端提示符"""
        # 清空缓冲
        while self.com.read(Serial.read_size) != b"":
            time.sleep(0.01)
        tmp = b""
        self.com.write(b"\n")
        # 等待缓冲非空
        while (res := self.com.read(Serial.read_size)) == b"":
            time.sleep(0.01)
        tmp += res
        while (res := self.com.read(Serial.read_size)) != b"":
            tmp += res
            time.sleep(0.01)
        # print(f"{tmp.decode() = }")
        # print(f"{remove_ansi(tmp.decode()).strip() = }")
        tmp = remove_ansi(tmp).decode().strip()
        if self.prompt_pattern.search(tmp):
            return tmp
        return None

    def shell_run(self, cmd: str) -> CmdRecord:
        """串口以终端交互模式运行命令，捕获终端提示符确认退出"""
        record = CmdRecord[str](
            cmd=cmd, prompt=f"[Serial][{self.name}]{self.prompt_now}"
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        for line in self._run_line_generator(cmd):
            timestamp, _ = Term.putsln(line)
            record.result_append(line, timestamp)

        if self.f_get_exit_code:
            exit_code = next(self._run_line_generator("echo $?"))
            if exit_code.isdigit():
                record.exit_code = int(exit_code)
        record.record_end()
        return record

    def shell_run_sudo(self, cmd: str, password: str) -> CmdRecord[str]:
        """串口终端模式sudo提权运行,只提权运行一次,运行后清除sudo缓存"""
        processed_cmd = f"sudo -k -S {cmd}"
        record = CmdRecord(
            cmd=cmd, prompt=f"[Serial][{self.name}][sudo]{self.prompt_now}"
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())

        self.send(processed_cmd.encode() + b"\n")
        self.com.read_until(b":")
        self.com.readline()  # 去除输入密码行
        self.send(password.encode() + b"\n")
        self.com.readline()  # 去除回显行

        for is_output, line in self.readline_generator():
            if is_output:
                timestamp, _ = Term.putsln(line)
                record.result_append(line, timestamp)

        if self.f_get_exit_code:
            exit_code = next(self._run_line_generator("echo $?"))
            if exit_code.isdigit():
                record.exit_code = int(exit_code)
        record.record_end()

        for _ in self._run_line_generator("sudo -K"):
            pass

        return record

    def _run_line_generator(self, cmd: str) -> Generator[str, None, None]:
        """生成器方式逐行返回终端交互模式的输出，跳过回显,要求配置完备终端提示符捕获，否则无法退出"""
        # 清空缓冲
        while self.com.read(Serial.read_size) != b"":
            time.sleep(0.01)
        tmp = b""
        self.com.write(f"{cmd}\n".encode())
        # 等待缓冲非空
        while (res := self.com.read(Serial.read_size)) == b"":
            time.sleep(0.01)
        tmp += res

        found_cmd = False
        found_prompt = False
        while True:
            tmp += self.com.read(Serial.read_size)
            tmp = tmp.replace(b"\r\n", b"\n")
            while b"\n" in tmp:
                line_b, tmp = tmp.split(b"\n", 1)
                line = line_b.decode().replace("\r", "")

                if cmd in line and not found_cmd:
                    found_cmd = True
                    continue

                if self.prompt_pattern.search(line):
                    found_prompt = True
                    break

                yield line
            else:
                if self.prompt_pattern.search(tmp.decode()):
                    found_prompt = True
            if found_prompt:
                return

    @override
    def readline_generator(self) -> Generator[tuple[bool, str], None, None]:
        """生成器方式逐行返回终端交互模式的输出，终端提示符捕获退出\n
        override父类方法,返回的(bool,str)中bool代表是否是完整的行,在交互命令中完整行即命令输出,不完整行即终端提示符\n
        True: 命令输出\n
        False: 终端提示符"""
        tmp = b""
        found_prompt = False
        while True:
            tmp += self.com.read(Serial.read_size)
            tmp = tmp.replace(b"\r\n", b"\n")
            while b"\n" in tmp:
                line_b, tmp = tmp.split(b"\n", 1)
                line = line_b.decode().replace("\r", "")

                if self.prompt_pattern.search(remove_ansi(line)):
                    found_prompt = True
                    yield False, line.strip()
                    return

                yield True, line
            else:
                if self.prompt_pattern.search(remove_ansi(tmp.decode())):
                    found_prompt = True
                    yield False, tmp.decode().strip()
                    return
            if found_prompt:
                return

    def shell_run_lines(self, *cmds: str | Iterable[str]) -> list[CmdRecord]:
        results: list[CmdRecord[str]] = []

        for cmd in cmds:
            if isinstance(cmd, str):
                if "\n" in cmd or "\r\n" in cmd:  # 多行命令单个字符串
                    cmd_list = cmd.splitlines()
                    cmd_list = [
                        e.strip()
                        for e in cmd_list
                        if not e.strip().endswith("#") and e.strip() != ""
                    ]
                    results.extend(self.shell_run_lines(cmd_list))
                else:  # 单个命令字符串
                    results.append(self.shell_run(cmd))
            elif isinstance(cmd, Iterable):
                results.extend(self.shell_run_lines(*cmd))
        return results
