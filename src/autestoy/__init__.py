from .export.term import Term, TermStyle
from .protocols.ssh import SSH, CollectObj, RemoteConfig
from .tools.ansi import AnsiBackground, AnsiColor, AnsiReset, AnsiStyle
from .tools.control import ulog
from .tools.datatype import Bits
from .tools.timestamp import Timestamp

__all__ = [
    # 重要类或函数
    "SSH",
    "RemoteConfig",
    "ulog",
    "Bits",
    # 终端相关
    "Term",
    "TermStyle",
    "AnsiBackground",
    "AnsiColor",
    "AnsiReset",
    "AnsiStyle",
    # 工具类或函数
    "CollectObj",
    "Timestamp",
    "GlobalTimeBase",
]

# 脚本的基础时间
GlobalTimeBase = Timestamp()
# 终端显示相对时间的计算基时
Term.set_time_base(GlobalTimeBase)
# 导入库时显示本地时间
Term.putsln(
    f"{AnsiStyle.bold}{AnsiColor.black}{AnsiBackground.yellow}[INFO] Srcipt start at [{Term.time_base}]{AnsiReset}"
)
