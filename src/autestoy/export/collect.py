"""实现脚本输出收集，通过装饰器等"""

from __future__ import annotations

from enum import StrEnum, auto
from functools import wraps


class CollectType(StrEnum):
    SSH = auto()
    SFTP = auto()
    Channel = auto()
    Local = auto()
    Serial = auto()
    Telnet = auto()
    TrySeconds = auto()


CollectObj: list[tuple[CollectType, object]] = []


def collect(type: CollectType, storage_dict: list):
    """
    类装饰器：将每个实例添加到 storage_dict 中。要求类的实例拥有name属性作为字典的键
    """

    def decorator(cls):
        original_init = cls.__init__

        @wraps(original_init)
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            storage_dict.append((type, self))

        cls.__init__ = new_init
        return cls

    return decorator
