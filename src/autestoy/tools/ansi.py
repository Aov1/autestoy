"""一些对于终端ANSI转义序列的处理工具"""

import re

ANSI_ESCAPE_B = re.compile(rb"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
ANSI_ESCAPE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def remove_ansi_bytes(text):
    global ANSI_ESCAPE_B
    return ANSI_ESCAPE_B.sub(b"", text)


def remove_ansi(text):
    global ANSI_ESCAPE
    return ANSI_ESCAPE.sub("", text)
