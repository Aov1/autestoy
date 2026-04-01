from __future__ import annotations

import re
import warnings
from typing import Iterable, overload

import numpy as np
from numpy.typing import NDArray


def str2num(s: str) -> tuple[int, int | float]:
    """
    将支持的字符串格式转换为 ( 位数 , 实际值 ) 的tuple，只包含正值\n
    进行数据截断处理\n
    没有位数标志的返回 ( 0 , 实际值 )\n
    支持下划线和空格分隔长字符\n
    支持科学计数法\n
    支持的格式：
    - 纯数字字符串，带有可选的格式标识（如：456、123_u8）
    - 带小数点的数字字符串，带有可选的格式标识（如：1.23、2_f64）
    - 科学计数法字符串（如：1e6 , 1.5e-3）
    - 2|8|10|16进制字符串，带有可选的格式标识（如：0x1A、0b1010_u8）
    - 布尔值字符串（如：true、false）
    - verilog位宽字符串（如：8'b10101010、8'sb10101010）
    """
    s = s.replace("_", "").replace(" ", "")

    if res := re.match(r"^([0-9]+)(([iIuU])([0-9]+))?$", s):  # 纯数字字符串
        bits = int(res.group(4)) if res.group(2) else 0
        sign = -1 if res.group(3) in ("i", "I") else 1
        return (
            sign * bits,
            int(res.group(1)) % (1 << bits) if bits else int(res.group(1)),
        )
    elif res := re.match(
        r"^([+-]?([0-9]+)?(\.[0-9]+)?)((fp|f|bf|tf)([0-9]+))?$", s, re.IGNORECASE
    ):  # 带小数点的数字字符串，格式后缀提供位数，解析f32 f64 bf tf等，只解析位数
        bits = int(res.group(6)) if res.group(4) else 0
        return (bits, float(res.group(1)))
    elif re.match(
        r"^[+-]?[0-9]+(.[0-9]+)?[eE][+-]?[0-9]+$", s
    ):  # 科学计数法字符串，无法提供位数
        return (0, float(s))
    elif res := re.match(r"^(0[bB][0-1]+)(([uUiI])([0-9]+))?$", s):  # 0b1001_1100_u8
        bits = int(res.group(4)) if res.group(2) else 0
        sign = -1 if res.group(3) in ("i", "I") else 1
        return (
            sign * bits,
            int(res.group(1), 2) % (1 << bits) if bits else int(res.group(1), 2),
        )
    elif res := re.match(
        r"^(0[oO][0-7]+)(([uUiI])([0-9]+))?$", s
    ):  # eg 0o0123_4567_u32
        bits = int(res.group(4)) if res.group(2) else 0
        sign = -1 if res.group(3) in ("i", "I") else 1
        return (
            sign * bits,
            int(res.group(1), 8) % (1 << bits) if bits else int(res.group(1), 8),
        )
    elif res := re.match(
        r"^0[dD]([0-9]+)(([uUiI])([0-9]+))?$", s
    ):  # eg 0d01_2345_6789_i64
        bits = int(res.group(4)) if res.group(2) else 0
        sign = -1 if res.group(3) in ("i", "I") else 1
        return (
            sign * bits,
            int(res.group(1), 10) % (1 << bits) if bits else int(res.group(1), 10),
        )
    elif res := re.match(
        r"^(0[xX][0-9a-fA-F]+)(([uUiI])([0-9]+))?$", s
    ):  # eg 0x01_2345_6789_ABCD_u64
        bits = int(res.group(4)) if res.group(2) else 0
        sign = -1 if res.group(3) in ("i", "I") else 1
        return (
            sign * bits,
            int(res.group(1), 16) % (1 << bits) if bits else int(res.group(1), 16),
        )
    elif re.match(r"(?i)(True|False|T|F)", s):  # eg True, false, t, f
        return (1, 1 if "t" in s.lower() else 0)

    # verilog bitstring literals
    elif res := re.match(r"(\d+)\'([Ss])?[bB]([01]+)", s):  # eg 8'b1010_1010
        sign = -1 if res.group(2) else 1
        bits = int(res.group(1))
        return (
            sign * bits,
            int(res.group(3), 2) % (1 << bits),
        )
    elif res := re.match(r"(\d+)\'([Ss])?[oO]([0-7]+)", s):  # eg 16'o123_456
        sign = -1 if res.group(2) else 1
        bits = int(res.group(1))
        return (
            sign * bits,
            int(res.group(3), 8) % (1 << bits),
        )
    elif res := re.match(r"(\d+)\'([Ss])?[dD]([0-9]+)", s):  # eg 8'd123
        sign = -1 if res.group(2) else 1
        bits = int(res.group(1))
        return (
            sign * bits,
            int(res.group(3), 10) % (1 << bits),
        )
    elif res := re.match(r"(\d+)\'([Ss])?[hH]([0-9a-fA-F]+)", s):  # eg 8'h1A
        sign = -1 if res.group(2) else 1
        bits = int(res.group(1))
        return (
            sign * bits,
            int(res.group(3), 16) % (1 << bits),
        )
    elif res := re.match(r"(\d+)?\'([01])", s):  # eg 8'1 = 0b11111111  '0 = 0b0
        bits = int(res.group(1)) if res.group(1) else 1
        return (
            bits,
            int(res.group(2) * bits, 2),
        )
    else:
        raise ValueError(f"Invalid integer string: {s}")


def get_value_width(value: int) -> int:
    width = 0
    while value := value >> 1:
        width += 1
    return width


def num2bytes(value: int, width: int | None = None) -> NDArray:
    if value < 0:
        raise ValueError(f"Invalid negative integer: {value}")
    # if width is None:
    width = width if width else 0
    if width <= 0:
        width = get_value_width(value)

    value = value % (1 << width)
    bytes_cnt = (width + 7) // 8

    bytes = value.to_bytes(bytes_cnt)
    barray = np.frombuffer(bytes, dtype=np.uint8)[::-1]
    return barray


def bytes2num(bytes: NDArray[np.uint8]) -> int:
    value = 0
    for i, byte in enumerate(bytes):
        value += byte << (i * 8)
    return value


def slice_width(start: int, stop: int) -> int:
    """返回start和stop之间的宽度"""
    return max(start, stop) - min(start, stop) + 1


def max_value(width: int) -> int:
    """返回宽度为width的最大整数值"""
    return (1 << width) - 1


def to_int(value: float | int) -> int | None:
    """将float转换为int，如果值不一致，则返回None"""
    if isinstance(value, int):
        return value
    else:
        return int(value) if abs(value - int(value)) < 1e-8 else None


def str2int(value: str) -> tuple[int, int]:
    """str2num的缩窄，float转换为int如果值不一致，则raise"""
    gwidth, gvalue = str2num(value)
    gvalue = to_int(gvalue)
    if not gvalue:
        raise ValueError(f"Invalid float string: {value} != int({value})")
    return gwidth, gvalue


class Bits:
    _display_4bits_in_line = 16

    @overload
    def __init__(self, value: int, width: int) -> None:
        """
        当value为int时必须指定宽度\n
        eg: Bits(123, 8) , Bits(0x1234, 16)
        """
        ...

    @overload
    def __init__(self, value: str) -> None:
        """
        当value为str时，并且value可被解析成整数且带有位数标识，自动解析宽度\n
        eg: Bits("16'h1234") , Bits("255_u8") , Bits("0b1000_1110_i32")
        """
        ...

    @overload
    def __init__(self, value: str, width: int) -> None:
        """
        当value为str，且value可被解析为不带宽度的int，width用于指定宽度\n
        eg: Bits("123", 8) , Bits("0x1234", 16)\n
        value可解析为带宽度的整形，且width给出了宽度时，width指定的宽度优先级大于字符串解析的宽度\n
        eg: Bits("0x1234_u16", 32)-> 0x0000_1234 , Bits("0x1234_5678_i32", 16)-> 0x5678\n
        值的注意的是，字符串解析包含了长度截断，width即使大于截断长度，数值依然被截断\n
        eg: Bits("0x12345678_u16",32) -> Bits(0x0000_5678,32)\n
        """
        ...

    @overload
    def __init__(self, value: Bits, width: int) -> None:
        """当value为Bits实例时，width用于指定宽度，相当于重置Bits的宽度"""
        ...

    @overload
    def __init__(self, value: Bits) -> None:
        """当value为Bits实例时，width为None时相当于复制了Bits实例"""
        ...

    @overload
    def __init__(self, value: Iterable[tuple[int | str, int] | str | Bits]) -> None:
        """当value为Iterable时，且Iterable的子类型是支持的初始化类型，创建拼接初始化"""
        ...

    def __init__(
        self, value: int | str | Bits | Iterable, width: int | None = None
    ) -> None:
        self.width: int
        self.value: int

        # value:int && width:int
        if isinstance(value, int) and isinstance(width, int):
            if value < 0 or width <= 0:
                raise ValueError(f"Invalid negative integer: {value} or {width}")
            self.width = width
            self.value = value & ((1 << width) - 1)
        elif isinstance(value, str):
            gwidth, gvalue = str2int(value)
            # value:str && width:None
            if gwidth != 0 and width is None:
                self.width = abs(gwidth)
                self.value = gvalue
            # value:str && width:int
            elif gwidth == 0 and isinstance(width, int) and width > 0:
                self.width = width
                self.value = gvalue & ((1 << self.width) - 1)
            elif gwidth != 0 and isinstance(width, int) and width > 0:
                self.width = width
                self.value = gvalue & ((1 << self.width) - 1)
            else:
                raise ValueError(f"Invalid value: {value} match {width}")
        elif isinstance(value, Bits) and width is None:
            self.value = value.value
            self.width = value.width
        elif isinstance(value, Bits) and isinstance(width, int):
            self.value = value.value & ((1 << width) - 1)
            self.width = width
        elif isinstance(value, Iterable):
            tmp_value = 0
            tmp_width = 0
            for each in value:
                if isinstance(each, str) and str2int(each)[0] != 0:
                    e_width, e_value = str2int(each)
                    tmp_width += abs(e_width)
                    tmp_value = (tmp_value << e_width) | e_value
                elif isinstance(each, Bits):
                    tmp_width += each.width
                    tmp_value = (tmp_value << each.width) | each.value
                elif isinstance(each, tuple) and len(each) == 2:
                    e_value, e_width = each
                    tmp_width += e_width
                    tmp_value = (tmp_value << e_width) | e_value
                else:
                    raise TypeError(f"Invalid Iterable sub value: {each}")
            self.value = tmp_value
            self.width = tmp_width

        # check
        if self.value is None or self.width is None:
            raise TypeError(
                f"Invalid value: input {type(value)}-{value} not match any process"
            )

    @overload
    def __getitem__(self, key: int) -> Bits:
        """获取一位，返回Bits(value=[0 or 1] , width=1 )"""
        ...

    @overload
    def __getitem__(self, key: slice) -> Bits:
        """对Bits实例进行切片，返回一个新的Bits实例，型如 `bits[a:b]` \n
        其中a、b的大小顺序决定了切片的高位在前或低位在前，以适配不同的的描述方式\n
        减小转换的思维负担
        """
        ...

    @overload
    def __getitem__(self, key: Iterable[int | slice]) -> Bits: ...

    def __getitem__(self, key: int | slice | Iterable[int | slice]) -> Bits:
        if isinstance(key, int):
            if key < 0 or key >= self.width:
                raise IndexError(f"Index out of range: {key} with [{self.width - 1}-0]")
            return Bits((self.value >> key) & 1, 1)
        elif isinstance(key, slice):
            st, ed, ex = (key.start, key.stop, key.step)
            if ex is not None:  # TODO
                warnings.warn(f"step will be supported in the future : {slice.step}")
            if isinstance(st, int) and isinstance(ed, int):
                if st > ed:
                    tmp_width = slice_width(st, ed)
                    tmp_val = self.value >> ed & max_value(tmp_width)
                    return Bits(tmp_val, tmp_width)
                elif st < ed:
                    tmp_width = slice_width(st, ed)
                    tmp_val = self.value >> (self.width - 1 - ed) & max_value(tmp_width)
                    return Bits(tmp_val, tmp_width)
                else:  # st==ed
                    return self[st]
            elif isinstance(st, int) and ed is None:
                return self[st]
            elif isinstance(ed, int) and st is None:
                return Bits(self.value >> (self.width - 1 - ed) & 1, 1)
            else:
                raise TypeError("Bits slice start and stop must be integers or None")

        elif isinstance(key, Iterable):
            return Bits([self[each] for each in key])
        else:
            raise TypeError("Bits index must be an integer or slice")

    def __str__(self) -> str:
        return f"Bits({self.value}, {self.width})"


class Binary:
    def __init__(self, value: int | str | Bits, force_width: int = 32) -> None:
        pass
