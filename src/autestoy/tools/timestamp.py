from __future__ import annotations

import time
from datetime import datetime, timezone


class Timestamp:
    """
    Timestamp用于记录时间戳，并提供可自定义的格式化输出以及转换
    """

    sw_utc: bool = False
    fmt: str = "%Y-%m-%d %H:%M:%S.%f"
    millis_width: int = 3

    @classmethod
    def len(cls) -> int:
        """返回转换成字符串的长度"""
        return len(cls(0))

    def __init__(self, now_time: float | None = None):
        if now_time:
            self.timestamp = now_time
        else:
            self.timestamp = time.time()

    def __str__(self):
        res = datetime.fromtimestamp(
            self.timestamp, tz=timezone.utc if Timestamp.sw_utc else None
        )
        return res.strftime(Timestamp.fmt)[: -Timestamp.millis_width]

    def __format__(self, format_spec):
        # 委托给 float 的格式化逻辑
        return format(self.__str__(), format_spec)

    def __sub__(self, other: Timestamp | float) -> float:
        if isinstance(other, Timestamp):
            return self.timestamp - other.timestamp
        else:
            return self.timestamp - other

    def __add__(self, other: Timestamp | float) -> float:
        if isinstance(other, Timestamp):
            return self.timestamp + other.timestamp
        else:
            return self.timestamp + other

    def __radd__(self, other: Timestamp | float) -> float:
        return self.__add__(other)

    def __rsub__(self, other: Timestamp | float) -> float:
        if isinstance(other, Timestamp):
            return other.timestamp - self.timestamp
        else:
            return other - self.timestamp

    def update_timestamp(self):
        """强制更新到现在的时间"""
        self.timestamp = time.time()

    def to_float(self) -> float:
        """转换为unix时间戳"""
        return self.timestamp

    def to_seconds_from(self, base: Timestamp | float = 0) -> float:
        """返回从base时间戳开始计算的秒数"""
        return self.timestamp - base
