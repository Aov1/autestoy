"""telnet协议"""

import re
import time
from typing import Generator, Self

from telnetlib3.sync import TelnetConnection

from autestoy.tools.ansi import remove_ansi

from ..export.term import PROMPT_pattern as prompt_pattern_default
from ..export.term import Term
from ..tools.record import CmdRecord


class TelnetConfig:
    def __init__(
        self,
        host: str,
        port: int = 23,
        timeout: float | None = None,
        encoding: str = "utf-8",
    ) -> None:
        """Telnet配置，用于创建Telnet连接\n
        在user与password都为None时不进行登陆操作"""
        # for telnetlib3 TelnetConnection
        self.host: str = host
        self.port: int = port
        self.timeout: float | None = timeout
        self.encoding: str = encoding
        # name
        self.name = f"{host}:{port}"

    def set_name(self, name: str) -> Self:
        self.name = name
        return self


class Telnet:
    def __init__(self, telnet_conf: TelnetConfig) -> None:
        self.conf = telnet_conf
        self.name = telnet_conf.name
        self.tel3 = TelnetConnection(
            host=telnet_conf.host,
            port=telnet_conf.port,
            timeout=telnet_conf.timeout,
            encoding=telnet_conf.encoding,
        )
        self.tel3.connect()
        if not self.is_connected():
            raise RuntimeError(
                f"[Telnet] {telnet_conf.host}:{telnet_conf.port} Not connected"
            )

    def is_connected(self) -> bool:
        return self.tel3._connected and self.tel3 is not None

    def send(self, data: str) -> None:
        self.tel3.write(data)

    def recv_no_block(self) -> str:
        """接收telnet输出，非阻塞，无内容返回空字符"""
        try:
            res = self.tel3.read_some(0.01)
        except TimeoutError:
            return ""
        return res.decode() if isinstance(res, bytes) else res

    def recv_block(self) -> str:
        """接收telnet输出，直到有非空字符串"""
        while (res := self.recv_no_block()) == "":
            pass
        return res


class TelnetShell(Telnet):
    def __init__(
        self,
        telnet_conf: TelnetConfig,
        user_and_password: tuple[str | None, str | None] = (None, None),
        prompt_pattern: str = prompt_pattern_default,
    ) -> None:
        super().__init__(telnet_conf)
        self.user: str | None = user_and_password[0]
        self.password: str | None = user_and_password[1]

        self.prompt_pattern = re.compile(prompt_pattern)

        # 是否登陆
        if self.user is not None or self.password is not None:
            self.prompt = self._login(self.user, self.password)
        self.cmds: list[CmdRecord] = []

    def _login(
        self, user: str | None = None, password: str | None = None
    ) -> str | None:
        res = self.tel3.read_until("login:")
        self.tel3.write(f"{user}\n" if user is not None else "\n")
        res = self.tel3.read_until("Password:")
        self.tel3.write(f"{password}\n" if password is not None else "\n")
        buf = ""
        st = time.time()
        while time.time() - st < 5:
            res = self.recv_no_block()
            buf += res
            if "incorrect" in buf:
                raise RuntimeError("Login incorrect")
            if prompt := self.prompt_pattern.search(remove_ansi(buf)):
                return prompt.group()
        raise RuntimeError("Login timeout")

    def shell_run_line_generator(self, cmd: str) -> Generator[str, None, None]:
        """逐行生成telnet输出"""
        self.send(cmd + "\n")
        buf = ""
        skip_cmd = False
        while True:
            buf += self.recv_no_block()
            while "\n" in buf or "\r\n" in buf:
                buf = buf.replace("\r\n", "\n").replace("\r", "")
                line, buf = buf.split("\n", 1)

                if not skip_cmd and cmd in line:
                    skip_cmd = True
                    continue

                if self.prompt_pattern.search(line):
                    return

                yield line
            else:
                if skip_cmd and self.prompt_pattern.search(buf):
                    return

    def shell_run(self, cmd: str) -> CmdRecord[str]:
        """执行shell命令，返回输出"""
        record = CmdRecord(
            cmd=cmd,
            prompt=f"[{self.name}][{self.conf.host}:{self.conf.port}]{self.prompt}",
        )
        self.cmds.append(record)
        record.start_time, _ = Term.putsln(record.get_fmt_prompt())
        for line in self.shell_run_line_generator(cmd):
            timestamp, _ = Term.putsln(line)
            record.result_append(line, timestamp)
        record.record_end()
        return record
