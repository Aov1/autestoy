from autestoy.protocols.telnet import Telnet, TelnetConfig
from autestoy.tools.ansi import remove_ansi


def test_telnet_init(telnet: Telnet):
    telnet.tel3.write("pwd\n")
    res = telnet.tel3.read_some()
    print(remove_ansi(res))
    assert telnet.prompt is not None
