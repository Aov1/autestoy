from conftest import log

from autestoy import Bits, ulog
from autestoy.protocols.metaclass import DUTConfiguratorBase
from autestoy.protocols.ssh import SSH


class Test(DUTConfiguratorBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def write_register(
        self, address: Bits | str | int, value: Bits | str | int
    ) -> bool:
        if isinstance(address, (str, int)):
            address = Bits(address, 32)
        if isinstance(value, (str, int)):
            value = Bits(value, 32)
        res = self[SSH][0].exec_run(f"echo {address} {value}")

        return res.exit_code == 0


def test_dut_configurator_base(ssh):
    log("test_dut_configurator_base")
    dut = DUTConfiguratorBase(ssh)
    dut.add_dynamic_method("read_register", read_register)

    dut[SSH][0].exec_run("ls")

    dut.get_from_name(SSH, "HUAWEI").exec_run("ls")

    val = dut.read_register(0x12345678)
    ulog(f"{val = }")

    dut = Test(ssh)
    dut.write_register(0x12345678, 0xDEADBEEF)


def read_register(self: DUTConfiguratorBase, address: Bits | str | int) -> Bits:
    if isinstance(address, (str, int)):
        address = Bits(address, 32)
    record = self[SSH][0].exec_run(f"echo {address}")
    if res := record.search(r"0x([0-9a-fA-F]+)"):
        return Bits(int(res.group(1), 16), address.width)
    return Bits(0, address.width)
