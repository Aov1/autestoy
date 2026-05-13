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
    AnsiBackgroundTrueColor,
    AnsiColor,
    AnsiReset,
    AnsiStyle,
    ansi,
    exchange_ansi_color_background,
    get_ansi_background_from,
    get_ansi_color_from,
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
    data_CONNECT,
    data_DISCONNECT,
    data_ERROR,
    data_LOG,
    data_WARNING,
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
    timestamp_ansi: str = AnsiStyle.bold + AnsiColor.black + AnsiBackground.light_blue
    command_header_ansi: str = AnsiColor.light_green
    message_ansi: str = AnsiColor.none + AnsiStyle.dark
    protocol_connect_header: str = (
        AnsiStyle.bold + AnsiColor.black + AnsiBackground.light_yellow
    )
    protocol_connect_info: str = (
        AnsiStyle.bold + AnsiColor.black + AnsiBackground.light_green
    )
    protocol_disconnect_header: str = (
        AnsiStyle.bold + AnsiColor.black + AnsiBackground.light_yellow
    )
    protocol_disconnect_info: str = (
        AnsiStyle.bold + AnsiColor.black + AnsiBackground.light_red
    )

    log_header_ansi: str = AnsiColor.yellow
    log_message_ansi: str = AnsiColor.none
    warning_header_ansi: str = AnsiStyle.bold + AnsiColor.yellow
    warning_message_ansi: str = AnsiColor.none
    error_header_ansi: str = AnsiStyle.bold + AnsiColor.red
    error_message_ansi: str = AnsiColor.none
    user_header_ansi: str = AnsiColor.yellow
    user_message_ansi: str = AnsiColor.none


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
            case MessageType.CONNECT:
                self._event_protocol_connect(msg)
            case MessageType.DISCONNECT:
                self._event_protocol_disconnect(msg)
            case MessageType.LOG | MessageType.WARNING | MessageType.ERROR:
                self._event_log(msg)
            case _:
                pass

    def _ts(
        self,
        ovrd_timestamp: Optional[Timestamp] = None,
    ) -> Timestamp:
        """返回时间戳，如果提供了ovrd则返回ovrd，否则返回当前时间戳,内部使用"""
        if ovrd_timestamp is not None:
            return ovrd_timestamp
        return Timestamp()

    def _fmt_ts(
        self,
        ts: Optional[Timestamp] = None,
    ) -> str:
        """用于格式化时间戳,受到初始化参数影响,内部使用:w"""
        if ts is None:
            ts = self._ts()

        if self.absoulute_timestamp:
            return str(ts)
        else:
            return f"{ts.to_float() - self.timebase:>{TermStyle.relative_timestamp_width}.{TermStyle.relative_timestamp_bits}f}"

    def _event_cmd_prompt(self, msg: Message[data_CMD_PROMPT]):
        """用于处理显示所有协议的提示符+命令,上级调用保证了output只有一行,内部使用"""
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

    def _event_cmd_output(self, msg: Message[data_CMD_OUTPUT]):
        """用于处理显示所有的协议交互输出,上级调用保证了output只有一行,内部使用"""
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

    def _event_log(self, msg: Message[data_LOG | data_WARNING | data_ERROR]):
        """log warning errer的统一处理显示方法,内部调用"""
        if "\n" in msg.data.log:
            log = msg.data.log.replace("\r\n", "\n")
            prompt_line, log = log.split("\n", 1)
            self._log_line(msg, prompt_line)
            while "\n" in log:
                info_line, log = log.split("\n", 1)
                self._log_line(msg, info_line, no_prompt=True)
            else:
                if log != "":
                    self._log_line(msg, log, no_prompt=True)

        else:
            self._log_line(msg)

    def _log_line(
        self,
        msg: Message[data_LOG | data_WARNING | data_ERROR],
        ovrd_log_info: str | None = None,
        no_prompt: bool = False,
    ):
        """用于处理log的多行情况,用于log warning error,内部使用"""
        ts = self._fmt_ts(msg.timestamp)
        output = msg.data.log if ovrd_log_info is None else ovrd_log_info
        source = msg.source.name
        type = msg.type
        name = msg.data.name
        log_header_ansi = (
            self.style.log_header_ansi
            if type is MessageType.LOG
            else self.style.warning_header_ansi
            if type is MessageType.WARNING
            else self.style.error_header_ansi
            if type is MessageType.ERROR
            else AnsiReset
        )
        log_msg_ansi = (
            self.style.log_message_ansi
            if type is MessageType.LOG
            else self.style.warning_message_ansi
            if type is MessageType.WARNING
            else self.style.error_message_ansi
            if type is MessageType.ERROR
            else AnsiReset
        )

        if no_prompt:
            string = make_ansi(
                (f"[{ts}]", self.style.timestamp_ansi, AnsiReset),
                " ",
                (output, log_msg_ansi, AnsiReset),
            )
        else:
            string = make_ansi(
                (f"[{ts}]", self.style.timestamp_ansi, AnsiReset),
                " ",
                (f"[{type.name}][{source}][{name}]", log_header_ansi, AnsiReset),
                " ",
                (output, log_msg_ansi, AnsiReset),
            )
        self.write(string + "\n")

    def _event_protocol_connect(self, msg: Message[data_CONNECT]) -> None:
        ts = self._fmt_ts(msg.timestamp)
        source = msg.source.name
        name = msg.data.name
        id_key = msg.data.id_key
        if name == id_key:
            name = None
        output = msg.data.info
        string = make_ansi(
            (f"[{ts}]", self.style.timestamp_ansi, AnsiReset),
            (
                "\ue0b0",
                get_ansi_background_from(self.style.protocol_connect_header)
                + exchange_ansi_color_background(
                    get_ansi_background_from(self.style.timestamp_ansi)
                ),
                AnsiReset,
            ),
            (
                f"[{source}]{f'[{name}]' if name else ''}[{id_key}]",
                self.style.protocol_connect_header,
                AnsiReset,
            ),
            (
                "\ue0b0",
                get_ansi_background_from(self.style.protocol_connect_info)
                + exchange_ansi_color_background(
                    get_ansi_background_from(self.style.protocol_connect_header)
                ),
                AnsiReset,
            ),
            (f"{output}", self.style.protocol_connect_info, AnsiReset),
            (
                "\ue0b0",
                exchange_ansi_color_background(
                    get_ansi_background_from(self.style.protocol_connect_info)
                ),
                AnsiReset,
            ),
        )
        self.write(string + "\n")

    def _event_protocol_disconnect(self, msg: Message) -> None:
        ts = self._fmt_ts(msg.timestamp)
        source = msg.source.name
        name = msg.data.name
        id_key = msg.data.id_key
        if name == id_key:
            name = None
        output = msg.data.info
        string = make_ansi(
            (f"[{ts}]", self.style.timestamp_ansi, AnsiReset),
            (
                "\ue0b0",
                get_ansi_background_from(self.style.protocol_disconnect_header)
                + exchange_ansi_color_background(
                    get_ansi_background_from(self.style.timestamp_ansi)
                ),
                AnsiReset,
            ),
            (
                f"[{source}]{f'[{name}]' if name else ''}[{id_key}]",
                self.style.protocol_disconnect_header,
                AnsiReset,
            ),
            (
                "\ue0b0",
                get_ansi_background_from(self.style.protocol_disconnect_info)
                + exchange_ansi_color_background(
                    get_ansi_background_from(self.style.protocol_disconnect_header)
                ),
                AnsiReset,
            ),
            (f"{output}", self.style.protocol_disconnect_info, AnsiReset),
            (
                "\ue0b0",
                exchange_ansi_color_background(
                    get_ansi_background_from(self.style.protocol_disconnect_info)
                ),
                AnsiReset,
            ),
        )
        self.write(string + "\n")
