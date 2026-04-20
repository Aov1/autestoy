"""telnet协议"""

import re
import time
from typing import Generator

from telnetlib3.sync import TelnetConnection

from autestoy.tools.ansi import remove_ansi

from ..export.term import PROMPT_pattern, Term
from ..tools.record import CmdRecord


class TelnetConfig:
    def __init__(
        self,
        name: str,
        host: str,
        port: int = 23,
        user: str | None = None,
        password: str | None = None,
        timeout: float | None = None,
        encoding: str = "utf-8",
        prompt_pattern: str = PROMPT_pattern,
    ) -> None:
        """Telnet配置，用于创建Telnet连接\n
        在user与password都为None时不进行登陆操作"""
        self.name = name
        # for telnetlib3 TelnetConnection
        self.host: str = host
        self.port: int = port
        self.timeout: float | None = timeout
        self.encoding: str = encoding
        # for login
        self.user: str | None = user
        self.password: str | None = password
        self.prompt_pattern: str = PROMPT_pattern


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
        self.prompt_pattern = re.compile(telnet_conf.prompt_pattern)
        self.tel3.connect()
        if not self.is_connected():
            raise RuntimeError(
                f"[Telnet] {telnet_conf.host}:{telnet_conf.port} Not connected"
            )
        if self.conf.user is not None or self.conf.password is not None:
            self.prompt = self._login(telnet_conf.user, telnet_conf.password)
        self.cmds: list[CmdRecord] = []

    def is_connected(self) -> bool:
        return self.tel3._connected and self.tel3 is not None

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
            res = self.recv_no_wait()
            buf += res
            if "incorrect" in buf:
                raise RuntimeError("Login incorrect")
            if prompt := self.prompt_pattern.search(remove_ansi(buf)):
                return prompt.group()
        raise RuntimeError("Login timeout")

    def send(self, data: str) -> None:
        self.tel3.write(data)

    def recv_no_wait(self) -> str:
        """接收telnet输出，非阻塞，无内容返回空字符"""
        try:
            res = self.tel3.read_some(0.01)
        except TimeoutError:
            return ""
        return res.decode() if isinstance(res, bytes) else res

    def recv(self) -> str:
        """接收telnet输出，直到有非空字符串"""
        while (res := self.recv_no_wait()) == "":
            pass
        return res

    def shell_run_line_generator(self, cmd: str) -> Generator[str, None, None]:
        """逐行生成telnet输出"""
        self.send(cmd + "\n")
        buf = ""
        skip_cmd = False
        while True:
            buf += self.recv_no_wait()
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
