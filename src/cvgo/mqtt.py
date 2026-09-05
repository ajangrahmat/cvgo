"""Optional MQTT connectivity for robotics and device messaging."""

from __future__ import annotations

import json
import time
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock, RLock
from typing import Any, Callable

from ._validation import boolean, non_negative_number, positive_int


class MqttClient:
    """MQTT client with JSON payloads, reconnect, and async publishing."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 1883,
        *,
        client_id: str = "",
        username: str | None = None,
        password: str | None = None,
        keepalive: int = 60,
        reconnect_after: float = 5.0,
        tls: bool = False,
        connect: bool = False,
    ) -> None:
        if not isinstance(host, str) or not host.strip():
            raise ValueError("host must be a non-empty string")
        if not isinstance(client_id, str):
            raise TypeError("client_id must be a string")
        port = positive_int("port", port)
        keepalive = positive_int("keepalive", keepalive)
        reconnect_after = non_negative_number("reconnect_after", reconnect_after)
        tls = boolean("tls", tls)
        connect = boolean("connect", connect)
        self.host = host
        self.port = port
        self.client_id = client_id
        self.username = username
        self.password = password
        self.keepalive = keepalive
        self.reconnect_after = float(reconnect_after)
        self.tls = tls
        self.client: Any | None = None
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
            import paho.mqtt.client as mqtt
        except ImportError as exc:
            raise ImportError(
                "paho-mqtt is not installed. Run: pip install cvgo[mqtt]"
            ) from exc
        return mqtt

    @property
    def connected(self) -> bool:
        return bool(self.client is not None and self.client.is_connected())

    def connect(self) -> bool:
        with self._lock:
            self._ensure_open()
            if self.connected:
                return True
            mqtt = self._module()
            self.last_connect_attempt = time.monotonic()
            try:
                self.client = mqtt.Client(client_id=self.client_id)
                if self.username is not None:
                    self.client.username_pw_set(self.username, self.password)
                if self.tls:
                    self.client.tls_set()
                self.client.connect(self.host, self.port, self.keepalive)
                self.client.loop_start()
                self.last_error = None
                return True
            except Exception as exc:
                self.last_error = str(exc)
                self.client = None
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

    def publish(self, topic: str, value: Any, *, qos: int = 0, retain: bool = False) -> bool:
        with self._lock:
            self._ensure_open()
            if not isinstance(topic, str) or not topic:
                raise ValueError("topic must be a non-empty string")
            if not self.connected and not self.reconnect():
                return False
            try:
                result = self.client.publish(topic, self._payload(value), qos=qos, retain=retain)
                return result.rc == 0
            except Exception as exc:
                self.last_error = str(exc)
                return False

    def publish_async(self, topic: str, value: Any, *, qos: int = 0, retain: bool = False) -> Future[bool]:
        with self._executor_lock:
            if self._executor is None:
                self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cvgo-mqtt")
            return self._executor.submit(self.publish, topic, value, qos=qos, retain=retain)

    def subscribe(self, topic: str, callback: Callable[[str, Any], None], *, qos: int = 0) -> bool:
        with self._lock:
            self._ensure_open()
            if not callable(callback):
                raise TypeError("callback must be callable")
            if not self.connected and not self.reconnect():
                return False

            def on_message(_client, _userdata, message):
                payload = message.payload
                try:
                    payload = json.loads(payload.decode() if isinstance(payload, bytes) else payload)
                except (TypeError, ValueError):
                    if isinstance(payload, bytes):
                        payload = payload.decode(errors="replace")
                callback(message.topic, payload)

            self.client.message_callback_add(topic, on_message)
            result = self.client.subscribe(topic, qos=qos)
            return result[0] == 0 if isinstance(result, tuple) else result.rc == 0

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("MqttClient is closed")

    def close(self, *, wait: bool = True) -> None:
        with self._executor_lock:
            executor = self._executor
            self._executor = None
        if executor is not None:
            executor.shutdown(wait=wait, cancel_futures=not wait)
        with self._lock:
            if self.client is not None:
                self.client.loop_stop()
                self.client.disconnect()
                self.client = None
            self._closed = True

    def __enter__(self) -> "MqttClient":
        self.connect()
        return self

    def __exit__(self, *_exc) -> None:
        self.close()