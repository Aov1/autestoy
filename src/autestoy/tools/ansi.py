"""一些对于终端ANSI转义序列的处理工具"""

import re
from enum import StrEnum
from typing import TypeVar, overload

ANSI_ESCAPE_B = re.compile(rb"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
ANSI_ESCAPE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


@overload
def remove_ansi(text: bytes) -> bytes: ...


@overload
def remove_ansi(text: str) -> str: ...


# T = TypeVar("T")


# @overload
# def remove_ansi(text: T) -> str: ...


# def remove_ansi_bytes(text: bytes):
#     global ANSI_ESCAPE_B
#     return ANSI_ESCAPE_B.sub(b"", text)


def remove_ansi(text: str | bytes) -> str | bytes:
    if isinstance(text, bytes):
        global ANSI_ESCAPE_B
        return ANSI_ESCAPE_B.sub(b"", text)
    else:
        global ANSI_ESCAPE
        return ANSI_ESCAPE.sub("", text)


AnsiReset = "\033[0m"


class AnsiStyle(StrEnum):
    bold = "\033[1m"
    dark = "\033[2m"
    italic = "\033[3m"
    underline = "\033[4m"

    exchange = "\033[7m"
    hidden = "\033[8m"
    delateline = "\033[9m"


class AnsiColor(StrEnum):
    none = ""
    black = "\033[30m"
    red = "\033[31m"
    green = "\033[32m"
    yellow = "\033[33m"
    blue = "\033[34m"
    magenta = "\033[35m"
    cyan = "\033[36m"
    white = "\033[37m"

    light_black = "\033[90m"
    light_red = "\033[91m"
    light_green = "\033[92m"
    light_yellow = "\033[93m"
    light_blue = "\033[94m"
    light_magenta = "\033[95m"
    light_cyan = "\033[96m"
    light_white = "\033[97m"


class AnsiBackground(StrEnum):
    none = ""
    black = "\033[40m"
    red = "\033[41m"
    green = "\033[42m"
    yellow = "\033[43m"
    blue = "\033[44m"
    magenta = "\033[45m"
    cyan = "\033[46m"
    white = "\033[47m"

    light_black = "\033[100m"
    light_red = "\033[101m"
    light_green = "\033[102m"
    light_yellow = "\033[103m"
    light_blue = "\033[104m"
    light_magenta = "\033[105m"
    light_cyan = "\033[106m"
    light_white = "\033[107m"


def AnsiColor256(color: int) -> str:
    color = max(0, min(255, color))
    return f"\033[38;5;{color}m"


def AnsiBackground256(color: int) -> str:
    color = max(0, min(255, color))
    return f"\033[48;5;{color}m"


def AnsiTrueColor(r: int, g: int, b: int) -> str:
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    return f"\033[38;2;{r};{g};{b}m"


def AnsiBackgroundTrueColor(r: int, g: int, b: int) -> str:
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    return f"\033[48;2;{r};{g};{b}m"
