from __future__ import annotations

import queue
import re
import threading as td
import time

# from enum import IntEnum, auto
from typing import Generic, Iterator, override

from paramiko.channel import ChannelStdinFile as pk_ChannelStdinFile

from ..export.term import TermStyle
from ..tools.result import Result, T
from ..tools.timestamp import Timestamp
from .ansi import AnsiReset, remove_ansi

# T = TypeVar("T")


class CmdRecord(Generic[T]):
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
        self.prompt: str = prompt
        self.start_time: Timestamp = Timestamp()
        self.end_time: Timestamp | None = None
        self.run_time: float | None = None
        self.cmd: str = cmd
        self.result: list[tuple[Timestamp, Result[T]]] = []
        self.stdin: pk_ChannelStdinFile | None = None

    def __contains__(self, string: str) -> bool:
        """支持if string in record的判断，对于每一行进行检索"""
        for each_line in self.get_result():
            if string in each_line:
                return True
        return False

    def task_kill(self):
        """非线程任务，只发送ctrl-c"""
        if self.stdin is not None:
            self.stdin.write("\x03")

    def record_end(self) -> None:
        """手动记录命令结束时间，编写者保证在内部使用时记录，紧跟在命令结束之后"""
        self.end_time = Timestamp()
        self.run_time = self.end_time - self.start_time

    def get_run_time(self) -> float | None:
        """获取命令的运行时间，命令未结束返回已经运行的时长"""
        return (
            self.run_time
            if self.end_time is not None
            else time.time() - self.start_time
        )

    def result_append(self, result: T, timestamp: Timestamp | None = None) -> None:
        """以Result[T]的形式,添加在self.result末尾，默认附加时间戳，可以指定"""
        if timestamp is None:
            timestamp = Timestamp()
        self.result.append((timestamp, Result(result)))

    def record_result(self, result: list[tuple[Timestamp, Result]]) -> None:
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
        """获取命令的输出结果，去除Result，去除ansi转义\n
        对于非str类型的结果尝试转换为str"""
        return [
            remove_ansi(e[1].get()) if e[1].type is str else str(e[1].get())
            for e in self.result
        ]

    def get_result_string(self) -> str:
        """获取命令的输出结果字符串，去除ansi转义"""
        return "\n".join(self.get_result())

    def get_result_iter(self) -> Iterator[str]:
        """获取命令的输出结果迭代器，去除ansi转义"""
        return (
            remove_ansi(e[1].get()) if e[1].type is str else str(e[1].get())
            for e in self.result
        )

    def search(self, re_string: str) -> re.Match[str] | None:
        """搜索命令的输出结果，匹配立即返回re.Match对象，未匹配返回None"""
        for line in self.get_result_iter():
            match = re.search(re_string, line)
            if match:
                return match
        return None

    def search_all(self, re_string: str) -> Iterator[re.Match[str]]:
        """搜索命令的输出结果，返回匹配的re.Match对象的迭代器，未匹配返回空迭代器"""
        return re.finditer(re_string, self.get_result_string())


class CmdRecording(CmdRecord, Generic[T]):
    """线程指令的记录类，添加了线程相关的处理"""

    def __init__(self, cmd: str, prompt: str) -> None:
        super().__init__(cmd, prompt)
        # for long running
        self.fifo = queue.Queue()  # 用于主线程实时处理线程输出
        self.stop_event = td.Event()  # 用于停止线程的事件
        self.long_running_task: td.Thread  # 记录任务本身，便于获取状态

    @override
    def __contains__(self, string: str) -> bool:
        """支持 if string in record: 的语法，每次对于fifo进行判断，消耗fifo"""
        line = self.get_once()
        return True if line and string in line else False

    @override
    def task_kill(self):
        """对于线程任务，发送ctrl-c给远程后本地设置结束事件"""
        if self.stdin is not None:
            self.stdin.write("\x03")
        self.stop_event.set()

    def get_once(self) -> None | str:
        """获取一次fifo中的数据，返回去除ansi转义的字符串，当前fifo为空返回None"""
        return remove_ansi(self.fifo.get()) if not self.fifo.empty() else None

    def search_next_line(
        self, pattern: str, flags: re._FlagsType = 0
    ) -> None | re.Match[str]:
        """匹配一次fifo中的数据，返回re.Match对象，当前fifo为空返回None，消耗fifo"""
        line = self.get_once()
        return re.search(pattern, line, flags) if line else None

    def find_next_line(
        self, pattern: str, flags: re._FlagsType = 0
    ) -> None | list[str]:
        """查找一次fifo中的数据，返回匹配到的字符串列表，当fifo为空或未匹配时返回空列表，消耗fifo"""
        line = self.get_once()
        return re.findall(pattern, line, flags) if line else None


class MetaRecord(Generic[T]):
    """元记录，记录类的log"""

    def __init__(self, type: str, name: str, info: str) -> None:
        # timestamp
        self.start_time = Timestamp()
        self.end_time: None | Timestamp = None
        # info
        self.type: str = type
        self.info: str = info
        self.name: str = name
        # record
        self.logs: list[tuple[Timestamp, Result[T]]] = []

    def get_fmt_prompt(self, colorful: bool = True) -> str:
        fmt_string = f"{TermStyle.log_font_color}{TermStyle.log_background_color}[{self.type}][{self.name}][{self.info}]{AnsiReset}"
        if colorful:
            return fmt_string
        return remove_ansi(fmt_string)
