import queue
import threading as td
import time

# from enum import IntEnum, auto
from typing import override

from paramiko.channel import ChannelStdinFile as pk_ChannelStdinFile

from ..export.term import TermStyle
from .ansi import AnsiReset, remove_ansi

# class CmdType(IntEnum):
#     """命令类型枚举类，用于记录命令的类型"""

#     SSH_ONE_SHOT = auto()
#     SSH_LONG_RUNNING = auto()
#     SSH_INTERACTIVE = auto()


# class TerminalStyle:
#     """样式类，用于配置样式，使用ANSI转义"""

#     prompt: str = AnsiColor.light_green
#     command: str = ""


class CmdRecord:
    """命令记录类，用于记录命令的执行结果，规范不同协议发送输出的内容"""

    _cmd_id: int = 0

    @classmethod
    def id_generator(cls) -> int:
        """类方法，生成命令的自增id"""
        cls._cmd_id += 1
        return cls._cmd_id

    def __init__(self, cmd: str, prompt: str) -> None:
        """初始化，为了减少运行时间的误差，请在发送命令前紧接该初始化"""
        self.id: int = CmdRecord.id_generator()
        # self.cmd_type: CmdType = cmd_type
        self.prompt: str = prompt
        self.start_time: float = time.time()
        self.end_time: float | None = None
        self.run_time: float | None = None
        self.cmd: str = cmd
        self.result: list[tuple[float, str]] = []
        self.stdin: pk_ChannelStdinFile | None = None

    def task_kill(self):
        if self.stdin is not None:
            self.stdin.write("\x03")

    def record_end(self) -> None:
        """手动记录命令结束时间，编写者保证在内部使用时记录，紧跟在命令结束之后"""
        self.end_time = time.time()
        self.run_time = self.end_time - self.start_time

    def get_run_time(self) -> float | None:
        """获取命令的运行时间，命令未结束返回已经运行的时长"""
        return (
            self.run_time
            if self.end_time is not None
            else time.time() - self.start_time
        )

    # def record_result(self, result: str) -> None:
    #     """记录命令的输出结果，包括ansi"""
    #     self.result = result.replace("\r\n", "\n").strip().split("\n")

    def record_result_bata(self, result: list[tuple[float, str]]) -> None:
        """记录命令的输出结果，包括ansi"""
        self.result = result

    def get_fmt_prompt(self, colorful: bool = True) -> str:
        """获取格式化终端提示符，包括命令id、提示符和命令本身。\n
        终端显示和记录都基于此函数"""
        tmp = f"{TermStyle.prompt_font_color}{TermStyle.prompt_background_color}[{self.id}]:{self.prompt}{AnsiReset} {TermStyle.msg_font_color}{TermStyle.msg_background_color}{self.cmd}{AnsiReset}"
        if colorful:
            return tmp
        return remove_ansi(tmp)

    def __str__(self) -> str:  # TODO
        out = self.get_fmt_prompt()
        return out

    def get_result(self) -> list[str]:
        """获取命令的输出结果，去除ansi转义"""
        return [remove_ansi(e[1]) for e in self.result]


class CmdRecording(CmdRecord):
    def __init__(self, cmd: str, prompt: str) -> None:
        super().__init__(cmd, prompt)
        # for long running
        self.fifo = queue.Queue()
        self.stop_event = td.Event()
        self.long_running_task: td.Thread

    @override
    def task_kill(self):
        if self.stdin is not None:
            self.stdin.write("\x03")
        self.stop_event.set()


class Result:
    def __init__(self) -> None:
        pass
