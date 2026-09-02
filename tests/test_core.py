"""Pengujian komponen murni yang tidak memerlukan kamera."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from cvgo import Camera, DriverMonitor, LandmarkPoint, MonitorResult


class FakeCapture:
    def isOpened(self):
        return True

    def get(self, _property):
        return 0

    def release(self):
        return None


class TestCameraBackend(unittest.TestCase):
    def test_default_backend_is_cap_any(self):
        capture = FakeCapture()
        fake_cv2 = SimpleNamespace(
            CAP_ANY=0,
            VideoCapture=Mock(return_value=capture),
        )

        with patch.object(Camera, "_cv2", return_value=fake_cv2):
            Camera(4).open()

        fake_cv2.VideoCapture.assert_called_once_with(
            4,
            fake_cv2.CAP_ANY,
        )

    def test_custom_backend_is_preserved(self):
        capture = FakeCapture()
        fake_cv2 = SimpleNamespace(
            CAP_ANY=0,
            VideoCapture=Mock(return_value=capture),
        )

        with patch.object(Camera, "_cv2", return_value=fake_cv2):
            Camera(4, backend=700).open()

        fake_cv2.VideoCapture.assert_called_once_with(4, 700)


class FakeFace:
    def __init__(self, points):
        self.points = points

    def __getitem__(self, index):
        return self.points[index]


class TestLandmarkPoint(unittest.TestCase):
    def test_pixel_from_size(self):
        point = LandmarkPoint(0.5, 0.25, 0.0)
        self.assertEqual(point.pixel((640, 480)), (320, 120))


class TestDriverMath(unittest.TestCase):
    def test_ear(self):
        points = [LandmarkPoint(0, 0, 0) for _ in range(6)]
        points[0] = LandmarkPoint(0, 0, 0)
        points[1] = LandmarkPoint(1, 1, 0)
        points[2] = LandmarkPoint(3, 1, 0)
        points[3] = LandmarkPoint(4, 0, 0)
        points[4] = LandmarkPoint(3, -1, 0)
        points[5] = LandmarkPoint(1, -1, 0)
        ear = DriverMonitor.calculate_ear(FakeFace(points), (0, 1, 2, 3, 4, 5))
        self.assertAlmostEqual(ear, 0.5)


class TestMonitorResult(unittest.TestCase):
    def test_mask_and_direction(self):
        result = MonitorResult(
            frame=None,
            face_found=True,
            looking_away=True,
            look_direction="left",
            mask=DriverMonitor.BIT_LOOKING_AWAY,
        )
        self.assertTrue(result.alert)
        self.assertTrue(result.looking_left)
        self.assertFalse(result.looking_right)
        self.assertEqual(result.mask_hex, "2")


class FakeCamera:
    def __init__(self, frame):
        self.frame = frame

    def read(self):
        return self.frame


class TestDriverRead(unittest.TestCase):
    def test_read_processes_camera_frame(self):
        monitor = object.__new__(DriverMonitor)
        monitor.camera = FakeCamera("frame")
        monitor.process = lambda frame: f"processed:{frame}"

        self.assertEqual(monitor.read(), "processed:frame")

    def test_read_returns_none_when_camera_fails(self):
        monitor = object.__new__(DriverMonitor)
        monitor.camera = FakeCamera(None)
        monitor.process = lambda frame: frame

        self.assertIsNone(monitor.read())


if __name__ == "__main__":
    unittest.main()
