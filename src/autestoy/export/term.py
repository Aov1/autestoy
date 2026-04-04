"""
关于终端输出
"""

import sys

from ..tools.ansi import AnsiColor, AnsiReset, remove_ansi
from ..tools.result import Result
from ..tools.timestamp import Timestamp

sys_write = sys.stdout.write


class TermStyle:
    timestamp_font_color = AnsiColor.blue
    timestamp_background_color = AnsiColor.none
    relative_timestamp_bits = 3
    relative_timestamp_width = 10

    msg_font_color = AnsiColor.none
    msg_background_color = AnsiColor.none

    prompt_font_color = AnsiColor.light_green
    prompt_background_color = AnsiColor.none

    log_font_color = AnsiColor.yellow
    log_background_color = AnsiColor.none

    warning_font_color = AnsiColor.yellow
    warning_background_color = AnsiColor.none

    error_font_color = AnsiColor.red
    error_background_color = AnsiColor.none


class Term:
    sw_timestamp: bool = True
    sw_absolute_timestamp: bool = False

    @classmethod
    def set_time_base(cls, time_base: Timestamp):
        cls.time_base: Timestamp = time_base

    @classmethod
    def puts_timestamp(cls, timestamp: Timestamp | None = None):
        if not timestamp:
            timestamp = Timestamp()

        if cls.sw_absolute_timestamp:  # 显示绝对时间开关
            timestamp_str = str(timestamp)
        else:  # 显示相对时间
            timestamp_str = f"{timestamp - cls.time_base:>{TermStyle.relative_timestamp_width}.{TermStyle.relative_timestamp_bits}f}"
        sys_write(
            f"{TermStyle.timestamp_background_color}{TermStyle.timestamp_font_color}[{timestamp_str}]{AnsiReset} "
        )

    @classmethod
    def puts_msg(cls, msg: str) -> tuple[Timestamp, Result[str]]:
        """终端输出msg，返回时间戳和Result(msg)，用作流式处理\n
        不显示时间戳，无换行。"""
        log_time = Timestamp()
        sys_write(
            f"{TermStyle.msg_background_color}{TermStyle.msg_font_color}{msg}{AnsiReset}"
        )
        return log_time, Result(remove_ansi(msg))

    @classmethod
    def putsln(
        cls,
        msg: str,
        log_time: Timestamp | None = None,
        insert_str_before_msg: str | None = None,
    ) -> tuple[Timestamp, Result[str]]:
        """终端输出带换行，返回时间戳和Result(msg)作为流式处理\n
        是否输出时间戳受到Term类属性控制\n
        输出样式受到TermStyle类属性控制，使用ANSI转义\n
        会对msg添加换行符，返回的Result(msg)不带换行符"""
        if log_time is None:
            log_time = Timestamp()
        if cls.sw_timestamp:  # 显示时间戳开关
            cls.puts_timestamp(log_time)
            # need test
            # if cls.sw_absolute_timestamp:  # 显示绝对时间开关
            #     timestamp_str = str(log_time)
            # else:  # 显示相对时间
            #     timestamp_str = f"{log_time - cls.time_base:>{TermStyle.relative_timestamp_width}.{TermStyle.relative_timestamp_bits}f}"
            # sys_write(
            #     f"{TermStyle.timestamp_background_color}{TermStyle.timestamp_font_color}[{timestamp_str}]{AnsiReset} "
            # )
        if insert_str_before_msg:
            sys_write(insert_str_before_msg + " ")
        sys_write(
            f"{TermStyle.msg_background_color}{TermStyle.msg_font_color}{msg}{AnsiReset}\n"
        )
        return log_time, Result(remove_ansi(msg))
