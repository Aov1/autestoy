import pytest

from autestoy.protocols.ssh import SSH, RemoteConfig


@pytest.fixture(scope="session")
def remote():
    return RemoteConfig(
        user="u0_a210",
        ip="192.168.0.32",
        password="0402",
        port=8022,
    ).set_name("HUAWEI MATEPAD 12.2")


@pytest.fixture(scope="session")
def ssh(remote: RemoteConfig):
    return SSH(remote, timeout=5)
