# from conftest import uart

from autestoy.protocols.serial import Serial, SerialConfig


def test_serial_init(uart: Serial):
    uart.shell_mode(True)
    