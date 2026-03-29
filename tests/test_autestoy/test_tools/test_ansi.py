from autestoy.tools.ansi import (
    AnsiBackground,
    AnsiColor,
    AnsiReset,
    remove_ansi,
    remove_ansi_bytes,
)


def test_remove_ansi_bytes():
    res = remove_ansi_bytes(b"\x1b[?2004h\x1b[0;32m~\x1b[0m \x1b[0;97m$\x1b[0m ")
    assert res == b"~ $ "


def test_remove_ansi():
    res = remove_ansi("\x1b[?2004h\x1b[0;32m~\x1b[0m \x1b[0;97m$\x1b[0m ")
    assert res == "~ $ "


def test_Ansi():
    s = f"{AnsiColor.red}Hello{AnsiReset}"
    print(s)
    assert s == "\x1b[31mHello\x1b[0m"

    s = f"{AnsiBackground.light_blue}{AnsiColor.green}World{AnsiReset}"
    print(s)
    assert s == "\x1b[104m\x1b[32mWorld\x1b[0m"
