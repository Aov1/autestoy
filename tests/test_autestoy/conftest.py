import pytest

from autestoy import SSH, AnsiBackground, AnsiColor, AnsiReset, AnsiStyle, RemoteConfig
from autestoy.protocols.serial import Serial, SerialConfig
from autestoy.protocols.telnet import Telnet, TelnetConfig

# from autestoy.protocols.ssh import SSH, RemoteConfig


@pytest.fixture(scope="session")
def remote():
    return RemoteConfig(
        user="kickpi",
        # user="u0_a210",
        ip="192.168.4.191",
        # ip="192.168.18.6",
        # ip="192.168.4.32",
        password="kickpi",
        # password="0402",
        # port=8022,
    ).set_name("HUAWEI")


@pytest.fixture(scope="session")
def uart_conf():
    return SerialConfig("/dev/ttyUSB0", 115200)


@pytest.fixture(scope="session")
def telnet_conf():
    return TelnetConfig(
        name="kickpi",
        host="192.168.4.191",
        port=2323,
        user="kickpi",
        password="kickpi",
    )


@pytest.fixture(scope="session")
def ssh(remote: RemoteConfig):
    ssh_t = SSH(remote, timeout=60)
    assert ssh_t.is_connected(), "ssh connect failed"
    yield ssh_t
    for e in ssh_t.channels:
        e.shell.close()
    ssh_t.remote.close()
    print("ssh closed")


@pytest.fixture(scope="session")
def uart(uart_conf: SerialConfig):
    uart = Serial("UartT", uart_conf, shell_mode=True)
    yield uart
    uart.com.close()
    assert uart.com.closed
    print("Uart Colsed")


@pytest.fixture(scope="session")
def telnet(telnet_conf: TelnetConfig):
    tel = Telnet(telnet_conf)
    yield tel
    tel.tel3.close()
    assert tel.tel3._closed
    print("Telnet Closed")


# @pytest.fixture(scope="session")
def log(title: str):
    style = AnsiColor.black + AnsiBackground.yellow + AnsiStyle.bold
    print(f"{style}{title}{AnsiReset}")
