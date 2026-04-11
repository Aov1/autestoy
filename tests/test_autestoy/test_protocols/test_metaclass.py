from conftest import log

from autestoy.protocols.metaclass import DUTConfiguratorBase
from autestoy.protocols.ssh import SSH


def test_dut_configurator_base(ssh):
    log("test_dut_configurator_base")
    dut = DUTConfiguratorBase(ssh)
    dut[SSH][0].exec_run("ls")

    dut.HUAWEI.exec_run("ls") if isinstance(dut.HUAWEI, SSH) else None
    dut.get_from_name(SSH, "HUAWEI").exec_run("ls")
