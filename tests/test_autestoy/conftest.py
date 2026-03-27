import pytest

from autestoy.protocols.ssh import RemoteConfig


@pytest.fixture(scope="session")
def remote():
    return RemoteConfig(
        user="u0_a210",
        ip="192.168.18.6",
        password="0402",
        port=8022,
    ).set_name("HUAWEI MATEPAD 12.2")
