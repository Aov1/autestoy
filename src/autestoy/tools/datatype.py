import re

import numpy as np


def str2type(s: str):
    pass


def str2num(s: str) -> tuple[int, int | float]:
    """
    将支持的字符串格式转换为 ( 位数 , 实际值 ) 的tuple
    位数是verilog支持的显示声明位数的格式或者末尾声明（如：16'd123 , 123_i8）
    无法计算位数的返回 ( 0 , 实际值 )
    支持下划线和空格分隔长字符
    支持科学计数法
    支持的格式：
    - 纯数字字符串
    - 带小数点的数字字符串
    - 科学计数法字符串（如：1e6 , 1.5e-3）
    -
    """
    s = s.replace("_", "").replace(" ", "")

    if re.match(r"^[+-]?[0-9]+$", s):  # 纯数字字符串
        return (0, int(s))
    elif re.match(r"^[+-]?[0-9]+(\.[0-9]+)?$", s):  # 带小数点的数字字符串
        return (0, float(s))
    elif re.match(r"^[+-]?[0-9]+(.[0-9]+)?[eE][+-]?[0-9]+$", s):  # 科学计数法字符串
        return (0, float(s))
    elif re.match(r"^[+-]?[0\\][bB][0-1]+$", s):
        return (0, int(s, 2))
    elif re.match(r"^[+-]?[0\\][oO][0-7]+$", s):
        return (0, int(s, 8))
    elif re.match(r"^[+-]?[0\\][xX][0-9a-fA-F]+$", s):
        return (0, int(s, 16))

    else:
        raise ValueError(f"Invalid integer string: {s}")


class Bits:
    def __init__(self, value: int | str, width: int) -> None:
        self.value = value
        self.width = width


class Binary:
    def __init__(self, value: int | str | Bits, force_width: int = 32) -> None:
        pass
