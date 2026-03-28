import re

import numpy as np


def str2num(s: str) -> tuple[int, int | float]:
    """
    将支持的字符串格式转换为 ( 位数 , 实际值 ) 的tuple\n
    进行数据截断处理等\n
    没有位数标志的返回 ( 0 , 实际值 )\n
    支持下划线和空格分隔长字符\n
    支持科学计数法\n
    支持的格式：
    - 纯数字字符串，带有可选的格式标识（如：456、123_u8）
    - 带小数点的数字字符串，带有可选的格式标识（如：1.23、2_f64）
    - 科学计数法字符串（如：1e6 , -1.5e-3）
    - 2|8|10|16进制字符串，带有可选的格式标识（如：0x1A、0b1010_u8）
    - 布尔值字符串（如：true、false）
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


class Bits:
    def __init__(self, value: int | str, width: int) -> None:
        self.value = value
        self.width = width


class Binary:
    def __init__(self, value: int | str | Bits, force_width: int = 32) -> None:
        pass
