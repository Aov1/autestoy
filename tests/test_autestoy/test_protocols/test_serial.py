# from conftest import uart

import pytest

from autestoy.protocols.serial import Serial, SerialConfig, SerialShell


def test_SerialShell_init(uart: SerialShell):
    uart.shell_run("ifconfig")
    uart.shell_run_sudo("dmesg | tail -10", "kickpi")
    uart.shell_run_sudo("dmesg | tail -10 >> log.txt", "kickpi")
    uart.send(b"cat log.txt\n")
    buf, res = uart.recv_until(b"450005")
    print(f"{buf = }\n{res = }")
    uart.shell_run("rm log.txt")
