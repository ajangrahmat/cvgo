"""Pengujian komponen publik CVGO tanpa kamera atau model MediaPipe."""

import unittest
from types import SimpleNamespace

import cvgo as go
from cvgo.face import LandmarkPoint


class FakeFace:
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.points = [
            LandmarkPoint(0.0, 0.0, 0.0)
            for _ in range(468)
        ]

    def __getitem__(self, index):
        return self.points[index]

    def set_pixel(self, index, x, y):
        self.points[index] = LandmarkPoint(
            x / self.width,
            y / self.height,
            0.0,
        )


class TestMetrics(unittest.TestCase):
    def test_eye_ratio_uses_frame_aspect_ratio(self):
        face = FakeFace()
        eye_pixels = (
            (0, 0),
            (1, 1),
            (3, 1),
            (4, 0),
            (3, -1),
            (1, -1),
        )

        for indices in ((33, 160, 158, 133, 153, 144),
                        (362, 385, 387, 263, 373, 380)):
            for index, point in zip(indices, eye_pixels):
                face.set_pixel(index, *point)

        self.assertAlmostEqual(go.eye_ratio(face), 0.5)

    def test_yaw_and_pitch_ratio(self):
        face = FakeFace()
        face.points[234] = LandmarkPoint(0.2, 0.0, 0.0)
        face.points[454] = LandmarkPoint(0.8, 0.0, 0.0)
        face.points[10] = LandmarkPoint(0.0, 0.2, 0.0)
        face.points[152] = LandmarkPoint(0.0, 0.8, 0.0)
        face.points[1] = LandmarkPoint(0.5, 0.5, 0.0)

        self.assertAlmostEqual(go.yaw_ratio(face), 0.5)
        self.assertAlmostEqual(go.pitch_ratio(face), 0.5)


class TestTimer(unittest.TestCase):
    def test_condition_must_hold_until_delay(self):
        timer = go.Timer(1.5)

        self.assertFalse(timer.check(True, now=10.0))
        self.assertFalse(timer.check(True, now=11.0))
        self.assertTrue(timer.check(True, now=11.5))
        self.assertEqual(timer.progress, 1.0)

        self.assertFalse(timer.check(False, now=12.0))
        self.assertEqual(timer.elapsed, 0.0)


class TestSmoother(unittest.TestCase):
    def test_exponential_average(self):
        smoother = go.Smoother(0.5)

        self.assertEqual(smoother.update(10), 10)
        self.assertEqual(smoother.update(20), 15)

        smoother.reset()
        self.assertIsNone(smoother.value)


class TestFPS(unittest.TestCase):
    def test_updates_after_interval(self):
        fps = go.FPS(update_every=1.0)
        fps.reset(now=10.0)

        self.assertEqual(fps.update(now=10.0), 0.0)
        self.assertEqual(fps.update(now=11.0), 2.0)

    def test_read_and_read_fps_aliases(self):
        fps = go.FPS(update_every=1.0)
        fps.reset(now=10.0)

        self.assertEqual(fps.read(now=10.0), 0.0)
        self.assertEqual(fps.read_fps(now=11.0), 2.0)


class FakeOwner:
    def draw(self, *_args, **_kwargs):
        return None


def raw_landmarks(count, *, visibility=None):
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


class TestHandResult(unittest.TestCase):
    def test_points_handedness_and_box(self):
        hand = go.Hand(
            raw_landmarks(21),
            FakeOwner(),
            (640, 480),
            handedness="Left",
            confidence=0.9,
        )

        self.assertEqual(len(hand), 21)
        self.assertTrue(hand.is_left)
        self.assertFalse(hand.is_right)
        self.assertEqual(
            hand.point(go.HandLandmark.INDEX_FINGER_TIP),
            hand[8],
        )
        self.assertEqual(hand.box(padding=0).xyxy, (0, 0, 639, 479))


class TestPoseResult(unittest.TestCase):
    def test_named_points_visibility_and_world_points(self):
        pose = go.Pose(
            raw_landmarks(33, visibility=0.8),
            FakeOwner(),
            (640, 480),
            raw_world=raw_landmarks(33, visibility=1.0),
        )

        self.assertEqual(len(pose), 33)
        self.assertEqual(len(pose.world_points), 33)
        self.assertTrue(pose.visible(go.PoseLandmark.LEFT_SHOULDER))
        self.assertFalse(
            pose.visible(go.PoseLandmark.LEFT_SHOULDER, confidence=0.9)
        )


if __name__ == "__main__":
    unittest.main()
