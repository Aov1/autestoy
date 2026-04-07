import time

from ..export.collect import CollectObj, CollectType, collect
from ..export.term import Term
from .ansi import AnsiColor, AnsiReset
from .record import CmdRecord
from .result import Result
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
    override_font_color: str | None = None,
    override_background_color: str | None = None,
) -> tuple[Timestamp, Result[str]]:
    """用户Log，终端输出，带有时间戳"""
    long_msg = " ".join(str(m) for m in msg)
    record = CmdRecord(
        cmd=long_msg,
        prompt="[UserLog]:",
    )
    return Term.putsln(
        record.get_fmt_prompt(),
        set_font_color=override_font_color,
        set_background_color=override_background_color,
    )
