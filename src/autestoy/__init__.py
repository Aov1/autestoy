"""
autestoy — auto + test + toy
一个用于原型验证的自动化测试工具库。
"""

from __future__ import annotations

# ──────────────────────────────────────────────
# 导出 - 输出收集
# ──────────────────────────────────────────────
from .export.collect import CollectObj, CollectType, collect

# ──────────────────────────────────────────────
# 导出 - Markdown / Obsidian
# ──────────────────────────────────────────────
from .export.markdown import MarkdownExporter, ObsidianExporter

# ──────────────────────────────────────────────
# 导出 - 终端输出
# ──────────────────────────────────────────────
from .export.term import PROMPT_pattern, Term, TermStyle, get_terminal_size

# ──────────────────────────────────────────────
# 协议层 - JTAG（占位）
# ──────────────────────────────────────────────
from .protocols.jtag import Jtag

# ──────────────────────────────────────────────
# 协议层 - 元编程 / DUT 配置基类
# ──────────────────────────────────────────────
from .protocols.metaclass import DUTConfiguratorBase, Protocol

# ──────────────────────────────────────────────
# 协议层 - 串口
# ──────────────────────────────────────────────
from .protocols.serial import Serial, SerialConfig, SerialShell

# ──────────────────────────────────────────────
# 协议层 - SSH
# ──────────────────────────────────────────────
from .protocols.ssh import SFTP, SSH, Channel, RemoteConfig

# ──────────────────────────────────────────────
# 协议层 - Telnet
# ──────────────────────────────────────────────
from .protocols.telnet import Telnet, TelnetConfig, TelnetShell

# ──────────────────────────────────────────────
# 工具 - ANSI 终端转义
# ──────────────────────────────────────────────
from .tools.ansi import (
    AnsiBackground,
    AnsiBackground256,
    AnsiBackgroundTrueColor,
    AnsiColor,
    AnsiColor256,
    AnsiReset,
    AnsiStyle,
    AnsiTrueColor,
    remove_ansi,
)

# ──────────────────────────────────────────────
# 工具 - 屏幕 / 基础信息
# ──────────────────────────────────────────────
from .tools.baseinfo import get_screen_metrics

# ──────────────────────────────────────────────
# 工具 - 流程控制
# ──────────────────────────────────────────────
from .tools.control import TrySeconds, get_line_from_head, ulog

# ──────────────────────────────────────────────
# 工具 - 数据类型
# ──────────────────────────────────────────────
from .tools.datatype import Addr32, Addr64, Bits, BitView, Packet

# ──────────────────────────────────────────────
# 工具 - GUI（占位）
# ──────────────────────────────────────────────
from .tools.gui import Gui

# ──────────────────────────────────────────────
# 工具 - 本地执行
# ──────────────────────────────────────────────
from .tools.local import Local

# ──────────────────────────────────────────────
# 工具 - 命令记录
# ──────────────────────────────────────────────
from .tools.record import CmdRecord, CmdRecording, MetaRecord

# ──────────────────────────────────────────────
# 工具 - 寄存器 / 地址空间枚举
# ──────────────────────────────────────────────
from .tools.register import Field, HasParent, RegGroup, Register

# ──────────────────────────────────────────────
# 工具 - 结果包装
# ──────────────────────────────────────────────
from .tools.result import Result

# ──────────────────────────────────────────────
# 工具 - 时间戳
# ──────────────────────────────────────────────
from .tools.timestamp import Timestamp

# ══════════════════════════════════════════════
# 公开接口列表
# ══════════════════════════════════════════════

__all__ = [
    # ── 终端输出 ──
    "Term",
    "TermStyle",
    "PROMPT_pattern",
    "get_terminal_size",
    # ── 输出收集 ──
    "CollectObj",
    "CollectType",
    "collect",
    # ── 导出 ──
    "MarkdownExporter",
    "ObsidianExporter",
    # ── 协议: SSH ──
    "RemoteConfig",
    "SSH",
    "Channel",
    "SFTP",
    # ── 协议: 串口 ──
    "SerialConfig",
    "Serial",
    "SerialShell",
    # ── 协议: Telnet ──
    "TelnetConfig",
    "Telnet",
    "TelnetShell",
    # ── 协议: JTAG ──
    "Jtag",
    # ── 协议: 元编程 ──
    "DUTConfiguratorBase",
    "Protocol",
    # ── ANSI ──
    "AnsiStyle",
    "AnsiColor",
    "AnsiBackground",
    "AnsiReset",
    "remove_ansi",
    "AnsiColor256",
    "AnsiBackground256",
    "AnsiTrueColor",
    "AnsiBackgroundTrueColor",
    # ── 流程控制 ──
    "ulog",
    "TrySeconds",
    "get_line_from_head",
    # ── 数据类型 ──
    "Bits",
    "BitView",
    "Addr32",
    "Addr64",
    "Packet",
    # ── 本地执行 ──
    "Local",
    # ── 命令记录 ──
    "CmdRecord",
    "CmdRecording",
    "MetaRecord",
    # ── 寄存器 ──
    "HasParent",
    "Field",
    "Register",
    "RegGroup",
    # ── 结果包装 ──
    "Result",
    # ── 时间戳 ──
    "Timestamp",
    # ── 基础信息 ──
    "get_screen_metrics",
    # ── GUI ──
    "Gui",
    # ── 运行时 ──
    "init",
    "GlobalTimeBase",
]

# ══════════════════════════════════════════════
# 运行时状态
# ══════════════════════════════════════════════

from .tools.globalvar import GLOBAL_has_init, GLOBAL_timebase

"""
全局时基。

调用 `init()` 后初始化，所有时间戳将基于此计算相对时间。
在调用 `init()` 之前为 None。
"""


def init() -> Timestamp:
    """初始化 autestoy 运行环境。

    完成以下工作：
      1. 创建全局时间基准 `GlobalTimeBase`
      2. 将 `Term` 的相对时间基线与全局时基绑定
      3. 在终端输出一条启动信息（含启动时间）

    返回:
        Timestamp: 初始化时刻的时间戳

    示例:
        >>> import autestoy as att
        >>> att.init()
        [INFO] Script start at [2026-01-01 12:00:00.000]
    """
    global GLOBAL_timebase
    GLOBAL_timebase = Timestamp()
    global GLOBAL_has_init
    GLOBAL_has_init = True
    # 终端相对时间基线
    # Term.set_time_base(GlobalTimeBase)
    # Term.putsln(
    #     f"{AnsiStyle.bold}{AnsiColor.black}{AnsiBackground.yellow}"
    #     f"[INFO] Script start at [{GlobalTimeBase}]"
    #     f"{AnsiReset}"
    # )

    return GLOBAL_timebase
