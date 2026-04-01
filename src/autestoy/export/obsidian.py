"""
生成obsidian格式的导出文件相关工具（markdown + mermaid）
"""

import inspect
import os


class ObsidianExporter:
    def __init__(self, output_path: str | None = None) -> None:
        self.output_path = (
            output_path if output_path else os.path.abspath(inspect.stack()[1].filename)
        )

        print(f"Output path: {self.output_path}")
