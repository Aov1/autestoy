import threading as td
import time
from enum import IntEnum, auto
from typing import Iterable, Iterator

from .ansi import remove_ansi


class CmdType(IntEnum):
    """命令类型枚举类，用于记录命令的类型"""

    SSH_ONE_SHOT = auto()
    SSH_LONG_RUNNING = auto()
    SSH_INTERACTIVE = auto()


class CmdRecord:
    """命令记录类，用于记录命令的执行结果，规范不同协议发送输出的内容"""

    _cmd_id: int = 0

    @classmethod
    def id_generator(cls) -> int:
        """类方法，生成命令的自增id"""
        cls._cmd_id += 1
        return cls._cmd_id

    def __init__(self, cmd: str, cmd_type: CmdType, prompt: str) -> None:
        """初始化，为了减少运行时间的误差，请在发送命令前紧接该初始化"""
        self._id: int = CmdRecord.id_generator()
        self._cmd_type: CmdType = cmd_type
        self._prompt: str = prompt
        self._start_time: float = time.time()
        self._end_time: float | None = None
        self._run_time: float
        self._cmd: str = cmd
        self._result = ""
        self._result_iter: Iterator
        self.long_running_task: td.Thread
        self.stop_event: td.Event

    def record_end(self) -> None:
        """手动记录命令结束时间，编写者保证在内部使用时记录，紧跟在命令结束之后"""
        self._end_time = time.time()
        self._run_time = self._end_time - self._start_time

    def get_id(self) -> int:
        """获取命令的自增id"""
        return self._id

    def get_start_time(self) -> float:
        """获取命令的开始时间"""
        return self._start_time

    def get_end_time(self) -> float | None:
        """获取命令的结束时间，命令未结束返回None"""
        return self._end_time

    def get_run_time(self) -> float:
        """获取命令的运行时间，命令未结束返回已经运行的时长"""
        return (
            self._run_time
            if self._end_time is not None
            else time.time() - self._start_time
        )

    def get_command(self) -> str:
        """获取输入命令"""
        return self._cmd

    def get_result(self) -> str | Iterator:
        """获取命令的输出结果"""
        return self._result

    def record_result(self, result: str | Iterator) -> None:
        """记录命令的输出结果"""
        if self._cmd_type is CmdType.SSH_ONE_SHOT and isinstance(result, str):
            self._result = result
        elif self._cmd_type is CmdType.SSH_LONG_RUNNING and isinstance(
            result, Iterator
        ):
            self._result_iter = result

    def get_fmt_prompt(self) -> str:
        """获取格式化终端提示符"""
        tmp = f"[{self._id}]:{self._prompt} {self._cmd}"
        # print(tmp)
        return tmp

    def __str__(self) -> str:
        out = self.get_fmt_prompt()
        if self._cmd_type is CmdType.SSH_ONE_SHOT:
            for line in self.get_result_lines():
                out += f"{line}\n"
        elif self._cmd_type is CmdType.SSH_LONG_RUNNING:
            pass  # TODO:完成不退出指令
        return out

    def get_result_lines(self) -> list[str]:  # TODO:完成不退出指令
        if self._cmd_type is CmdType.SSH_ONE_SHOT:
            return [remove_ansi(e.strip()) for e in self._result.strip().split("\r\n")]
        else:
            pass

    def get_result_line_iter(self) -> Iterator[str]:  # TODO:完成不退出指令
        if self._cmd_type is CmdType.SSH_LONG_RUNNING:
            return iter(self._result.split("\n"))
        else:
            pass
