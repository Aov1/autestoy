import time

from .export.term import Term, TermStyle
from .protocols.ssh import SSH, Channel_collect, RemoteConfig, SFTP_collect, SSH_collect
from .tools.record import CmdRecord
from .tools.timestamp import Timestamp

# from .tools.ansi import remove_ansi,remove_ansi_bytes
__all__ = [
    "SSH",
    "RemoteConfig",
    "CmdRecord",
    "Timestamp",
    "Channel_collect",
    "SSH_collect",
    "SFTP_collect",
    "Term",
    "TermStyle",
    "TimeBase",
]


TimeBase = time.time()
Term.set_time_base(TimeBase)
