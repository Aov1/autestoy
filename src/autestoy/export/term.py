"""
关于终端输出
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from typing import Any, Callable, Optional

# from autestoy.tools.record import CmdRecord
from ..tools.ansi import (
    AnsiBackground,
    AnsiColor,
    AnsiReset,
    AnsiStyle,
    ansi,
    make_ansi,
    remove_ansi,
)
from ..tools.globalvar import GLOBAL_timebase
from ..tools.result import Result
from ..tools.timestamp import Timestamp
from .messageio import (
    Message,
    MessageBus,
    MessageSource,
    MessageType,
    OutputLine,
    data_CMD_OUTPUT,
    data_CMD_PROMPT,
    data_LOG,
)

sys_write = sys.stdout.write


def get_terminal_size() -> tuple[int, int]:
    return shutil.get_terminal_size()


PROMPT_pattern = r"(?:[\w@\-\.\[\]]+[:~/\w\-\. ]*|[:~/\w\-\. ]+)?[\$#]\s*$"


class TermStyle:
    timestamp_font_color = AnsiColor.blue
    timestamp_background_color = AnsiColor.none
    relative_timestamp_bits = 5
    relative_timestamp_width = 13

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

    terminal_size: tuple[int, int] = get_terminal_size()

    @classmethod
    def set_time_base(cls, time_base: Timestamp):
        cls.time_base: Timestamp = time_base

    @classmethod
    def fmt_timestamp(cls, timestamp: Timestamp | None = None) -> str:
        if not timestamp:
            timestamp = Timestamp()

        if cls.sw_absolute_timestamp:  # 显示绝对时间开关
            timestamp_str = str(timestamp)
        else:  # 显示相对时间
            timestamp_str = f"{timestamp - cls.time_base:>{TermStyle.relative_timestamp_width}.{TermStyle.relative_timestamp_bits}f}"
        return f"{TermStyle.timestamp_background_color}{TermStyle.timestamp_font_color}[{timestamp_str}]{AnsiReset} "

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
        set_font_color: str | None = None,
        set_background_color: str | None = None,
    ) -> tuple[Timestamp, Result[str]]:
        """终端输出带换行，返回时间戳和Result(msg)作为流式处理\n
        是否输出时间戳受到Term类属性控制\n
        输出样式受到TermStyle类属性控制，使用ANSI转义\n
        会对msg添加换行符，返回的Result(msg)不带换行符"""
        if log_time is None:
            log_time = Timestamp()
        if cls.sw_timestamp:  # 显示时间戳开关
            cls.puts_timestamp(log_time)
        if insert_str_before_msg:
            sys_write(insert_str_before_msg + " ")
        font_color = TermStyle.msg_font_color if not set_font_color else set_font_color
        background_color = (
            TermStyle.msg_background_color
            if not set_background_color
            else set_background_color
        )
        sys_write(f"{background_color}{font_color}{msg}{AnsiReset}\n")
        return log_time, Result(remove_ansi(msg))

    @classmethod
    def is_terminal_size_changed(cls) -> bool:
        tmp_new_size = get_terminal_size()
        if tmp_new_size != cls.terminal_size:
            cls.terminal_size = tmp_new_size
            return True
        return False


# ===============MessageIO============


def rt_ts_res_msg(msg: str) -> tuple[Timestamp, Result[str]]:
    return Timestamp(), Result(msg)


@dataclass
class MessageStyle:
    timestamp_ansi: str = AnsiColor.blue
    command_header_ansi: str = AnsiColor.light_green
    message_ansi: str = AnsiColor.none
    log_ansi: str = AnsiColor.yellow
    warning_ansi: str = AnsiStyle.bold + AnsiColor.yellow
    error_ansi: str = AnsiStyle.bold + AnsiColor.red
    user_dbg_ansi: str = AnsiColor.yellow


class MessageTerminal(OutputLine):
    """消息终端，用于输出消息到终端"""

    def __init__(
        self,
        name: str = "terminal",
        maxsize: int = 0,
        writable: Callable[[str], Any] = sys.stdout.write,
        style: MessageStyle = MessageStyle(),
        absoulute_timestamp: bool = False,
    ):
        super().__init__(name=name, maxsize=maxsize)
        self.timebase = GLOBAL_timebase
        self.timestamp = Timestamp()
        self.absoulute_timestamp = absoulute_timestamp
        self.write = writable
        self.style = style

        # MessageBus.subscribe(MessageType.CMD_PROMPT, self._event_cmd_prompt)
        # MessageBus.subscribe(MessageType.CMD_OUTPUT, self._event_cmd_output)
        # MessageBus.subscribe(MessageType.LOG, self._event_log)

    def handle(self, msg: Message) -> None:
        match msg.type:
            case MessageType.CMD_PROMPT:
                self._event_cmd_prompt(msg)
            case MessageType.CMD_OUTPUT:
                self._event_cmd_output(msg)
            case MessageType.LOG:
                self._event_log(msg)
            case _:
                pass

    def _ts(
        self,
        ovrd_timestamp: Optional[Timestamp] = None,
    ) -> Timestamp:
        """返回时间戳，如果提供了ovrd则返回ovrd，否则返回当前时间戳"""
        if ovrd_timestamp is not None:
            return ovrd_timestamp
        return Timestamp()

    def _fmt_ts(
        self,
        ts: Optional[Timestamp] = None,
    ) -> str:
        if ts is None:
            ts = self._ts()

        if self.absoulute_timestamp:
            return str(ts)
        else:
            return f"{ts.to_float() - self.timebase:>{TermStyle.relative_timestamp_width}.{TermStyle.relative_timestamp_bits}f}"

    def _event_cmd_prompt(self, msg: Message[data_CMD_PROMPT]):
        ts = self._fmt_ts(msg.timestamp)
        id = msg.data.id
        name = msg.data.name
        command = msg.data.command
        prompt = msg.data.prompt
        source = msg.source.name
        string = make_ansi(
            (f"[{ts}]", self.style.timestamp_ansi, AnsiReset),
            " ",
            (
                f"[{id}][{source}][{name}]{prompt}",
                self.style.command_header_ansi,
                AnsiReset,
            ),
            " ",
            (command, self.style.message_ansi, AnsiReset),
        )
        self.write(string + "\n")
        # self.write(f"[{ts}] [{id}][{source}][{name}]{prompt} {command}\n")

    def _event_cmd_output(self, msg: Message[data_CMD_OUTPUT]):
        ts = self._fmt_ts(msg.timestamp)
        id = msg.data.id
        output = msg.data.output
        string = make_ansi(
            (f"[{ts}]", self.style.timestamp_ansi, AnsiReset),
            " ",
            (f"[{id}]", self.style.command_header_ansi, AnsiReset),
            (output, self.style.message_ansi, AnsiReset),
        )
        self.write(string + "\n")
        # self.write(f"[{ts}] [{id}]{output}\n")

    def _event_log(self, msg: Message[data_LOG]):
        ts = self._fmt_ts(msg.timestamp)
        output = msg.data.log
        source = msg.source.name
        type = msg.type.name
        name = msg.data.name
        string = make_ansi(
            (f"[{ts}]", self.style.timestamp_ansi, AnsiReset),
            " ",
            (f"[{type}][{source}][{name}]", self.style.log_ansi, AnsiReset),
            " ",
            (output, self.style.message_ansi, AnsiReset),
        )
        self.write(string + "\n")

        # self.write(f"[{ts}] [{source}Log]{output}\n")
