"""
生成obsidian格式的导出文件相关工具（markdown + mermaid）
"""

from __future__ import annotations

import inspect
import os

from autestoy.tools.record import CmdRecord

from ..protocols.ssh import SFTP, SSH, Channel

# from ..tools.ansi import remove_ansi
from ..tools.local import Local

# from .baseinfo import get_script_dir, get_script_name
from .collect import CollectObj
from .term import Term


class MarkdownExporter:
    def __init__(self, output_path: str | None = None) -> None:
        self.output_path = (
            output_path if output_path else os.path.abspath(inspect.stack()[1].filename)
        )
        self.file_name = os.path.basename(inspect.stack()[1].filename).replace(
            ".py", ".md"
        )
        self.cmd_records = []

    def _get_cmd_records(self):
        for each in CollectObj:
            if isinstance(each[1], SSH):
                self.cmd_records += each[1].cmds
            elif isinstance(each[1], Channel):
                self.cmd_records += each[1].cmds
            elif isinstance(each[1], SFTP):
                self.cmd_records += each[1].cmds
            elif isinstance(each[1], Local):
                self.cmd_records += each[1].cmds

    def _sort_cmd_records(self):
        self.cmd_records.sort(key=lambda x: x.start_time)

    def save(self):
        self._get_cmd_records()
        self._sort_cmd_records()
        with open(self.output_path + self.file_name, "w") as f:
            f.write("```bash\n")
            for cmd in self.cmd_records:
                cmd: CmdRecord[str]
                tmp = f"[{cmd.start_time - Term.time_base:.3f}] {cmd.get_fmt_prompt(False)}"
                # tmp = tmp.replace("[", "\\[").replace("]", "\\]")
                f.write(tmp + "\n")
                for e in cmd.result:
                    f.write(f"[{e[0] - Term.time_base:.3f}] {str(e[1].get())}\n")
            f.write("```")


class ObsidianExporter(MarkdownExporter):
    def __init__(self, output_path: str | None = None) -> None:
        super().__init__(output_path)
