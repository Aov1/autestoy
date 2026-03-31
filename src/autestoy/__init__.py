import time

from .export.collect import Channel_record, SSH_record
from .export.term import Term, TermStyle
from .protocols.ssh import SSH, RemoteConfig
from .tools.result import CmdRecord
from .tools.timestamp import Timestamp

# from .tools.ansi import remove_ansi,remove_ansi_bytes
__all__ = [
    "SSH",
    "RemoteConfig",
    "CmdRecord",
    "Timestamp",
    "Channel_record",
    "SSH_record",
    "Term",
    "TermStyle",
    "TimeBase",
]


TimeBase = time.time()
Term.set_time_base(TimeBase)
