"""telnet协议"""

import re

from telnetlib3.sync import TelnetConnection

from autestoy.tools.ansi import remove_ansi

from ..export.term import PROMPT_pattern


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

    def is_connected(self) -> bool:
        return self.tel3._connected and self.tel3 is not None

    def _login(
        self, user: str | None = None, password: str | None = None
    ) -> str | None:
        res = self.tel3.read_until("login:")
        # print(f"{res = }")
        self.tel3.write(f"{user}\n" if user is not None else "\n")
        # print(f"[DBG]write: {user}")
        res = self.tel3.read_until("Password:")
        # print(f"{res = }")
        self.tel3.write(f"{password}\n" if password is not None else "\n")
        # print(f"[DBG]write: {password}")
        buf = ""
        # self.tel3.write("\r\n")

        while True:
            res = self.tel3.read_some()
            res = res.decode() if isinstance(res, bytes) else res
            buf += res
            # print(f"[DBG]{buf = }")

            if prompt := self.prompt_pattern.search(remove_ansi(res)):
                return prompt.group()
