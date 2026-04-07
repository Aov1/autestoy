from __future__ import annotations

import getpass
import subprocess as sp
import sys
from typing import Any

from ..export.collect import CollectObj, CollectType, collect
from ..export.term import Term
from .record import CmdRecord, MetaRecord
from .timestamp import Timestamp


@collect(CollectType.Local, CollectObj)
class Local:
    def __init__(self):
        self.name = str(sys.platform)
        self.meta_record = MetaRecord[str](
            type="Local",
            name=self.name,
            info=getpass.getuser(),
        )
        self.start_time = Timestamp()
        self.cmds: list[CmdRecord] = []

    def run(self, cmd: str) -> CmdRecord[str]:  # TODO
        record = CmdRecord[str](
            cmd=cmd, prompt=f"[Local {self.name}][{self.meta_record.info}]$"
        )
        Term.putsln(record.get_fmt_prompt())
        result = sp.run(cmd, shell=True, capture_output=True)
        out = result.stdout.decode().strip()
        if out != "":
            record.result_append(out)
            Term.putsln(out)
        err = result.stderr.decode().strip()
        if err != "":
            record.result_append(err)
            Term.putsln(err, set_font_color="red")
        self.cmds.append(record)
        return record
