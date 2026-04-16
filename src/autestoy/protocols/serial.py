"""串口协议"""

import serial


class Serial:
    def __init__(
        self,
        name: str,
        port: str,
        baudrate: int = 115200,
        timeout: float = 0,
        **kwargs_inster_serial_init,
    ) -> None:
        self.name: str = name
        self.serial: serial.Serial = serial.Serial(
            port, baudrate, timeout=timeout, **kwargs_inster_serial_init
        )

    pass
