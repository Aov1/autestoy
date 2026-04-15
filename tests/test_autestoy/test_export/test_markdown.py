from conftest import log

from autestoy.export.markdown import MarkdownExporter


def test_ObsidianExporter():
    log("test_ObsidianExporter")
    exporter = MarkdownExporter()
    print(exporter.file_name)
    print(exporter.output_path)
    assert exporter is not None
