import re
from typing import overload

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


class Bits:
    @overload
    def __init__(self, value: int, width: int) -> None:
        """
        当value为int时必须指定宽度
        """
        ...

    @overload
    def __init__(self, value: str) -> None:
        """
        当value为str时，并且value可被解析成整数且带有位数标识，自动解析宽度
        """
        ...

    @overload
    def __init__(self, value: str, width: int) -> None:
        """
        当value为str，且value可被解析为不带宽度的int，width用于指定宽度\n
        value可解析为带宽度的整形，且width给出了宽度时，取较大的宽度以保证无信息丢失
        """
        ...

    def __init__(self, value: int | str, width: int | None = None) -> None:
        if isinstance(value, int) and isinstance(width, int):
            if value < 0 or width <= 0:
                raise ValueError(f"Invalid negative integer: {value} or {width}")
            self.width = width
            self.bytes_cnt = (width + 7) // 8
            self.value = value & ((1 << width) - 1)
            self.bytes = num2bytes(value, width)
            self.signed = False
        elif isinstance(value, str):
            gwidth, gvalue = str2num(value)
            if gwidth != 0 and width is None:
                if isinstance(gvalue, float) and abs(gvalue - int(gvalue)) < 1e-6:
                    gvalue = int(gvalue)
                else:
                    raise ValueError(f"Invalid float: {value}")
                self.signed = gwidth < 0
                self.width = abs(gwidth)
                self.bytes_cnt = (self.width + 7) // 8
                self.value = gvalue
                self.bytes = num2bytes(self.value, self.width)
            elif gwidth == 0 and isinstance(width, int) and width > 0:
                if isinstance(gvalue, float) and abs(gvalue - int(gvalue)) < 1e-6:
                    gvalue = int(gvalue)
                else:
                    raise ValueError(f"Invalid float: {value}")
                self.signed = False
                self.width = width
                self.bytes_cnt = (self.width + 7) // 8
                self.value = gvalue & ((1 << self.width) - 1)
                self.bytes = num2bytes(self.value, self.width)
            elif gwidth != 0 and isinstance(width, int):
                if isinstance(gvalue, float) and abs(gvalue - int(gvalue)) < 1e-6:
                    gvalue = int(gvalue)
                else:
                    raise ValueError(f"Invalid float: {value}")
                self.signed = gwidth < 0
                self.width = max(width, abs(gwidth))
                self.bytes_cnt = (self.width + 7) // 8
                self.value = gvalue & ((1 << self.width) - 1)
                self.bytes = num2bytes(self.value, self.width)
            else:
                raise ValueError(f"Invalid value: {value} match {width}")


class Binary:
    def __init__(self, value: int | str | Bits, force_width: int = 32) -> None:
        pass
