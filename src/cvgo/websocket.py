"""Optional WebSocket connectivity for real-time robotics dashboards."""

from __future__ import annotations

import json
import time
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock, RLock
from typing import Any

from ._validation import boolean, non_negative_number, positive_number


class WebSocketClient:
    """WebSocket client with JSON messages, reconnect, and async sending."""

    def __init__(
        self,
        url: str,
        *,
        timeout: float = 10.0,
        reconnect_after: float = 5.0,
        connect: bool = False,
    ) -> None:
        if not isinstance(url, str) or not url.strip():
            raise ValueError("url must be a non-empty string")
        timeout = positive_number("timeout", timeout)
        reconnect_after = non_negative_number("reconnect_after", reconnect_after)
        connect = boolean("connect", connect)
        self.url = url
        self.timeout = float(timeout)
        self.reconnect_after = float(reconnect_after)
        self.connection: Any | None = None
        self.last_connect_attempt = 0.0
        self.last_error: str | None = None
        self._lock = RLock()
        self._executor_lock = Lock()
        self._executor: ThreadPoolExecutor | None = None
        self._closed = False
        if connect:
            self.connect()

    @staticmethod
    def _module():
        try:
            import websocket
        except ImportError as exc:
            raise ImportError(
                "websocket-client is not installed. Run: pip install cvgo[websocket]"
            ) from exc
        return websocket

    @property
    def connected(self) -> bool:
        return self.connection is not None

    def connect(self) -> bool:
        with self._lock:
            self._ensure_open()
            if self.connected:
                return True
            websocket = self._module()
            self.last_connect_attempt = time.monotonic()
            try:
                self.connection = websocket.create_connection(self.url, timeout=self.timeout)
                self.last_error = None
                return True
            except Exception as exc:
                self.last_error = str(exc)
                self.connection = None
                return False

    def reconnect(self) -> bool:
        with self._lock:
            if self.connected:
                return True
            if time.monotonic() - self.last_connect_attempt < self.reconnect_after:
                return False
            return self.connect()

    @staticmethod
    def _payload(value: Any) -> str | bytes:
        if isinstance(value, (str, bytes)):
            return value
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)

    def send(self, value: Any) -> bool:
        with self._lock:
            self._ensure_open()
            if not self.connected and not self.reconnect():
                return False
            try:
                self.connection.send(self._payload(value))
                return True
            except Exception as exc:
                self.last_error = str(exc)
                self.connection = None
                return False

    def send_async(self, value: Any) -> Future[bool]:
        with self._executor_lock:
            if self._executor is None:
                self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cvgo-websocket")
            return self._executor.submit(self.send, value)

    def receive(self) -> Any | None:
        with self._lock:
            self._ensure_open()
            if not self.connected and not self.reconnect():
                return None
            try:
                value = self.connection.recv()
                if isinstance(value, bytes):
                    value = value.decode(errors="replace")
                try:
                    return json.loads(value)
                except (TypeError, ValueError):
                    return value
            except Exception as exc:
                self.last_error = str(exc)
                self.connection = None
                return None

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("WebSocketClient is closed")

    def close(self, *, wait: bool = True) -> None:
        with self._executor_lock:
            executor = self._executor
            self._executor = None
        if executor is not None:
            executor.shutdown(wait=wait, cancel_futures=not wait)
        with self._lock:
            if self.connection is not None:
                self.connection.close()
                self.connection = None
            self._closed = True

    def __enter__(self) -> "WebSocketClient":
        self.connect()
        return self

    def __exit__(self, *_exc) -> None:
        self.close()