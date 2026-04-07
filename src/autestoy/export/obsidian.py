"""
生成obsidian格式的导出文件相关工具（markdown + mermaid）
"""

from .baseinfo import get_script_dir, get_script_name


class ObsidianExporter:
    def __init__(self, output_path: str | None = None) -> None:
        self.output_path = output_path if output_path else get_script_dir()
        self.file_name = get_script_name().replace(".py", ".md")

        # tmp = (
        #     output_path if output_path else os.path.abspath(inspect.stack()[1].filename)
        # )
        # self.platfrom = sys.platform
        # if self.platfrom == "win32":
        #     self.full_path = tmp.replace("\\", "/")
        # else:
        #     self.full_path = tmp

        # self.output_path = os.path.dirname(self.full_path)
        # self.file_name = os.path.basename(self.full_path)
