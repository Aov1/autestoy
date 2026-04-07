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
        self.exit_code: int | None = None

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
        """以Result[T]的形式,添加在self.result末尾，默认附加时间戳，时间戳可以指定"""
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
        """获取命令的输出结果字符串，将多行输出合并，去除ansi转义"""
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

    def cut_fields(
        self,
        *fields: int,
        re_delimiter: str = r"\t",
    ) -> list[list[str]]:
        """切割命令的输出结果，返回切割后的字段二维列表。\n
        类似于linux的cut -d "<chr>" -f <n>命令，但支持了正则匹配分隔符号"""

        result = []
        for line in self.get_result_iter():
            tmp = []
            res = re.split(re_delimiter, line)
            for f in fields:
                if f <= 0:
                    tmp = []
                    tmp.append(res)
                    break
                else:
                    tmp.append(res[f - 1]) if f <= len(res) else tmp.append("")
            result.append(tmp)
        return result

    def cut_characters(self, *characters: tuple[int, int]) -> list[list[str]]:
        """切割命令的输出结果，返回切割后的字符二维列表。\n
        characters: 字符范围的元组，(start, end)，start和end都是从1开始的索引\n
        start，end包含进范围之中\n
        支持多组索引，逗号分隔"""
        result = []
        for line in self.get_result_iter():
            tmp = []
            for char_start, char_end in characters:
                if char_start <= 1:
                    char_start = 1
                if char_end > len(line):
                    char_end = len(line)
                tmp.append(line[char_start - 1 : char_end])
            result.append(tmp)
        return result


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
        """获取一次fifo中的数据，返回去除ansi转义的字符串\n
        由于可能存在fifo为空的情况，且空fifo返回None，所以并不意味着稳定的读取一行输出"""
        return remove_ansi(self.fifo.get()) if not self.fifo.empty() else None

    def clean_fifo(self) -> None:
        """清空fifo中目前所有的数据"""
        while not self.fifo.empty():
            self.fifo.get()

    def force_get_fifo(
        self, times: int = 1, timeout: float = 2, raise_when_timeout: bool = False
    ) -> list[str]:
        """强制按次数获取fifo中的数据，返回去除 ansi 转义的字符串列表，消耗fifo\n
        fifo为空将等待，会阻塞运行\n
        timeout 为等待超时时间，为0忽略\n
        raise_when_timeout 为超时是否抛出异常，不抛出异常时返回已经获取的fifo line\n
        """
        lines = []
        t_start = time.time()
        while len(lines) < times:
            if time.time() - t_start > timeout and timeout != 0:
                if raise_when_timeout:
                    raise TimeoutError("force_get_fifo timeout")
                return lines
            line = self.get_once()
            if line is None:
                continue
            lines.append(line)
        return lines

    def search_next_line(
        self, pattern: str, flags: re._FlagsType = 0
    ) -> None | tuple[str, re.Match[str] | None]:
        """匹配一次fifo中的数据，消耗fifo\n
        当fifo为空时返回None\n
        fifo非空时进行正则匹配，返回 输出行 和 匹配结果\n
        匹配结果也可能为空"""
        line = self.get_once()
        if line is None:
            return None
        return line, re.search(pattern, line, flags)

    def find_next_line(
        self, pattern: str, flags: re._FlagsType = 0
    ) -> None | tuple[str, list[str | None]]:
        """查找一次fifo中的数据，消耗fifo\n
        当fifo为空时返回None\n
        fifo非空时进行正则匹配，返回 输出行 和 匹配结果列表\n
        匹配失败时返回的是 输出行 和 空列表"""
        line = self.get_once()
        if line is None:
            return None
        return line, re.findall(pattern, line, flags)

    def fifo_wait(
        self, re_string: str | None = None, timeout: float = 10
    ) -> None | list[str]:
        """等待fifo中有指定的数据，返回截至找到指定字符串之前的所有fifo line，当然消耗fifo\n
        re_string:需要正则匹配的字符串，为None时匹配任何字符\n
        timeout设置超时，非0启用，超时返回None；timeout=0不启用超时\n"""
        lines: list[str] = []  # 存储获取的fifo line
        t_start = time.time()  # 开始时间
        while True:
            line = self.get_once()  # 获取一次fifo line
            if line is None:  # fifo为空
                if timeout != 0 and time.time() - t_start > timeout:  # 是否超时
                    return None  # 超时结束
                continue  # 未超时继续
            lines.append(line)  # fifo line 非空保存

            if re_string is None:  # 未设置匹配字符串立即结束
                return lines
            else:  # 设置了匹配字符串
                if re.search(re_string, line):  # 进行匹配
                    return lines  # 匹配到立即返回


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
