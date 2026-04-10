from .export.term import Term, TermStyle
from .protocols.ssh import SSH, CollectObj, RemoteConfig
from .tools.ansi import AnsiBackground, AnsiColor, AnsiReset, AnsiStyle
from .tools.control import ulog
from .tools.record import CmdRecord
from .tools.timestamp import Timestamp

# from .tools.ansi import remove_ansi,remove_ansi_bytes
__all__ = [
    # export/term.py
    "Term",
    "TermStyle",
    "ulog",
    # protocols/ssh.py
    "SSH",
    "CollectObj",
    "RemoteConfig",
    # tools/ansi.py
    "AnsiBackground",
    "AnsiColor",
    "AnsiReset",
    "AnsiStyle",
    # tools/record.py
    "CmdRecord",
    # tools/timestamp.py
    "Timestamp",
    # this file
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
