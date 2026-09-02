"""Komunikasi serial sederhana untuk Arduino, ESP32, dan board sejenis."""

from __future__ import annotations

import time
from typing import Any


class Serial:
    """Serial dengan pencarian port otomatis dan reconnect ringan."""

    KEYWORDS = (
        "arduino",
        "ch340",
        "ch341",
        "cp210",
        "ft232",
        "wemos",
        "d1 mini",
        "esp8266",
        "esp32",
    )

    def __init__(
        self,
        port: str | None = None,
        *,
        baud: int = 9600,
        timeout: float = 1.0,
        reconnect_after: float = 5.0,
        newline: bool = False,
        connect: bool = True,
    ) -> None:
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.reconnect_after = reconnect_after
        self.newline = newline
        self.connection: Any | None = None
        self.last_connect_attempt = 0.0
        if connect:
            self.connect()

    @staticmethod
    def _modules():
        try:
            import serial
            import serial.tools.list_ports
        except ImportError as exc:
            raise ImportError(
                "PySerial belum terpasang. Jalankan: pip install pyserial"
            ) from exc
        return serial, serial.tools.list_ports

    @classmethod
    def auto(cls, *, baud: int = 9600, **kwargs) -> "Serial":
        return cls(None, baud=baud, **kwargs)

    @property
    def connected(self) -> bool:
        return bool(self.connection is not None and self.connection.is_open)

    @classmethod
    def find_port(cls) -> str | None:
        _, list_ports = cls._modules()
        ports = list(list_ports.comports())
        unix_keys = (
            "ttyUSB",
            "ttyACM",
            "usbserial",
            "usbmodem",
        )

        for port in ports:
            if any(key in port.device for key in unix_keys):
                return port.device
        for port in ports:
            info = f"{port.description} {port.manufacturer or ''} {port.hwid}".lower()
            if any(keyword in info for keyword in cls.KEYWORDS):
                return port.device
        return ports[0].device if len(ports) == 1 else None

    def connect(self) -> bool:
        serial, _ = self._modules()
        self.last_connect_attempt = time.monotonic()
        port = self.port or self.find_port()
        if port is None:
            return False
        try:
            self.connection = serial.Serial(port, self.baud, timeout=self.timeout)
            self.port = port
            time.sleep(2.0)
            self.connection.reset_input_buffer()
            self.connection.reset_output_buffer()
            return True
        except (serial.SerialException, OSError):
            self.connection = None
            return False

    def reconnect(self) -> bool:
        if self.connected:
            return True
        if time.monotonic() - self.last_connect_attempt < self.reconnect_after:
            return False
        return self.connect()

    def send(self, value: str | int | bytes) -> bool:
        if not self.connected and not self.reconnect():
            return False
        data = value if isinstance(value, bytes) else str(value).encode()
        if self.newline and not data.endswith(b"\n"):
            data += b"\n"
        try:
            self.connection.write(data)
            return True
        except Exception as exc:
            # PySerial tidak selalu tersedia saat dokumentasi di-build, sehingga
            # objek error spesifik tidak dirujuk di sini.
            self.close()
            is_serial_error = exc.__class__.__module__.startswith("serial")
            if is_serial_error or isinstance(exc, OSError):
                return False
            raise

    def read(self) -> str | None:
        if not self.connected or not self.connection.in_waiting:
            return None
        return self.connection.readline().decode(errors="ignore").strip() or None

    def close(self) -> None:
        if self.connection is not None:
            try:
                self.connection.close()
            finally:
                self.connection = None

    def __enter__(self) -> "Serial":
        if not self.connected:
            self.connect()
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
