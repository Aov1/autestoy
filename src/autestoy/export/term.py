"""
关于终端输出
"""

import sys
import time

from ..tools.ansi import AnsiColor, AnsiReset

sys_write = sys.stdout.write


class TermStyle:
    timestamp_font_color = AnsiColor.blue
    timestamp_background_color = AnsiColor.none
    timestamp_bits = 3
    relative_timestamp_width = 10

    msg_font_color = AnsiColor.none
    msg_background_color = AnsiColor.none

    prompt_font_color = AnsiColor.light_green
    prompt_background_color = AnsiColor.none


class Term:
    sw_timestamp: bool = True
    sw_absolute_timestamp: bool = False

    @classmethod
    def set_time_base(cls, time_base: float):
        cls.time_base = time_base

    @classmethod
    def puts(cls, msg: str) -> tuple[float, str]:
        """终端输出msg，返回时间戳和msg本身，用作流式处理"""
        log_time = time.time()
        sys_write(
            f"{TermStyle.msg_background_color}{TermStyle.msg_font_color}{msg}{AnsiReset}"
        )
        return log_time, msg

    @classmethod
    def putsln(
        cls,
        msg: str,
        log_time: float | None = None,
        insert_str_before_msg: str | None = None,
    ) -> tuple[float, str]:
        """终端输出带换行，返回时间戳和字符作为流式处理\n
        是否输出时间戳受到Term类属性控制\n
        输出样式受到TermStyle类属性控制，使用ANSI转义"""
        if log_time is None:
            log_time = time.time()
        if cls.sw_timestamp:
            if cls.sw_absolute_timestamp:
                timestamp = log_time
            else:
                timestamp = log_time - cls.time_base
            sys_write(
                f"{TermStyle.timestamp_background_color}{TermStyle.timestamp_font_color}[{timestamp:>{TermStyle.relative_timestamp_width if not cls.sw_absolute_timestamp else 11 + TermStyle.timestamp_bits}.{TermStyle.timestamp_bits}f}]{AnsiReset} "
            )
        if insert_str_before_msg:
            sys_write(insert_str_before_msg + " ")
        sys_write(
            f"{TermStyle.msg_background_color}{TermStyle.msg_font_color}{msg}{AnsiReset}\n"
        )
        return log_time, msg
