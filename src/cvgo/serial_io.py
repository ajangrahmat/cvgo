"""Komunikasi serial sederhana untuk Arduino, ESP32, dan board sejenis."""

from __future__ import annotations

import time
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock, RLock
from typing import Any

from ._validation import (
    boolean,
    non_negative_number,
    positive_int,
)


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
        settle_time: float = 2.0,
        newline: bool = False,
        connect: bool = True,
    ) -> None:
        baud = positive_int("baud", baud)
        timeout = non_negative_number("timeout", timeout)
        reconnect_after = non_negative_number(
            "reconnect_after",
            reconnect_after,
        )
        settle_time = non_negative_number("settle_time", settle_time)
        newline = boolean("newline", newline)
        connect = boolean("connect", connect)

        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.reconnect_after = reconnect_after
        self.settle_time = settle_time
        self.newline = newline
        self.connection: Any | None = None
        self.last_connect_attempt = 0.0
        self._io_lock = RLock()
        self._executor_lock = Lock()
        self._executor: ThreadPoolExecutor | None = None
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
        with self._io_lock:
            if self.connected:
                return True

            serial, _ = self._modules()
            self.last_connect_attempt = time.monotonic()
            port = self.port or self.find_port()
            if port is None:
                return False
            try:
                self.connection = serial.Serial(
                    port,
                    self.baud,
                    timeout=self.timeout,
                )
                self.port = port
                if self.settle_time:
                    time.sleep(self.settle_time)
                self.connection.reset_input_buffer()
                self.connection.reset_output_buffer()
                return True
            except (serial.SerialException, OSError):
                self._disconnect()
                return False

    def reconnect(self) -> bool:
        with self._io_lock:
            if self.connected:
                return True
            elapsed = time.monotonic() - self.last_connect_attempt
            if elapsed < self.reconnect_after:
                return False
            return self.connect()

    def send(self, value: str | int | bytes) -> bool:
        with self._io_lock:
            if not self.connected and not self.reconnect():
                return False
            data = value if isinstance(value, bytes) else str(value).encode()
            if self.newline and not data.endswith(b"\n"):
                data += b"\n"
            try:
                self.connection.write(data)
                return True
            except Exception as exc:
                # Objek error spesifik tidak dirujuk agar dokumentasi tetap bisa
                # di-build tanpa mengimpor PySerial.
                self._disconnect()
                is_serial_error = exc.__class__.__module__.startswith("serial")
                if is_serial_error or isinstance(exc, OSError):
                    return False
                raise

    def send_async(self, value: str | int | bytes) -> Future[bool]:
        """Antrekan pengiriman tanpa menahan loop kamera."""
        with self._executor_lock:
            if self._executor is None:
                self._executor = ThreadPoolExecutor(
                    max_workers=1,
                    thread_name_prefix="cvgo-serial",
                )
            return self._executor.submit(self.send, value)

    def read(self) -> str | None:
        with self._io_lock:
            if not self.connected or not self.connection.in_waiting:
                return None
            value = self.connection.readline().decode(errors="ignore").strip()
            return value or None

    def _disconnect(self) -> None:
        if self.connection is not None:
            try:
                self.connection.close()
            finally:
                self.connection = None

    def close(self, *, wait: bool = True) -> None:
        with self._executor_lock:
            executor = self._executor
            self._executor = None
        if executor is not None:
            executor.shutdown(wait=wait, cancel_futures=not wait)

        with self._io_lock:
            self._disconnect()

    def __enter__(self) -> "Serial":
        if not self.connected:
            self.connect()
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
