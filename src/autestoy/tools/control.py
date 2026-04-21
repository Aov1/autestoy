import time
from typing import overload

from ..export.collect import CollectObj, CollectType, collect
from ..export.term import Term, TermStyle
from .ansi import AnsiColor, AnsiReset
from .record import CmdRecord

# from .result import Result
from .timestamp import Timestamp


@collect(CollectType.TrySeconds, CollectObj)
class TrySeconds:
    """创建一个计时器，经过设置的时间后将返回False"""

    def __init__(self, seconds: float):
        self.seconds = seconds
        self.start_timestamp = Timestamp()
        self.info = f"TrySeconds({seconds:^8.2f}) from {Term.fmt_timestamp(self.start_timestamp)}:"
        Term.putsln(
            self.info + f"{AnsiReset} Start",
            log_time=self.start_timestamp,
            set_font_color=AnsiColor.yellow,
        )
        self.first_check = True

    def __bool__(self) -> bool:
        is_trying = time.time() - self.start_timestamp < self.seconds
        if not is_trying:
            res = "Timeout" if self.first_check else "Already Timeout"
            self.first_check = False
            Term.putsln(
                self.info + f"{AnsiReset} {res}",
                set_font_color=AnsiColor.yellow,
            )
        return is_trying

    def check_timeout(self) -> bool:
        return not bool(self)


def ulog(
    *msg: object,
    show_timestamp: bool = True,
    override_font_color: str | None = None,
    override_background_color: str | None = None,
) -> CmdRecord[str]:
    """用户Log，终端输出"""
    long_msg = " ".join(str(m) for m in msg)
    msg_lines = long_msg.splitlines()
    record = CmdRecord(
        cmd=long_msg,
        prompt="[User Log]:",
        create_id=False,
    )
    font_color = override_font_color or TermStyle.log_font_color
    background_color = override_background_color or TermStyle.log_background_color
    for line in msg_lines:
        if show_timestamp:
            Term.puts_timestamp()
        Term.puts_msg(
            f"{TermStyle.prompt_background_color}{TermStyle.prompt_font_color}{record.prompt}{AnsiReset} {background_color}{font_color}{line}{AnsiReset}\n"
        )
    record.record_end()
    return record


@overload
def get_line_from_head(buf: bytes) -> tuple[bytes, bytes]: ...


@overload
def get_line_from_head(buf: str) -> tuple[str, str]: ...


def get_line_from_head(buf: str | bytes) -> tuple[bytes | str, bytes | str]:
    """从缓冲区头部获取一行,没有完整行则返回剩余空字符和原buf"""
    if isinstance(buf, str):
        if "\r\n" in buf or "\n" in buf:
            line, buf = buf.split("\n", 1)
            return line, buf
        return "", buf
    else:
        while b"\r\n" in buf or b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            return line, buf
        return "", buf
