"""
Message IO 订阅-发布 模式的处理
"""

from __future__ import annotations

import queue
import sys
import threading as td
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, StrEnum, auto
from itertools import count
from typing import Callable, Union

from ..tools.timestamp import Timestamp


@dataclass(frozen=True)
class data_CMD_PROMPT:
    id: int
    name: str
    prompt: str
    command: str


@dataclass(frozen=True)
class data_CMD_OUTPUT:
    id: int | None
    output: str


@dataclass(frozen=True)
class data_LOG:
    name: str
    log: str


@dataclass(frozen=True)
class data_WARNING:
    name: str
    log: str


@dataclass(frozen=True)
class data_ERROR:
    name: str
    log: str


class MessageType(Enum):
    CMD_PROMPT = auto()
    CMD_OUTPUT = auto()
    # CMD_ERROR = auto()
    # CMD_END = auto()
    CONNECT = auto()
    DISCONNECT = auto()
    LOG = auto()
    WARNING = auto()
    ERROR = auto()


class MessageSource(StrEnum):
    USER = auto()
    SYSTEM = auto()
    SSH = auto()
    SSH_CHANNEL = auto()
    SFTP = auto()
    SERIAL = auto()
    TELNET = auto()


_MSGSEQ = count(0)


@dataclass
class Message[T]:
    # 必填信息
    type: MessageType
    source: MessageSource
    timestamp: Timestamp  # 手动填写命令输出的时间戳，以确保时间戳相同
    data: T
    # 默认序号id生成器，无需填写
    seq: int = field(default_factory=lambda: next(_MSGSEQ))


class MessageBus:
    """消息总线"""

    # 消息类型到回调函数的映射，使用 defaultdict 避免 KeyError
    _messages_callback_map: dict[MessageType, list[Callable[[Message], None]]] = (
        defaultdict(list)
    )
    # 回调函数锁，用于线程安全
    _messages_callback_lock: td.Lock = td.Lock()
    # 主进程消息队列
    _main_fifo: queue.Queue[Message] = queue.Queue()

    # use for count stats
    _publish_count: int = 0
    _consume_count: int = 0
    _stats_lock: td.Lock = td.Lock()

    @classmethod
    def subscribe(
        cls, message_type: MessageType, callback: Callable[[Message], None]
    ) -> Callable[[], None]:
        """订阅指定类型的消息"""
        with cls._messages_callback_lock:
            cls._messages_callback_map[message_type].append(callback)

        def unsubscribe():
            with cls._messages_callback_lock:
                try:
                    cls._messages_callback_map[message_type].remove(callback)
                except ValueError:
                    pass

        return unsubscribe

    @classmethod
    def safe_get_subscribers(
        cls, message_type: MessageType
    ) -> list[Callable[[Message], None]]:
        """获取指定类型的所有订阅者"""
        with cls._messages_callback_lock:
            return list(cls._messages_callback_map.get(message_type, []))

    @classmethod
    def has_subscribers(cls, message_type: MessageType) -> bool:
        """检查是否有订阅者"""
        with cls._messages_callback_lock:
            return bool(cls._messages_callback_map.get(message_type, []))

    @classmethod
    def publish(cls, message: Message):
        cls._main_fifo.put_nowait(message)
        with cls._stats_lock:
            cls._publish_count += 1

    @classmethod
    def get_fifo_once(cls, timeout: float | None = None) -> Message | None:
        try:
            msg = cls._main_fifo.get(timeout=timeout)
            # msg = cls._main_fifo.get_nowait()
        except queue.Empty:
            return None

        with cls._stats_lock:
            cls._consume_count += 1

        return msg

    @classmethod
    def get_fifo_until_empty(cls) -> list[Message]:
        messages: list[Message] = []
        if cls._main_fifo.empty():
            msg = cls.get_fifo_once(0.001)
            if msg is not None:
                messages.append(msg)
            return messages
        while not cls._main_fifo.empty():
            try:
                msg = cls._main_fifo.get_nowait()
                messages.append(msg)
            except queue.Empty:
                break  # 恰好取走
        with cls._stats_lock:
            cls._consume_count += len(messages)
            # print(f"{len(messages)} messages")
        return messages

    # @classmethod
    # def get_fifo_size(cls) -> int:
    #     return cls._main_fifo.qsize()

    @classmethod
    def fifo_size(cls) -> int:
        return cls._main_fifo.qsize()

    @classmethod
    def publish_count(cls) -> int:
        with cls._stats_lock:
            return cls._publish_count

    @classmethod
    def consume_count(cls) -> int:
        with cls._stats_lock:
            return cls._consume_count

    @classmethod
    def get_stats(cls) -> dict[str, int]:
        with cls._stats_lock:
            return {
                "publish_count": cls._publish_count,
                "consume_count": cls._consume_count,
                "fifo_size": cls._main_fifo.qsize(),
            }

    @classmethod
    def clear_stats(cls):
        with cls._stats_lock:
            cls._publish_count = 0
            cls._consume_count = 0

    @classmethod
    def shutdown(cls) -> list[Message]:
        messages = cls.get_fifo_until_empty()

        with cls._messages_callback_lock:
            cls._messages_callback_map.clear()

        return messages


_DISP_ID = count(0)


class MessageDispatcher:
    """消息调度器，负责分发MessageBus的fifo中的消息到输出源（OutputLine）"""

    def __init__(self):
        self._lines: dict[int, OutputLine] = {}
        self._lossy_lines_id: list[int] = []
        self._running = False
        self._thread: td.Thread | None = None

    def link_line(self, line: OutputLine, lossy: bool = False) -> OutputLine:
        _id = next(_DISP_ID)
        self._lines[_id] = line
        line.id = _id
        if lossy:
            self._lossy_lines_id.append(_id)
        return line

    def start_line(self, line_id: int) -> None:
        if line_id not in self._lines:
            raise ValueError(f"Line id {line_id} not found")
        self._lines[line_id].start()

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._running = True
        self._thread = td.Thread(
            target=self._dispatch_loop,
            name="MessageDispatcher",
            daemon=True,
        )
        self._thread.start()

    def stop(
        self, timeout: float | None = None, each_line_timeout: float | None = None
    ) -> None:
        self._running = False
        for line in self._lines.values():
            line.stop(each_line_timeout)
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout)

    def join(self, timeout: float | None = None) -> None:
        while (
            MessageBus.fifo_size() > 0
            or MessageBus.publish_count() != MessageBus.consume_count()
        ):
            time.sleep(0.1)
            print(
                MessageBus.fifo_size(),
                MessageBus.publish_count(),
                MessageBus.consume_count(),
            )
        for line in self._lines.values():
            line.join(timeout)

        self.stop(timeout, timeout)

    def _dispatch_loop(self) -> None:
        while self._running:
            # 使用until处理并被有与单次获取有显著速度提升
            msg_list = MessageBus.get_fifo_until_empty()
            if not msg_list:
                continue
            for msg in msg_list:
                if msg is None:
                    continue
                for id, line in self._lines.items():
                    if id in self._lossy_lines_id:
                        line.put_force(msg)
                    else:
                        line.put(msg)

            # msg = MessageBus.get_fifo_once(0.001)
            # if msg is None:
            #     continue
            # for id, line in self._lines.items():
            #     if id in self._lossy_lines_id:
            #         line.put_force(msg)
            #     else:
            #         line.put(msg)


class OutputLine(ABC):
    def __init__(
        self,
        name: str,
        maxsize: int = 0,
    ):
        self._name: str = name
        self.id: int = -1
        self._fifo: queue.Queue[Message | None] = queue.Queue(maxsize=maxsize)
        self._running = False
        self._thread: td.Thread | None = None
        # self._callback: Callable[[Message], None] | None = None
        self._drop_count: int = 0

    @abstractmethod
    def handle(self, msg: Message) -> None:
        # raise NotImplementedError
        ...

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        # self._callback = header
        self._running = True
        self._thread = td.Thread(
            target=self._consume_loop,
            name=f"OutputLine-{self._name}",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout: float | None = None) -> None:
        self._running = False
        self._fifo.put(None)
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            # self._thread = None

    def join(self, timeout: float | None = None) -> None:
        self._fifo.put(None)
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout)

    @property
    def fifo_size(self) -> int:
        return self._fifo.qsize()

    @property
    def drop_count(self) -> int:
        return self._drop_count

    def put(self, msg: Message) -> None:
        self._fifo.put(msg)

    def put_force(self, msg: Message) -> None:
        if self._fifo.full():
            try:
                self._fifo.get_nowait()
                self._drop_count += 1
            except queue.Empty:
                pass  # 基本不可能
        self._fifo.put(msg)

    def _consume_loop(self) -> None:
        while self._running:
            # if self._fifo.empty():
            #     continue
            try:
                msg = self._fifo.get(timeout=0.05)
            except queue.Empty:
                continue
            if msg is None:
                break

            if self.handle:
                try:
                    self.handle(msg)
                except Exception as e:
                    print(
                        f"OutputLine-{self._name}: _callback Error: {e}",
                        file=sys.stderr,
                    )
