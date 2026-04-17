"""串口协议"""

import re
import time
from multiprocessing import get_all_start_methods
from typing import Any, Generator, Iterable

import serial

from ..export.collect import CollectObj, CollectType, collect
from ..export.term import Term
from ..tools.ansi import remove_ansi, remove_ansi_bytes
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


@collect(CollectType.Serial, CollectObj)
class Serial:
    read_size = 1024
    prompt_pattern_default = r"(?:[\w@\-\.\[\]]+[:~/\w\-\. ]*|[:~/\w\-\. ]+)?[\$#]\s*$"

    def __init__(
        self,
        name: str,
        serial_config: SerialConfig,
        shell_mode: bool = False,
        shell_mode_prompt_pattern: str = prompt_pattern_default,
    ) -> None:
        # info
        self.name: str = name
        self.config = serial_config
        self.meta_record: MetaRecord = MetaRecord(
            type="Serial",
            name=self.name,
            info=f"[{self.config.port}@{self.config.baudrate}]",
        )
        self.last_cmd: CmdRecord | None = None
        self.cmds: list[CmdRecord] = []
        # serial
        self.com: serial.Serial = serial.Serial(**self.config.args)
        self.prompt_pattern = re.compile(shell_mode_prompt_pattern)
        self.prompt: str | None = None
        # conf
        self.conf_shell_mode: bool = False
        self.conf_shell_get_exit_code: bool = False
        self.shell_mode(shell_mode)

    def shell_mode(self, enable: bool, get_exit_code: bool = False) -> None:
        """配置串口是否使用终端模式，未开启时不可使用shell_run方法"""
        self.conf_shell_mode = enable
        self.conf_shell_get_exit_code = get_exit_code

    def shell_mode_get_prompt(self) -> str | None:
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
        tmp = remove_ansi_bytes(tmp).decode().strip()
        if self.prompt_pattern.search(tmp):
            return tmp
        return None

    def shell_run(self, cmd: str) -> CmdRecord:
        """串口以终端交互模式运行命令，捕获终端提示符确认退出"""
        if not self.conf_shell_mode:
            raise ValueError(
                "shell mode not enabled,use .shell_mode(True) first or initialize with shell_mode=True"
            )
        tmp_prompt = (
            self.prompt if self.prompt is not None else self.shell_mode_get_prompt()
        )
        record = CmdRecord[str](
            cmd=cmd,
            prompt="[Serial]" + tmp_prompt if tmp_prompt is not None else "",
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        for line in self._run(cmd):
            timestamp, _ = Term.putsln(line)
            record.result_append(line, timestamp)

        if self.conf_shell_get_exit_code:
            exit_code = next(self._run("echo $?"))
            if exit_code.isdigit():
                record.exit_code = int(exit_code)
        record.record_end()
        return record

    def _run(self, cmd: str) -> Generator[str, None, None]:
        """生成器方式逐行返回终端交互模式的输出，要求配置完备终端提示符捕获，否则无法退出"""
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
