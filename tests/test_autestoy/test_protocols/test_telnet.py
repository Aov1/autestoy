from autestoy.protocols.telnet import TelnetConfig, TelnetShell
from autestoy.tools.ansi import remove_ansi


def test_telnet_init(telnet: TelnetShell):
    telnet.shell_run("ifconfig")
    telnet.shell_run("ls")
    telnet.shell_run("pwd")

    assert telnet.prompt is not None
