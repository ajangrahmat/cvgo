"""Pengujian fitur CVGO V1 yang tidak memerlukan kamera atau internet."""

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

import cvgo as go


class FakeOwner:
    def draw(self, *_args, **_kwargs):
        return None


def landmarks(count, *, visibility=None):
    points = []

    for index in range(count):
        point = SimpleNamespace(
            x=index / max(count - 1, 1),
            y=index / max(count - 1, 1),
            z=0.0,
        )
        if visibility is not None:
            point.visibility = visibility
        points.append(point)

    return SimpleNamespace(landmark=points)


class TestModelManager(unittest.TestCase):
    def test_download_and_reuse_tflite_model(self):
        payload = b"\x00\x00\x00\x00TFL3" + b"x" * 2048

        with tempfile.TemporaryDirectory() as directory:
            response = io.BytesIO(payload)

            with patch(
                "cvgo.models.urllib.request.urlopen",
                return_value=response,
            ) as urlopen:
                path = go.download_model(
                    "object_detection",
                    directory=directory,
                )

            self.assertEqual(path.read_bytes(), payload)
            self.assertEqual(urlopen.call_count, 1)

            with patch(
                "cvgo.models.urllib.request.urlopen"
            ) as second_urlopen:
                reused = go.download_model(
                    "object_detection",
                    directory=directory,
                )

            self.assertEqual(reused, path)
            second_urlopen.assert_not_called()

    def test_gesture_task_header(self):
        payload = b"PK\x03\x04" + b"x" * 2048

        with tempfile.TemporaryDirectory() as directory:
            with patch(
                "cvgo.models.urllib.request.urlopen",
                return_value=io.BytesIO(payload),
            ):
                path = go.download_model(
                    "gesture_recognizer",
                    directory=directory,
                )

            self.assertTrue(path.name.endswith(".task"))

    def test_custom_model_must_exist(self):
        missing = Path("model-yang-tidak-ada.tflite")

        with self.assertRaises(FileNotFoundError):
            go.ObjectDetector(missing)


class TestObjectResult(unittest.TestCase):
    def test_person_label_and_box(self):
        item = go.DetectedObject(
            raw=None,
            box=go.ObjectBox(10, 20, 30, 40),
            label="person",
            score=0.9,
            category_index=0,
        )

        self.assertTrue(item.is_person)
        self.assertEqual(item.box.xyxy, (10, 20, 40, 60))


class TestGestureResult(unittest.TestCase):
    def test_gesture_keeps_editable_hand_result(self):
        hand = go.Hand(
            landmarks(21),
            FakeOwner(),
            (640, 480),
            handedness="Right",
            confidence=0.95,
        )
        gesture = go.Gesture(
            hand,
            label="Victory",
            score=0.91,
        )

        self.assertTrue(gesture.recognized)
        self.assertEqual(gesture.hand[go.HandLandmark.WRIST].x, 0.0)


class TestSegmentationResult(unittest.TestCase):
    def test_apply_background_color(self):
        frame = np.full((2, 2, 3), 100, dtype=np.uint8)
        mask = np.array([[1.0, 0.0], [0.7, 0.2]])
        result = go.SegmentationResult(mask)

        output = result.apply(
            frame,
            background=(0, 0, 0),
            threshold=0.5,
        )

        self.assertTrue(np.array_equal(output[0, 0], (100, 100, 100)))
        self.assertTrue(np.array_equal(output[0, 1], (0, 0, 0)))


class TestHolisticResult(unittest.TestCase):
    def test_empty_result(self):
        result = go.HolisticResult(
            FakeOwner(),
            raw=None,
            face=None,
            pose=None,
            left_hand=None,
            right_hand=None,
            mask=None,
        )

        self.assertFalse(result.found)
        self.assertEqual(result.hands, [])


def telegram_response(result):
    payload = json.dumps({"ok": True, "result": result}).encode()
    return io.BytesIO(payload)


class TestTelegram(unittest.TestCase):
    def test_token_is_required(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError):
                go.Telegram()

    def test_find_latest_chat_id(self):
        updates = [
            {
                "message": {
                    "chat": {"id": -123456},
                }
            }
        ]

        with patch(
            "cvgo.telegram.urllib.request.urlopen",
            return_value=telegram_response(updates),
        ):
            telegram = go.Telegram("123:token")
            chat_id = telegram.find_chat_id()

        self.assertEqual(chat_id, "-123456")
        self.assertTrue(telegram.configured)

    def test_send_message_and_cooldown(self):
        with patch(
            "cvgo.telegram.urllib.request.urlopen",
            return_value=telegram_response({"message_id": 1}),
        ) as urlopen:
            with patch(
                "cvgo.telegram.time.monotonic",
                return_value=100.0,
            ):
                telegram = go.Telegram(
                    "123:token",
                    "456",
                    cooldown=30,
                )
                first = telegram.send_message("CVGO aktif")
                second = telegram.send_message("Jangan terkirim")

        self.assertTrue(first)
        self.assertFalse(second)
        self.assertEqual(urlopen.call_count, 1)
        request = urlopen.call_args.args[0]
        self.assertIn(b"chat_id=456", request.data)
        self.assertIn(b"text=CVGO+aktif", request.data)

    def test_send_photo_bytes_as_multipart(self):
        image = b"\xff\xd8gambar-jpeg\xff\xd9"

        with patch(
            "cvgo.telegram.urllib.request.urlopen",
            return_value=telegram_response({"message_id": 2}),
        ) as urlopen:
            telegram = go.Telegram(
                "123:token",
                "456",
                cooldown=0,
            )
            sent = telegram.send_photo(
                image,
                "Orang terdeteksi",
            )

        self.assertTrue(sent)
        request = urlopen.call_args.args[0]
        self.assertIn(b'name="photo"', request.data)
        self.assertIn(b"Orang terdeteksi", request.data)
        self.assertIn(image, request.data)
        self.assertIn("multipart/form-data", request.get_header("Content-type"))

    def test_send_opencv_frame_as_jpeg(self):
        encoded = SimpleNamespace(tobytes=lambda: b"frame-jpeg")
        fake_cv2 = SimpleNamespace(
            IMWRITE_JPEG_QUALITY=1,
            imencode=lambda *_args: (True, encoded),
        )

        with patch.dict(sys.modules, {"cv2": fake_cv2}):
            with patch(
                "cvgo.telegram.urllib.request.urlopen",
                return_value=telegram_response({"message_id": 3}),
            ):
                telegram = go.Telegram(
                    "123:token",
                    "456",
                    cooldown=0,
                )
                sent = telegram.send_photo(np.zeros((2, 2, 3)))

        self.assertTrue(sent)


class FakeOptions:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class FakeObjectModel:
    def __init__(self):
        self.closed = False
        self.timestamp = None

    def detect(self, _image):
        category = SimpleNamespace(
            category_name="person",
            display_name="",
            index=0,
            score=0.88,
        )
        box = SimpleNamespace(
            origin_x=10,
            origin_y=20,
            width=30,
            height=40,
        )
        detection = SimpleNamespace(
            categories=[category],
            bounding_box=box,
        )
        return SimpleNamespace(detections=[detection])

    def detect_for_video(self, image, timestamp):
        self.timestamp = timestamp
        return self.detect(image)

    def close(self):
        self.closed = True


class FakeObjectFactory:
    model = FakeObjectModel()
    options = None

    @classmethod
    def create_from_options(cls, options):
        cls.options = options
        return cls.model


class TestObjectDetectorFlow(unittest.TestCase):
    def test_task_result_becomes_cvgo_object(self):
        fake_mp = SimpleNamespace(
            tasks=SimpleNamespace(
                BaseOptions=FakeOptions,
                vision=SimpleNamespace(
                    ObjectDetectorOptions=FakeOptions,
                    ObjectDetector=FakeObjectFactory,
                    RunningMode=SimpleNamespace(
                        IMAGE="image",
                        VIDEO="video",
                    ),
                ),
            ),
            Image=lambda **kwargs: kwargs,
            ImageFormat=SimpleNamespace(SRGB="srgb"),
        )
        fake_cv2 = SimpleNamespace(
            COLOR_BGR2RGB=1,
            cvtColor=lambda frame, _code: frame,
        )

        with tempfile.NamedTemporaryFile(suffix=".tflite") as model_file:
            with patch.dict(
                sys.modules,
                {"mediapipe": fake_mp, "cv2": fake_cv2},
            ):
                detector = go.ObjectDetector(
                    model_file.name,
                    allow=["person"],
                )
                objects = detector.detect(np.zeros((10, 10, 3)))

        self.assertEqual(len(objects), 1)
        self.assertTrue(objects[0].is_person)
        self.assertEqual(objects[0].box.xyxy, (10, 20, 40, 60))
        self.assertEqual(FakeObjectFactory.options.running_mode, "video")
        self.assertIsInstance(FakeObjectFactory.model.timestamp, int)


class FakeGestureModel:
    def __init__(self):
        self.timestamp = None

    def recognize(self, _image):
        gesture = SimpleNamespace(
            category_name="Victory",
            score=0.92,
        )
        handedness = SimpleNamespace(
            category_name="Left",
            score=0.97,
        )
        points = landmarks(21).landmark
        return SimpleNamespace(
            gestures=[[gesture]],
            handedness=[[handedness]],
            hand_landmarks=[points],
            hand_world_landmarks=[points],
        )

    def recognize_for_video(self, image, timestamp):
        self.timestamp = timestamp
        return self.recognize(image)

    def close(self):
        return None


class FakeGestureFactory:
    model = FakeGestureModel()
    options = None

    @classmethod
    def create_from_options(cls, options):
        cls.options = options
        return cls.model


class TestGestureRecognizerFlow(unittest.TestCase):
    def test_task_result_becomes_editable_gesture(self):
        fake_mp = SimpleNamespace(
            tasks=SimpleNamespace(
                BaseOptions=FakeOptions,
                vision=SimpleNamespace(
                    GestureRecognizerOptions=FakeOptions,
                    GestureRecognizer=FakeGestureFactory,
                    RunningMode=SimpleNamespace(
                        IMAGE="image",
                        VIDEO="video",
                    ),
                ),
            ),
            Image=lambda **kwargs: kwargs,
            ImageFormat=SimpleNamespace(SRGB="srgb"),
        )
        fake_cv2 = SimpleNamespace(
            COLOR_BGR2RGB=1,
            cvtColor=lambda frame, _code: frame,
        )

        with tempfile.NamedTemporaryFile(suffix=".task") as model_file:
            with patch.dict(
                sys.modules,
                {"mediapipe": fake_mp, "cv2": fake_cv2},
            ):
                recognizer = go.GestureRecognizer(
                    model_file.name,
                )
                gestures = recognizer.detect(np.zeros((10, 10, 3)))

        self.assertEqual(len(gestures), 1)
        self.assertEqual(gestures[0].label, "Victory")
        self.assertEqual(gestures[0].hand.handedness, "Right")
        self.assertEqual(len(gestures[0].hand.world_points), 21)
        self.assertEqual(FakeGestureFactory.options.running_mode, "video")
        self.assertIsInstance(FakeGestureFactory.model.timestamp, int)


if __name__ == "__main__":
    unittest.main()
