from autestoy.tools.ansi import remove_ansi, remove_ansi_bytes


def test_remove_ansi_bytes():
    res = remove_ansi_bytes(b"\x1b[?2004h\x1b[0;32m~\x1b[0m \x1b[0;97m$\x1b[0m ")
    assert res == b"~ $ "


def test_remove_ansi():
    res = remove_ansi("\x1b[?2004h\x1b[0;32m~\x1b[0m \x1b[0;97m$\x1b[0m ")
    assert res == "~ $ "
