from __future__ import annotations

import getpass
import os
import subprocess as sp
import sys

from autestoy.export.messageio import Message, MessageBus, MessageSource

# from ..export.collect import CollectObj, CollectType, collect
from ..export.term import Term
from ..tools.record import CmdRecord, CmdRecording
from ..tools.timestamp import Timestamp


# @collect(CollectType.Local, CollectObj)
class Local:
    def __init__(self):
        self.name = str(sys.platform)
        self.user = getpass.getuser()
        # self.meta_record = MetaRecord[str](
        #     type="Local",
        #     name=self.name,
        #     info=getpass.getuser(),
        # )
        self.start_time = Timestamp()
        self.cmds: list[CmdRecord] = []

    def run(self, cmd: str) -> CmdRecord[str]:  # TODO
        record = CmdRecord[str](
            cmd=cmd,
            prompt=f"{os.getcwd()} $",
            source=MessageSource.LOCAL,
            id_key=self.name,
            name=self.name,
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        res = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE, text=True)
        if res.stdout is None or res.stderr is None:
            raise ValueError("stdout or stderr is None")
        while True:
            line = res.stdout.readline().strip()
            if line == "" and res.poll() is not None:
                break
            if line != "":
                record.result.append(Term.putsln(line))
            err = res.stderr.readline().strip()
            if err != "":
                record.result.append(Term.putsln(err, set_font_color="red"))
        record.exit_code = res.poll()
        return record


class LocalPopen:
    def __init__(self):
        sp.Popen
