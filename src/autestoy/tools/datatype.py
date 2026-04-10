from __future__ import annotations

import re
import warnings
from typing import Iterable, Literal, overload

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


def width_in_base(width: int, base: Literal[2, 8, 10, 16]) -> int:
    """计算在特定进制下需显示需要的宽度"""
    if base == 2:
        return width
    elif base == 8:
        return (width + 2) // 3
    elif base == 10:
        return len(str(max_value(width)))
    elif base == 16:
        return (width + 3) // 4
    else:
        raise ValueError(f"{base = } not in [2,8,10,16]")


def insert_every_n(string: str, n: int, sep: str) -> str:
    """将字符串分成 n 长度的片段，插入分隔字符"""
    parts = [string[::-1][i : i + n] for i in range(0, len(string), n)]
    return sep.join(parts)[::-1]


def fmt_in_base(
    value: int,  # 数据
    width: int,  # 宽度
    base: Literal[2, 8, 10, 16],  # 进制 2 8 10 16
    digit_separator: str,  # 分隔副
    digits_per_group: int,  # 每组宽度
    verilog_like: bool = False,  # 默认使用 非 verilog 风格
    upper_base: bool = False,  # 默认小写进制字符
    upper_hex_digits: bool = True,  # 默认大写十六进制字符
) -> str:
    """将整数格式化为指定进制的字符串表示。基本供类内部使用\n
    参数:\n
    ```
    - value             : 要格式化的整数
    - width             : 输出宽度
    - base              : 进制，2 8 10 16 之一
    - digit_separator   : 分隔符
    - digits_per_group  : 每组宽度
    - verilog_like      : 是否使用 verilog 风格
    - upper_base        : 是否使用大写进制字符
    - upper_hex_digits  : 是否使用大写十六进制字符
    ```
    """
    UB = upper_base
    if base == 2:
        if verilog_like:
            return f"{width}'{'B' if UB else 'b'}{insert_every_n(bin(value)[2:].zfill(width_in_base(width, 2)), digits_per_group, digit_separator)}"
        else:
            return f"0{'B' if UB else 'b'}{insert_every_n(bin(value)[2:].zfill(width_in_base(width, 2)), digits_per_group, digit_separator)}"
    elif base == 8:
        if verilog_like:
            return f"{width}'{'O' if UB else 'o'}{insert_every_n(oct(value)[2:].zfill(width_in_base(width, 8)), digits_per_group, digit_separator)}"
        else:
            return f"0{'O' if UB else 'o'}{insert_every_n(oct(value)[2:].zfill(width_in_base(width, 8)), digits_per_group, digit_separator)}"
    elif base == 10:
        if verilog_like:
            return f"{width}'{'D' if UB else 'd'}{insert_every_n(str(value).zfill(width_in_base(width, 10)), digits_per_group, digit_separator)}"
        else:
            return f"{insert_every_n(str(value).zfill(width_in_base(width, 10)), digits_per_group, digit_separator)}"
    elif base == 16:
        if verilog_like:
            head = f"{width}'{'H' if UB else 'h'}"
            digit = f"{insert_every_n(hex(value)[2:].zfill(width_in_base(width, 16)), digits_per_group, digit_separator)}"
            digit = digit.upper() if upper_hex_digits else digit
            return f"{head}{digit}"
        else:
            head = f"0{'X' if UB else 'x'}"
            digit = f"{insert_every_n(hex(value)[2:].zfill(width_in_base(width, 16)), digits_per_group, digit_separator)}"
            digit = digit.upper() if upper_hex_digits else digit
            return f"{head}{digit}"
    else:
        raise ValueError(f"{base = } not in [2,8,10,16]")


class Bits:
    _one_line_max_width = 64
    _to_str_type: Literal[2, 8, 10, 16] = 16
    _digit_separator_width_in_base_2: int = 4
    _digit_separator_width_in_base_8: int = 3
    _digit_separator_width_in_base_10: int = 4
    _digit_separator_width_in_base_16: int = 4
    _digit_separator_type: str = "_"
    _verilog_like_type: bool = False
    _upper_base_symbol: bool = False
    _upper_hex_digits: bool = True

    @classmethod
    def set_verilog_like(cls, verilog_like: bool) -> None:
        cls._verilog_like_type = verilog_like

    @classmethod
    def set_digit_separator(
        cls,
        digit_separator: str,
        width_in_base_2: int = 4,
        width_in_base_8: int = 3,
        width_in_base_10: int = 4,
        width_in_base_16: int = 4,
    ) -> None:
        cls._digit_separator_type = digit_separator
        cls._digit_separator_width_in_base_2 = width_in_base_2
        cls._digit_separator_width_in_base_8 = width_in_base_8
        cls._digit_separator_width_in_base_10 = width_in_base_10
        cls._digit_separator_width_in_base_16 = width_in_base_16

    @classmethod
    def set_upper_base_symbol(cls, upper_base_symbol: bool) -> None:
        cls._upper_base_symbol = upper_base_symbol

    @classmethod
    def set_upper_hex_digits(cls, upper_hex_digits: bool) -> None:
        cls._upper_hex_digits = upper_hex_digits

    @classmethod
    def set_str_type(cls, to_str_type: Literal[2, 8, 10, 16]) -> None:
        cls._to_str_type = to_str_type

    @classmethod
    def set_one_line_max_width(cls, one_line_max_width: int) -> None:
        cls._one_line_max_width = one_line_max_width

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
        self._width: int
        self._value: int

        # value:int && width:int
        if isinstance(value, int) and isinstance(width, int):
            if value < 0 or width <= 0:
                raise ValueError(f"Invalid negative integer: {value} or {width}")
            self._width = width
            self._value = value & ((1 << width) - 1)
        elif isinstance(value, str):
            gwidth, gvalue = str2int(value)
            # value:str && width:None
            if gwidth != 0 and width is None:
                self._width = abs(gwidth)
                self._value = gvalue
            # value:str && width:int
            elif gwidth == 0 and isinstance(width, int) and width > 0:
                self._width = width
                self._value = gvalue & ((1 << self._width) - 1)
            elif gwidth != 0 and isinstance(width, int) and width > 0:
                self._width = width
                self._value = gvalue & ((1 << self._width) - 1)
            else:
                raise ValueError(f"Invalid value: {value} match {width}")
        elif isinstance(value, Bits) and width is None:
            self._value = value._value
            self._width = value._width
        elif isinstance(value, Bits) and isinstance(width, int):
            self._value = value._value & ((1 << width) - 1)
            self._width = width
        elif isinstance(value, Iterable):
            tmp_value = 0
            tmp_width = 0
            for each in value:
                if isinstance(each, str) and str2int(each)[0] != 0:
                    e_width, e_value = str2int(each)
                    tmp_width += abs(e_width)
                    tmp_value = (tmp_value << e_width) | e_value
                elif isinstance(each, Bits):
                    tmp_width += each._width
                    tmp_value = (tmp_value << each.width) | each.value
                elif isinstance(each, tuple) and len(each) == 2:
                    e_value, e_width = each
                    tmp_width += e_width
                    tmp_value = (tmp_value << e_width) | e_value
                else:
                    raise TypeError(f"Invalid Iterable sub value: {each}")
            self._value = tmp_value
            self._width = tmp_width

        # check
        if self._value is None or self._width is None:
            raise TypeError(
                f"Invalid value: input {type(value)}-{value} not match any process"
            )

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, value: int) -> None:
        self._value = value
        self.fix_value()

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, width: int) -> None:
        if width < 1:
            raise ValueError("width must be greater than 0")
        self._width = width
        self.fix_value()

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
    def __getitem__(self, key: Iterable[int | slice]) -> Bits:
        """
        混合切片，支持其他类型的切片同时使用"""
        ...

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

    def __repr__(self) -> str:
        return f"Bits(D:{self.value}|H:{hex(self.value)}|W:{self.width})"

    def __str__(self) -> str:
        return self.fmt(Bits._to_str_type)

    def fmt(self, base: Literal[2, 8, 10, 16], digit_sep: bool = True) -> str:
        if base == 2:
            digit_sep_width = Bits._digit_separator_width_in_base_2
        elif base == 8:
            digit_sep_width = Bits._digit_separator_width_in_base_8
        elif base == 10:
            digit_sep_width = Bits._digit_separator_width_in_base_10
        elif base == 16:
            digit_sep_width = Bits._digit_separator_width_in_base_16
        else:
            raise ValueError(f"{base = } not in [2,8,10,16]")
        return fmt_in_base(
            value=self.value,
            width=self.width,
            base=base,
            digit_separator=Bits._digit_separator_type if digit_sep else "",
            digits_per_group=digit_sep_width,
            upper_base=Bits._upper_base_symbol,
            verilog_like=Bits._verilog_like_type,
            upper_hex_digits=Bits._upper_hex_digits,
        )

    def fix_value(self) -> None:
        """当alue或width被修改之后进行的数据检查与截断处理"""
        self.value = self.value & ((1 << self.width) - 1)

    def set_width(self, width: int) -> None:
        self.width = width
        self.fix_value()


class Binary:
    def __init__(self, value: int | str | Bits, force_width: int = 32) -> None:
        pass
