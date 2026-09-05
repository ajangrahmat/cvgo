"""Tests for optional robotics connectivity clients."""

import json
import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

import cvgo as go


class FakeMqttClient:
    def __init__(self, **_kwargs):
        self.connected = False
        self.callback = None
        self.published = []

    def connect(self, *_args):
        self.connected = True

    def is_connected(self):
        return self.connected

    def loop_start(self):
        pass

    def loop_stop(self):
        pass

    def disconnect(self):
        self.connected = False

    def publish(self, topic, payload, **_kwargs):
        self.published.append((topic, payload))
        return SimpleNamespace(rc=0)

    def message_callback_add(self, _topic, callback):
        self.callback = callback

    def subscribe(self, _topic, **_kwargs):
        return (0, 1)


class FakeWebSocket:
    def __init__(self):
        self.sent = []
        self.received = '{"ok": true}'

    def send(self, value):
        self.sent.append(value)

    def recv(self):
        return self.received

    def close(self):
        pass


class TestMqttClient(unittest.TestCase):
    def test_publish_and_subscribe_json(self):
        fake = FakeMqttClient()
        mqtt_module = ModuleType("paho.mqtt.client")
        mqtt_module.Client = Mock(return_value=fake)
        mqtt_package = ModuleType("paho.mqtt")
        mqtt_package.client = mqtt_module
        paho_package = ModuleType("paho")
        paho_package.mqtt = mqtt_package
        callback = Mock()
        modules = {
            "paho": paho_package,
            "paho.mqtt": mqtt_package,
            "paho.mqtt.client": mqtt_module,
        }
        with patch.dict(sys.modules, modules):
            client = go.MqttClient(connect=True)
            self.assertTrue(client.publish("robot/state", {"ready": True}))
            self.assertEqual(fake.published[0], ("robot/state", '{"ready":true}'))
            self.assertTrue(client.subscribe("robot/command", callback))
            fake.callback(
                None,
                None,
                SimpleNamespace(
                    topic="robot/command",
                    payload=b'{"move":"forward"}',
                ),
            )
            client.close()

        callback.assert_called_once_with("robot/command", {"move": "forward"})


class TestWebSocketClient(unittest.TestCase):
    def test_send_and_receive_json(self):
        fake = FakeWebSocket()
        websocket_module = SimpleNamespace(create_connection=Mock(return_value=fake))
        with patch.dict(sys.modules, {"websocket": websocket_module}):
            client = go.WebSocketClient("ws://robot", connect=True)
            self.assertTrue(client.send({"command": "stop"}))
            self.assertEqual(json.loads(fake.sent[0]), {"command": "stop"})
            self.assertEqual(client.receive(), {"ok": True})
            client.close()


if __name__ == "__main__":
    unittest.main()