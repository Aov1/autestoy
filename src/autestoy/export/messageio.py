"""
Message IO 订阅-发布 模式的处理
"""

from __future__ import annotations

import sys
from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import Callable

from ..tools.timestamp import Timestamp


class MessageType(StrEnum):
    CMD_PROMPT = auto()
    CMD_OUTPUT = auto()
    CMD_ERROR = auto()
    CMD_END = auto()
    CONNECT = auto()
    DISCONNECT = auto()
    USER_LOG = auto()
    LOG = auto()


class MessageSource(StrEnum):
    USER = auto()
    SYSTEM = auto()
    SSH = auto()
    SSH_CHANNEL = auto()
    SFTP = auto()
    SERIAL = auto()
    TELNET = auto()


@dataclass
class Message:
    type: MessageType
    source: MessageSource
    timestamp: Timestamp
    data: dict = field(default_factory=dict)


class MessageBus:
    """消息总线"""

    # 消息类型到回调函数的映射，使用 defaultdict 避免 KeyError
    _messages: dict[MessageType, list[Callable[[Message], None]]] = defaultdict(list)

    @classmethod
    def subscribe(
        cls, message_type: MessageType, callback: Callable[[Message], None]
    ) -> Callable[[], None]:
        """订阅指定类型的消息，当消息发布时调用回调函数\n
        返回取消订阅的函数"""
        cls._messages[message_type].append(callback)
        return lambda: cls._messages[message_type].remove(callback)

    @classmethod
    def publish(cls, message: Message):
        for callback in cls._messages[message.type]:
            try:
                callback(message)
            except Exception as e:
                print(
                    f"Error in callback for message type {message.type}: {e}",
                    file=sys.stderr,
                )
