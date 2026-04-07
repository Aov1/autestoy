from conftest import log

from autestoy.export.obsidian import ObsidianExporter


def test_ObsidianExporter():
    log("test_ObsidianExporter")
    exporter = ObsidianExporter()
    print(exporter.file_name)
    print(exporter.output_path)
    assert exporter is not None
