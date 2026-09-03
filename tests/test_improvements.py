"""Regression tests untuk peningkatan CVGO 0.2.1."""

import hashlib
import io
import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

import cvgo as go
import cvgo.models as model_module
from cvgo.__main__ import main


class FakeFaceDetectionModel:
    def __init__(self, result):
        self.result = result
        self.closed = False

    def process(self, _frame):
        return self.result

    def close(self):
        self.closed = True


class TestFastFaceDetector(unittest.TestCase):
    def test_fast_engine_is_default_and_returns_boxes(self):
        relative = SimpleNamespace(
            xmin=0.1,
            ymin=0.2,
            width=0.5,
            height=0.5,
        )
        detection = SimpleNamespace(
            location_data=SimpleNamespace(relative_bounding_box=relative),
            score=[0.91],
        )
        result = SimpleNamespace(detections=[detection])
        model = FakeFaceDetectionModel(result)
        factory = Mock(return_value=model)
        fake_mp = SimpleNamespace(
            solutions=SimpleNamespace(
                face_detection=SimpleNamespace(FaceDetection=factory),
            )
        )
        fake_cv2 = SimpleNamespace(
            COLOR_BGR2RGB=1,
            cvtColor=lambda frame, _code: frame.copy(),
        )

        with patch.dict(
            sys.modules,
            {"mediapipe": fake_mp, "cv2": fake_cv2},
        ):
            detector = go.FaceDetector(padding=10)
            boxes = detector.detect(np.zeros((100, 200, 3), dtype=np.uint8))
            detector.close()

        self.assertEqual(detector.engine, "fast")
        self.assertEqual(boxes[0].xyxy, (10, 10, 130, 80))
        self.assertAlmostEqual(boxes[0].confidence, 0.91)
        self.assertIs(detector.raw_result, result)
        self.assertTrue(model.closed)

    def test_mesh_options_keep_legacy_engine(self):
        landmarks = Mock()
        landmarks.model = object()

        with patch("cvgo.face.FaceLandmarks", return_value=landmarks):
            detector = go.FaceDetector(refine=True)
            detector.close()

        self.assertEqual(detector.engine, "mesh")
        landmarks.close.assert_called_once()

    def test_fast_engine_rejects_mesh_only_options(self):
        with self.assertRaisesRegex(ValueError, "engine='mesh'"):
            go.FaceDetector(engine="fast", refine=True)


class TestModelIntegrity(unittest.TestCase):
    def test_corrupt_cache_is_replaced_using_sha256(self):
        good = b"\x00\x00\x00\x00TFL3" + b"g" * 2048
        corrupt = b"\x00\x00\x00\x00TFL3" + b"x" * 2048
        info = replace(
            model_module.MODELS["object_detection"],
            sha256=hashlib.sha256(good).hexdigest(),
        )

        with tempfile.TemporaryDirectory() as directory, patch.dict(
            model_module.MODELS,
            {"object_detection": info},
        ):
            path = go.model_path("object_detection", directory=directory)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(corrupt)

            with patch(
                "cvgo.models.urllib.request.urlopen",
                return_value=io.BytesIO(good),
            ) as urlopen:
                result = go.download_model(
                    "object_detection",
                    directory=directory,
                )

            self.assertEqual(result.read_bytes(), good)
            urlopen.assert_called_once()
            request = urlopen.call_args.args[0]
            self.assertEqual(request.get_header("User-agent"), "CVGO/0.2.1")


class TestAsyncOutput(unittest.TestCase):
    def test_telegram_async_message_and_close(self):
        response = json.dumps(
            {"ok": True, "result": {"message_id": 1}}
        ).encode()

        with patch(
            "cvgo.telegram.urllib.request.urlopen",
            return_value=io.BytesIO(response),
        ) as urlopen:
            telegram = go.Telegram("123:token", "456", cooldown=0)
            future = telegram.send_message_async("CVGO aktif")
            self.assertTrue(future.result(timeout=1))
            telegram.close()

        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("User-agent"), "CVGO/0.2.1")
        with self.assertRaisesRegex(RuntimeError, "ditutup"):
            telegram.send_message_async("terlambat")

    def test_telegram_copies_frame_before_queueing(self):
        telegram = go.Telegram("123:token", "456", cooldown=0)
        telegram.send_photo = Mock(return_value=True)
        frame = np.zeros((2, 2, 3), dtype=np.uint8)

        future = telegram.send_photo_async(frame, "Deteksi")
        self.assertTrue(future.result(timeout=1))
        telegram.close()

        queued_frame = telegram.send_photo.call_args.args[0]
        self.assertIsNot(queued_frame, frame)
        self.assertTrue(np.array_equal(queued_frame, frame))

    def test_serial_async_send(self):
        connection = SimpleNamespace(
            is_open=True,
            write=Mock(),
            close=Mock(),
        )
        serial = go.Serial(connect=False, settle_time=0)
        serial.connection = connection

        future = serial.send_async("A")
        self.assertTrue(future.result(timeout=1))
        serial.close()

        connection.write.assert_called_once_with(b"A")
        connection.close.assert_called_once()


class TestDiagnosticsAndValidation(unittest.TestCase):
    def test_version_has_one_source_of_truth(self):
        root = Path(__file__).parents[1]
        config = (root / "pyproject.toml").read_text(encoding="utf-8")

        self.assertEqual(go.__version__, "0.2.1")
        self.assertIn('dynamic = ["version"]', config)
        self.assertIn('attr = "cvgo._version.__version__"', config)

    def test_system_info_reports_expected_dependencies(self):
        versions = {
            "numpy": "1.26.4",
            "opencv-contrib-python": "4.11.0.86",
            "mediapipe": "0.10.21",
            "pyserial": "3.5",
        }

        with patch(
            "cvgo.diagnostics.metadata.version",
            side_effect=lambda name: versions[name],
        ):
            info = go.system_info()

        self.assertEqual(info["cvgo"], "0.2.1")
        self.assertTrue(all(
            item["ok"] for item in info["dependencies"].values()
        ))

    def test_cli_json_can_include_camera_check(self):
        info = {
            "cvgo": "0.2.1",
            "python": "3.11.9",
            "python_supported": True,
            "implementation": "CPython",
            "system": "Linux",
            "release": "test",
            "machine": "aarch64",
            "dependencies": {
                "numpy": {"ok": True},
            },
        }
        camera = {"source": 4, "ok": True, "width": 640, "height": 480}

        with patch("cvgo.__main__.system_info", return_value=info), patch(
            "cvgo.__main__.check_camera",
            return_value=camera,
        ), patch("sys.stdout", new_callable=io.StringIO) as output:
            code = main(["check", "--camera", "4", "--json"])

        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["camera"], camera)

    def test_common_invalid_parameters_fail_early(self):
        invalid_calls = (
            lambda: go.Camera(width=0),
            lambda: go.Camera(backend=True),
            lambda: go.Timer(-1),
            lambda: go.Alarm(repeat=0),
            lambda: go.Serial(connect=False, settle_time=-1),
            lambda: go.FaceDetector(max_faces=0),
        )

        for call in invalid_calls:
            with self.subTest(call=call):
                with self.assertRaises((TypeError, ValueError)):
                    call()


if __name__ == "__main__":
    unittest.main()
