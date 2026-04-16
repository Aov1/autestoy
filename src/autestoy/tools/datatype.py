from __future__ import annotations

import random
import re
import warnings
from types import MethodType
from typing import (
    Any,
    Callable,
    Iterable,
    Iterator,
    Literal,
    Self,
    overload,
    override,
)

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
    if gvalue is None:
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


def rand_Bits(start: int, end: int, width: int) -> Bits:
    """随即生成一个Bits实例"""
    return Bits(random.randint(start, end), width)


def limit_sub(a: int, b: int, width: int) -> int:
    """限制两个数的差在width范围内，越界循环"""
    a = a & max_value(width)
    b = b & max_value(width)
    tmp = a - b
    return tmp if tmp >= 0 else tmp + max_value(width) + 1


def invert_bits(value: int, width: int) -> int:
    """对一个指定宽度的正整数int进行位反转，返回一个正整数int\n
    内部`~`运算使用"""
    if value < 0:
        raise ValueError(f"value {value} < 0")
    return value & max_value(width) ^ max_value(width)


def sum_value_Bits(*bits: Bits) -> Bits:
    """对多个Bits进行求和，取位宽最宽的Bits作为输出位宽\n
    与直接使用Bits加法进行求和宽度行为不一致，注意\n
    没有想好可以用在哪"""
    sum_value = 0
    max_width = 0
    for e in bits:
        sum_value += e.value
        max_width = max(max_width, e.width)
    return Bits(sum_value, max_width)


def sum_Bits(*bits: Bits) -> Bits:
    """对多个Bits进行求和，位宽取自第一个参数的位宽\n
    符合Bits定义的加法规则"""
    if len(bits) == 1:
        return Bits(bits[0])
    else:
        head = Bits(bits[0])
        for e in bits[1:]:
            head += e
        return head


type BitsInitValue = (
    None | bool | int | str | "Bits" | Iterable[tuple[int | str, int] | str | "Bits"]
)


class Bits:
    _one_line_max_width = 64
    _to_str_type: Literal[2, 8, 10, 16] = 16
    _digit_separator: dict[int, int] = {
        2: 4,
        8: 3,
        10: 4,
        16: 4,
    }
    # _digit_separator_width_in_base_2: int = 4
    # _digit_separator_width_in_base_8: int = 3
    # _digit_separator_width_in_base_10: int = 4
    # _digit_separator_width_in_base_16: int = 4
    _digit_separator_type: str = "_"
    _verilog_like_type: bool = False
    _upper_base_symbol: bool = False
    _upper_hex_digits: bool = True

    @classmethod
    def set_verilog_like(cls, verilog_like: bool) -> None:
        """设置默认显示格式是否使用近似varilog的语法"""
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
        """设置默认显示格式的数字分隔符和宽度"""
        cls._digit_separator_type = digit_separator
        cls._digit_separator[2] = width_in_base_2
        cls._digit_separator[8] = width_in_base_8
        cls._digit_separator[10] = width_in_base_10
        cls._digit_separator[16] = width_in_base_16

    @classmethod
    def set_upper_base_symbol(cls, upper_base_symbol: bool) -> None:
        """设置默认显示格式的进制符号是否大写"""
        cls._upper_base_symbol = upper_base_symbol

    @classmethod
    def set_upper_hex_digits(cls, upper_hex_digits: bool) -> None:
        """设置默认显示格式的十六进制数字是否大写"""
        cls._upper_hex_digits = upper_hex_digits

    @classmethod
    def set_str_type(cls, to_str_type: Literal[2, 8, 10, 16]) -> None:
        """设置默认显示格式的进制类型"""
        cls._to_str_type = to_str_type

    @classmethod
    def set_one_line_max_width(cls, one_line_max_width: int) -> None:
        cls._one_line_max_width = one_line_max_width

    def __init__(
        self,
        value: BitsInitValue,
        width: int | None = None,
    ) -> None:
        self._width: int
        self._value: int

        if value is None:
            self._width = 0
            self._value = 0
        elif isinstance(value, bool):
            self._width = 1 if width is None else width
            self._value = 1 if value else 0
        # value:int && width:int
        elif isinstance(value, int) and isinstance(width, int):
            if value < 0 or width < 0:
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
                    if isinstance(e_value, str):
                        e_value = str2int(e_value)[1]
                    tmp_width += e_width
                    tmp_value = (tmp_value << e_width) | e_value
                else:
                    raise TypeError(f"Invalid Iterable sub value: {each}")
            self._value = tmp_value
            self._width = tmp_width
        else:
            raise TypeError(
                f"Invalid value: input {type(value)}-{value} not match any process"
            )

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
        if self._width < 0:
            self._width = 0
        return self._width

    @width.setter
    def width(self, width: int) -> None:
        if width < 0:
            raise ValueError("width must be greater than 0")
        self._width = width
        self.fix_value()

    def __bool__(self) -> bool:
        return bool(self.value)

    def __len__(self) -> int:
        return self.width

    def _get_value(self, brange: tuple[int, int] | int) -> int:
        """获取维护的value的部分值"""
        if isinstance(brange, int):
            return (self.value >> brange) % 2
        elif isinstance(brange, tuple):
            st, ed = brange
            if st == ed:
                return self._get_value(st)
            elif st > ed:
                return (self.value >> ed) & max_value(st - ed + 1)
            else:
                return (self.value >> (self.width - 1 - ed)) & max_value(ed - st + 1)
        else:
            raise TypeError(f"Unsupported type: {type(brange)}")

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
            elif st is None and ed is None:
                return Bits(self)
            else:
                raise TypeError("Bits slice start and stop must be integers or None")

        elif isinstance(key, Iterable):
            return Bits([self[each] for each in key])
        else:
            raise TypeError("Bits index must be an integer or slice")

    def __repr__(self) -> str:
        """提供调试信息，十进制|十六进制|宽度"""
        return f"Bits(D:{self.value}|H:{hex(self.value)}|W:{self.width})"

    def __str__(self) -> str:
        """对于fmt方法的简单封装，提供了默认进制的显示，可通过类属性修改修改"""
        return self.fmt(Bits._to_str_type, digit_sep=False)

    def __index__(self) -> int:
        return self.value

    def fmt(
        self,
        base: Literal[2, 8, 10, 16],
        digit_sep: bool = True,
        verilog_like: bool | None = None,
    ) -> str:
        """将Bits实例转换为对应进制的字符串，主要用于显示与信息传递"""
        digit_sep_width = Bits._digit_separator.get(base, 4)
        if verilog_like is None:
            verilog_like = Bits._verilog_like_type

        return fmt_in_base(
            value=self.value,
            width=self.width,
            base=base,
            digit_separator=Bits._digit_separator_type if digit_sep else "",
            digits_per_group=digit_sep_width,
            upper_base=Bits._upper_base_symbol,
            verilog_like=verilog_like,
            upper_hex_digits=Bits._upper_hex_digits,
        )

    def __format__(self, format_spec: str, /) -> str:
        """提供自定义的格式化字符串\n
        `{value:[group_options][group_width][verilog_like][type]}`\n
        eg : `{Bits(0x12345678,32):4H}` -> '0x1234_5678'\n
        eg : `{Bits(0x12345678,32):,2H}` -> '0x12,34,56,78'\n
        """
        # print(f"{format_spec = }")
        cmd = re.match(
            r"([^\dvVbBhHdDoO])?(\d+)?(([vV])?([bBhHdDoO]))?",
            format_spec,
        )
        if cmd:
            verilog_like = True if cmd.group(4) else False
            g5 = cmd.group(5)
            base = (
                2
                if g5 == "B" or g5 == "b"
                else 8
                if g5 == "O" or g5 == "o"
                else 10
                if g5 == "D" or g5 == "d"
                else 16
                if g5 == "H" or g5 == "h"
                else 16
            )
            if cmd.group(1) and cmd.group(2):  # 有分隔符且有宽度
                group_width = int(cmd.group(2))
                sep = cmd.group(1)
            elif cmd.group(1) and not cmd.group(2):  # 有分隔符但没有宽度
                sep = cmd.group(1)
                group_width = Bits._digit_separator.get(base, 4)
            elif cmd.group(2) and not cmd.group(1):  # 没有分隔符但有宽度
                sep = "_"
                group_width = Bits._digit_separator.get(base, 4)
            else:
                sep = ""
                group_width = 4

            upper_hex = True if cmd.group(5) == "H" else False
            return fmt_in_base(
                self.value,
                self.width,
                base,
                sep,
                group_width,
                verilog_like,
                upper_hex_digits=upper_hex,
            )
        else:
            return str(self)

    def fix_value(self) -> None:
        """当alue或width被修改之后进行的数据检查与截断处理"""
        self._value = self._value & ((1 << self.width) - 1)

    def set_width(self, width: int) -> None:
        self.width = width
        self.fix_value()

    def _split_range(
        self, brange: tuple[int, int] | int
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        """将self.value按照range分割为两个部分，以tuple表示，第一个tuple为高位，第二个tuple为低位\n
        每个tuple中第一位是宽度，第二位是值，即返回((width_high,value_high), (width_low,value_low))"""
        val = self.value
        if isinstance(brange, int):
            if brange >= self.width or brange < 0:
                raise ValueError(
                    f"Range exceeds width: {brange} >= {self.width} or < 0"
                )
            return self._split_range((brange, brange))
        elif isinstance(brange, tuple):
            if any(brange) < 0 or any(brange) >= self.width:
                raise ValueError(
                    f"Range exceeds width: {brange} >= {self.width} or < 0"
                )

            if brange[0] >= brange[1]:
                rh, rl = brange
            else:  # brange[0] < brange[1]
                rh = self.width - 1 - brange[0]
                rl = self.width - 1 - brange[1]

            width_high = self.width - 1 - rh
            value_high = (val >> (rh + 1)) & max_value(width_high)
            width_low = rl
            value_low = val & max_value(rl)
            return (width_high, value_high), (width_low, value_low)

    def split_iter(
        self,
        group_width: int,
        right_align: bool = True,
        from_left: bool = True,
        times: int = -1,
    ) -> Iterator[Bits]:
        """将Bits类的值按照group_width分割为多个Bits类，返回一个迭代器"""
        if group_width < 1 or group_width > self.width:
            raise ValueError(f"Invalid group width: {group_width}")
        if right_align:
            if from_left:
                d = self.width % group_width
                if d != 0:
                    yield self[0 : d - 1]
                for i in range(d, self.width, group_width):
                    yield self[i : i + group_width - 1]
            else:  # from_right
                d = self.width % group_width
                for i in range(0, self.width - d, group_width):
                    yield self[i + group_width - 1 : i]
                if d != 0:
                    yield self[self.width - 1 : self.width - d]
        else:  # left_align
            if from_left:
                d = self.width % group_width
                for i in range(0, self.width - d, group_width):
                    yield self[i : i + group_width - 1]
                if d != 0:
                    yield self[self.width - d : self.width - 1]
            else:  # from_right
                d = self.width % group_width
                if d != 0:
                    yield self[d - 1 : 0]
                for i in range(d, self.width, group_width):
                    yield self[i + group_width - 1 : i]

    def split(self, group_width: int) -> list[Bits]:
        """将Bits类的值按照group_width分割为多个Bits类，返回一个列表\n
        遵循右对齐、高位在列表前的顺序，即
        ```python
        val = Bits(0xF_1234_5678,33) # 高位0xF截断为0x1
        val.split(8)
        # 返回 [Bits(0x1,1), Bits(0x12,8).Bits(0x34,8),Bits(0x56,8),Bits(0x78,8)]
        ```
        需要其他对齐方式以及输出顺序请使用list(self.split_iter(group_width, right_align, from_left))
        """
        return list(self.split_iter(group_width))

    def concat(self, other: Bits) -> Bits:
        """拼接两个Bits类，返回一个新的Bits类"""
        return Bits((self.value << other.width) | other.value, self.width + other.width)

    def append(self, *other: Bits | Iterable[Bits]) -> Self:
        """在当前Bits类的末尾拼接另一些Bits类"""
        for e in other:
            if isinstance(e, Bits):
                self.width += e.width
                self.value = (self.value << e.width) | e.value
            elif isinstance(e, Iterable):
                for ee in e:
                    self.append(ee)
        return self

    def pop(self, width: int, from_low_bit: bool = True) -> Bits:
        """从当前Bits类的末尾(默认低位)弹出指定宽度的值，以新的Bits类返回弹出的值"""
        if width > self.width:
            raise ValueError(
                f"width {width} is too large for Bits of width {self.width}"
            )
        if from_low_bit:
            pop_value = self[width - 1 : 0]
            self.value >>= width
        else:
            pop_value = self[0 : width - 1]
            self.value &= max_value(self.width - width)
        self.width -= width
        return pop_value

    def remove(self, brange: tuple[int, int] | int) -> Bits:
        """从当前Bits类中移除指定范围的值，剩余范围拼接"""
        (high_width, high_value), (low_width, low_value) = self._split_range(brange)
        rm_bits = (
            self[brange[0] : brange[1]] if isinstance(brange, tuple) else self[brange]
        )
        self.width = high_width + low_width
        self.value = (high_value << low_width) | low_value
        return rm_bits

    def set_bits(
        self, range: tuple[int, int] | int, value: int | str | Bits | bool
    ) -> None:
        """设置Bits类中间范围的值"""
        set_value = 0
        if isinstance(value, bool):
            set_value = 1 if value else 0
        elif isinstance(value, int):
            if value < 0:
                raise ValueError(f"Negative value not supported: {value}")
            set_value = value
        elif isinstance(value, str):
            set_value = str2int(value)[1]
        elif isinstance(value, Bits):
            set_value = value.value
        else:
            raise TypeError(f"Unsupported type for value: {type(value)}")

        set_width = 1
        if isinstance(range, int):
            set_width = 1
            set_value = set_value % 2
        elif isinstance(range, tuple):
            set_width = abs(range[1] - range[0]) + 1
            set_value = set_value & max_value(set_width)
        else:
            raise TypeError(f"Unsupported type for range: {type(range)}")

        (width_high, value_high), (width_low, value_low) = self._split_range(range)
        assert width_high + width_low + set_width == self.width, (
            f"set_bits width Error {width_high}+{width_low}+{set_width} != {self.width}"
        )
        self.value = (
            (value_high << (width_low + set_width))
            | (set_value << width_low)
            | value_low
        )

    @overload
    def __setitem__(self, key: int, value: int | str | Bits | bool) -> None: ...

    @overload
    def __setitem__(self, key: slice, value: int | str | Bits | bool) -> None: ...

    @overload
    def __setitem__(
        self, key: Iterable[int | slice], value: int | str | Bits | bool
    ) -> None: ...

    def __setitem__(
        self, key: int | slice | Iterable[int | slice], value: int | str | Bits | bool
    ) -> None:
        """支持切片赋值的语法\n
        ```python
        t = Bits(0x1234_5678, 32)
        t[0:15] = Bits("16'hffff") # -> Bits(0xFFFF_5678,32)
        t[15:0] = 0xFFFF           # -> Bits(0xFFFF_FFFF,32)
        t[0:15] = "32'h1111_1111"  # -> Bits(0x1111_FFFF,32)
        t = Bits(0x0000_0000,32)
        t[0]  = 1 # Bits(0x0000_0001, 32)
        t[4:] = 1 # Bits(0x0000_0011, 32)
        t[:3] = 1 # Bits(0x1000_0011, 32)
        ```
        """
        if isinstance(key, int):
            self.set_bits(key, value)
        elif isinstance(key, slice):
            st, ed, exp = key.start, key.stop, key.step
            if exp is not None:
                raise ValueError("step is not supported")

            if isinstance(st, int) and isinstance(ed, int):
                self.set_bits((st, ed), value)
            elif isinstance(st, int) and ed is None:
                self.set_bits(st, value)
            elif isinstance(ed, int) and st is None:
                self.set_bits(self.width - 1 - ed, value)
            elif st is None and ed is None:
                self.set_bits((self.width - 1, 0), value)
            else:
                raise TypeError(f"Unsupported key type: {type(key)}")
        elif isinstance(key, Iterable):  # 混合赋值，用于一次性设置多位
            field_widths: list[int] = []
            for k in key:
                if isinstance(k, int):
                    field_widths.append(1)
                elif isinstance(k, slice):
                    st, ed, exp = k.start, k.stop, k.step
                    if exp is not None:
                        raise ValueError("step is not supported")
                    if isinstance(st, int) and isinstance(ed, int):
                        field_widths.append(abs(st - ed) + 1)
                    elif isinstance(st, int) and ed is None:
                        field_widths.append(1)
                    elif isinstance(ed, int) and st is None:
                        field_widths.append(1)
            all_width = sum(field_widths) + 1  # pop无法超过Bits宽度
            set_value = Bits(value, all_width)
            width_index = 0
            for k in key:
                if isinstance(k, int):
                    self.set_bits(
                        k, set_value.pop(field_widths[width_index], from_low_bit=False)
                    )
                    width_index += 1
                elif isinstance(k, slice):
                    st, ed = k.start, k.stop
                    if isinstance(st, int) and isinstance(ed, int):
                        self.set_bits(
                            (st, ed),
                            set_value.pop(
                                field_widths[width_index], from_low_bit=False
                            ),
                        )
                        width_index += 1
                    elif isinstance(st, int) and ed is None:
                        self.set_bits(
                            st,
                            set_value.pop(
                                field_widths[width_index], from_low_bit=False
                            ),
                        )
                        width_index += 1
                    elif isinstance(ed, int) and st is None:
                        self.set_bits(
                            self.width - 1 - ed,
                            set_value.pop(
                                field_widths[width_index], from_low_bit=False
                            ),
                        )
                        width_index += 1

    def __eq__(self, other: object) -> bool:
        # self.fix_value()
        if isinstance(other, Bits):
            return self.value == other.value and self.width == other.width
        elif isinstance(other, tuple) and len(other) == 2:
            return self == Bits(other[0], other[1])
        elif isinstance(other, str):
            return self == Bits(other)
        elif isinstance(other, int):
            return self.value == other
        elif isinstance(other, bool):
            return self.value != 0
        elif other is None:
            return self.width == 0 and self.value == 0
        else:
            raise TypeError(f"unsupported type: {type(other)}")

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Bits):
            return self.value < other.value
        elif isinstance(other, tuple) and len(other) == 2:
            return self < Bits(other[0], other[1])
        elif isinstance(other, str):
            return self < Bits(other)
        elif isinstance(other, int):
            return self.value < other
        else:
            raise TypeError(f"unsupported type: {type(other)}")

    def __le__(self, other: object) -> bool:
        return not self.__gt__(other)

    def __gt__(self, other: object) -> bool:
        if isinstance(other, Bits):
            return self.value > other.value
        elif isinstance(other, tuple) and len(other) == 2:
            return self > Bits(other[0], other[1])
        elif isinstance(other, str):
            return self > Bits(other)
        elif isinstance(other, int):
            return self.value > other
        else:
            raise TypeError(f"unsupported type: {type(other)}")

    def __ge__(self, other: object) -> bool:
        return not self.__lt__(other)

    def borrow(self, brange: tuple[int, int] | int | None) -> BitView:
        """返回一个新的BitView实例，是本身Bits的范围借用"""
        return BitView(self, brange)

    def __add__(self, obj: BitsInitValue | tuple[int | str, int]) -> Bits:
        if obj is None:
            return Bits(self)
        elif isinstance(obj, Bits):
            return Bits(self.value + obj.value, self.width)
        elif isinstance(obj, bool):
            return Bits(self.value + int(obj), self.width)
        elif isinstance(obj, int):
            return Bits(self.value + obj, self.width)
        elif isinstance(obj, str):
            return self.__add__(Bits(obj, self.width))
        elif isinstance(obj, Iterable):
            tmp = Bits(self)
            for e in obj:
                if isinstance(e, (int, str, Bits, bool)):
                    tmp = tmp + e
                else:
                    raise TypeError(f"Bits.__add__ Unsupported type: {type(obj)}")
            return tmp
        else:
            raise TypeError(f"Bits.__add__ Unsupported type: {type(obj)}")

    def __sub__(self, obj: BitsInitValue) -> Bits:
        if obj is None:
            return Bits(self)
        elif isinstance(obj, Bits):
            return Bits(limit_sub(self.value, obj.value, self.width), self.width)
        elif isinstance(obj, bool):
            return Bits(limit_sub(self.value, int(obj), self.width), self.width)
        elif isinstance(obj, int):
            return Bits(limit_sub(self.value, obj, self.width), self.width)
        elif isinstance(obj, str):
            return self.__sub__(Bits(obj, self.width))
        elif isinstance(obj, Iterable):
            tmp = Bits(self)
            for e in obj:
                if isinstance(e, (int, str, Bits, bool)):
                    tmp = tmp - e
                else:
                    raise TypeError(f"Bits.__sub__ Unsupported type: {type(obj)}")
            return tmp
        else:
            raise TypeError(f"Bits.__sub__ Unsupported type: {type(obj)}")

    def __iadd__(self, other: int | str | Bits | bool | None) -> Self:
        """支持 += 运算符的原地加法"""
        if isinstance(other, (int, str, Bits, bool)):
            self.value = (Bits(self) + other).value
            return self
        elif other is None:
            return self
        else:
            raise TypeError(f"Bits.__iadd__ Unsupported type: {type(other)}")

    def __isub__(self, other: int | str | Bits | bool | None) -> Self:
        """支持 -= 运算符的原地减法"""
        if isinstance(other, (int, str, Bits, bool)):
            self.value = (Bits(self) - other).value
            return self
        elif other is None:
            return self
        else:
            raise TypeError(f"Bits.__isub__ Unsupported type: {type(other)}")

    def __radd__(self, other: int | str | Bits | bool | None) -> Bits:
        """支持 + 运算符的右向加法"""
        if isinstance(other, (int, str, Bits, bool)):
            return Bits(other) + self
        elif other is None:
            return self
        else:
            raise TypeError(f"Bits.__radd__ Unsupported type: {type(other)}")

    def __rsub__(self, other: int | str | Bits | bool | None) -> Bits:
        """支持 - 运算符的右向减法"""
        if isinstance(other, (int, str, Bits, bool)):
            return Bits(other) - self
        elif other is None:
            return Bits(None) - self
        else:
            raise TypeError(f"Bits.__rsub__ Unsupported type: {type(other)}")

    def __rshift__(self, other: int) -> Bits:
        """支持 >> 运算符的右向移位"""
        if isinstance(other, int):
            return Bits(self.value >> other, self.width)
        else:
            raise TypeError(f"Bits.__rshift__ Unsupported type: {type(other)}")

    def __lshift__(self, other: int) -> Bits:
        """支持 << 运算符的左向移位"""
        if isinstance(other, int):
            return Bits(self.value << other, self.width)
        else:
            raise TypeError(f"Bits.__lshift__ Unsupported type: {type(other)}")

    def __irshift__(self, other: int) -> Self:
        """支持 >>= 运算符的右向移位"""
        if isinstance(other, int):
            self.value = self.value >> other
            return self
        else:
            raise TypeError(f"Bits.__rshift__ Unsupported type: {type(other)}")

    def __ilshift__(self, other: int) -> Self:
        """支持 <<= 运算符的左向移位"""
        if isinstance(other, int):
            self.value = self.value << other
            return self
        else:
            raise TypeError(f"Bits.__lshift__ Unsupported type: {type(other)}")

    def __or__(self, other: Bits | int | str | bool) -> Bits:
        """支持 Bits | other\n
        值得注意的是，以左侧的位宽为运算基础，右侧运算数支持无位宽表述"""
        if isinstance(other, Bits):
            return Bits(self.value | other.value, self.width)
        elif isinstance(other, int):
            return Bits(self.value | other, self.width)
        elif isinstance(other, str):
            return self | Bits(other)
        else:
            raise TypeError(f"Unsupport type: {type(other)}")

    def __ror__(self, other: str | bool) -> Bits:
        """支持 `|` 位或运算符的左操作数为str或bool，右操作数为Bits的情况\n
        左操作数决定位宽\n
        str必须待用位宽标识，可以被Bits初始化所接受\n
        bool的位宽固定为1"""
        return Bits(other) | self

    def __ior__(self, other: Bits | int | str | bool) -> Self:
        """支持 `|=` 位或运算符的原地操作"""
        self.value = (self | other).value
        return self

    def __and__(self, other: Bits | int | str | bool) -> Bits:
        """支持 `&` 位与运算符的左操作数为Bits的情况\n
        位宽由左操作数决定"""
        if isinstance(other, Bits):
            return Bits(self.value & other.value, self.width)
        elif isinstance(other, int):
            return Bits(self.value & other, self.width)
        elif isinstance(other, str):
            return self & Bits(other)
        else:
            raise TypeError(f"Unsupport type: {type(other)}")

    def __rand__(self, other: str | bool) -> Bits:
        """支持 `&` 位与运算符的左操作数为str或bool，右操作数为Bits的情况\n
        左操作数决定位宽\n
        str必须拥有位宽标识；bool的位宽为1"""
        return Bits(other) & self

    def __iand__(self, other: Bits | int | str | bool) -> Self:
        """支持 `&=` 位与运算符的原地操作"""
        self.value = (self & other).value
        return self

    def __xor__(self, other: Bits | int | str | bool) -> Bits:
        """支持 `^` 异或运算符的左操作数为Bits的情况\n
        位宽由左操作数决定"""
        if isinstance(other, Bits):
            return Bits(self.value ^ other.value, self.width)
        elif isinstance(other, int):
            return Bits(self.value ^ other, self.width)
        elif isinstance(other, str):
            return self ^ Bits(other)
        else:
            raise TypeError(f"Unsupport type: {type(other)}")

    def __rxor__(self, other: str | bool) -> Bits:
        """支持 `^` 异或运算符的左操作数为str或bool，右操作数为Bits的情况\n
        位宽依据左操作数\n
        str必须待用位宽标识，可以被Bits初始化所接受\n
        bool的位宽固定为1"""
        return Bits(other) ^ self

    def __ixor__(self, other: Bits | int | str | bool) -> Self:
        """支持 `^` 异或运算符的原地修改"""
        self.value = (self ^ other).value
        return self

    def __invert__(self) -> Bits:
        """支持 `~` 取反符号"""
        return Bits(invert_bits(self.value, self.width), self.width)

    def invert(self) -> Self:
        """将Bits实例自身的值按位取反，返回自身\n
        如果只是想获取一个新的取反实例用作赋值，使用取反符号`~`"""
        self.value = invert_bits(self.value, self.width)
        return self

    def __int__(self) -> int:
        """支持 `int()` 转换，返回Bits实例的值"""
        return self.value

    def __float__(self) -> float:
        """支持 `float()` 转换，返回Bits实例的值"""
        return float(self.value)


class BitView(Bits):
    """用于对Bits类实例的借用，实质上是维护了一个指向Bits的指针和范围，作出异步读取与修改\n
    即仅在读取BitView实例的value时才会从master更新数据，以及设置value时同步向master修改数据"""

    def __init__(self, master: Bits, brange: tuple[int, int] | int | None) -> None:
        """parm `master`： 借用的原始Bits实例\n
        parm `brange`：要借用的范围，int时是右对齐的单个位，(int,int)时是包括边界的切片范围，None时是整个master的范围\n
        """

        self.master: Bits = master
        self.master_id = id(self.master)
        self.brange: tuple[int, int]
        if isinstance(brange, int):
            self.brange = (brange, brange)
            tmp_value = self.master._get_value(self.brange)
            tmp_width = 1
        elif isinstance(brange, tuple):
            self.brange = brange
            tmp_value = self.master._get_value(self.brange)
            tmp_width = abs(brange[0] - brange[1]) + 1
        elif brange is None:
            self.brange = (0, self.master.width - 1)
            tmp_value = self.master.value
            tmp_width = self.master.width
        else:
            raise TypeError(f"unsupported type: {type(brange)}")
        super().__init__(tmp_value, tmp_width)

    @property
    def value(self) -> int:
        self._value = self.master._get_value(self.brange)
        return self._value

    @value.setter
    def value(self, value: int) -> None:
        self._value = value
        self.fix_value()
        self.master.set_bits(self.brange, self._value)


class Addr32(Bits):
    def __init__(
        self,
        address: BitsInitValue,
    ):
        super().__init__(address, 32)


class Addr64(Bits):
    def __init__(self, address: BitsInitValue):
        super().__init__(address, 64)

    @override
    def split(self, group_width: int = 32) -> list[Addr32 | Bits]:  # type: ignore
        """Addr64覆盖了split，提供了默认分割值32，并返回Addr32\n
        分割宽度非32时依旧返回Bits类"""
        if group_width != 32:
            return super().split(group_width)
        high, low = super().split(group_width)
        return [Addr32(high), Addr32(low)]


class Field(BitView):
    def __init__(
        self,
        master: Bits,
        name: str,
        brange: tuple[int, int] | int,
        default_value: BitsInitValue | None = None,
        info: str = "",
    ) -> None:
        self.master: Bits = master
        self.name: str = name
        self.field_brange: tuple[int, int] = (
            brange if isinstance(brange, tuple) else (brange, brange)
        )
        self.field_width: int = self.field_brange[1] - self.field_brange[0] + 1
        self.default_value: Bits | None = (
            Bits(default_value, self.field_width) if default_value is not None else None
        )
        self.enums: dict[str, dict[str, Any]] = {}
        self.info: str = info
        super().__init__(self.master, self.field_brange)

    def add_enum(self, name: str, value: int | Bits | bool | str, info: str = ""):
        self.enums[name] = {
            "value": Bits(value, self.field_width),
            "info": info,
        }

    def select_enum(self, name: str) -> None:
        if name not in self.enums:
            raise ValueError(f"Enum {name} not found")
        self.value = self.enums[name]["value"].value


class Register:
    def __init__(
        self,
        address: Addr32 | Addr64,
        name: str | None = None,
        value_width: int = 32,
        read_method: Callable | None = None,
        write_method: Callable | None = None,
    ) -> None:
        self.address: Addr32 | Addr64 = address
        self.name: str | None = name
        self.bits_width: int = value_width
        self.bits: Bits = Bits(0, value_width)
        self.fields: dict[str, Field] = {}
        self.bitmap = Bits(0, value_width)
        self.read_method: Callable | None = (
            None if read_method is None else self.config_read_method(read_method)
        )
        self.write_method: Callable | None = (
            None if write_method is None else self.config_write_method(write_method)
        )

    def add_field(
        self,
        name: str,
        brange: tuple[int, int] | int,
        default_value: BitsInitValue | None = None,
    ) -> None:
        if self._is_field_overlap(brange):
            raise ValueError(f"Field {name} overlaps with existing field")
        field = Field(self.bits, name, brange, default_value)
        self.fields[field.name] = field
        st, ed = brange if isinstance(brange, tuple) else (brange, brange)
        self.bitmap[st:ed] = max_value(field.width)

    def _is_field_overlap(self, brange: tuple[int, int] | int) -> bool:
        return (
            self.bitmap[brange[0] : brange[1]]
            if isinstance(brange, tuple)
            else self.bitmap[brange]
        ) != 0

    def __getattr__(self, name: str) -> Field:
        if (res := self.fields.get(name)) is not None:
            return res
        raise AttributeError(f"'Register' object has no attribute '{name}'")

    def config_read_method(self, func: Callable) -> None:
        self.read_method = MethodType(func, self)

    def config_write_method(self, func: Callable) -> None:
        self.write_method = MethodType(func, self)

    def read(self, *args, **kwargs) -> Any:
        if self.read_method is None:
            raise NotImplementedError("read_method is not configured")
        return self.read_method(*args, **kwargs)

    def write(self, value: int, *args, **kwargs) -> None:
        if self.write_method is None:
            raise NotImplementedError("write_method is not configured")
        self.write_method(value, *args, **kwargs)


class Packet:
    def __init__(
        self,
    ) -> None:
        self.bits: Bits
