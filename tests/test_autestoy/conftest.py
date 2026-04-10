import pytest

from autestoy import SSH, AnsiBackground, AnsiColor, AnsiReset, AnsiStyle, RemoteConfig

# from autestoy.protocols.ssh import SSH, RemoteConfig


@pytest.fixture(scope="session")
def remote():
    return RemoteConfig(
        user="u0_a210",
        ip="192.168.18.6",
        # ip="192.168.4.32",
        password="0402",
        port=8022,
    ).set_name("HUAWEI MATEPAD 12.2")


@pytest.fixture(scope="session")
def ssh(remote: RemoteConfig):
    ssh_t = SSH(remote, timeout=60)
    assert ssh_t.is_connected(), "ssh connect failed"
    yield ssh_t
    for e in ssh_t.channels:
        e.shell.close()
    ssh_t.remote.close()
    print("ssh closed")


# @pytest.fixture(scope="session")
def log(title: str):
    style = AnsiColor.black + AnsiBackground.yellow + AnsiStyle.bold
    print(f"{style}{title}{AnsiReset}")
