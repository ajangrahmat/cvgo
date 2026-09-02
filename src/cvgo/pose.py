"""Pelacakan pose tubuh berbasis MediaPipe Pose."""

from __future__ import annotations

from enum import IntEnum
from typing import Any

from .face import LandmarkPoint


class PoseLandmark(IntEnum):
    """Nama indeks untuk 33 landmark pose tubuh."""

    NOSE = 0
    LEFT_EYE_INNER = 1
    LEFT_EYE = 2
    LEFT_EYE_OUTER = 3
    RIGHT_EYE_INNER = 4
    RIGHT_EYE = 5
    RIGHT_EYE_OUTER = 6
    LEFT_EAR = 7
    RIGHT_EAR = 8
    MOUTH_LEFT = 9
    MOUTH_RIGHT = 10
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_PINKY = 17
    RIGHT_PINKY = 18
    LEFT_INDEX = 19
    RIGHT_INDEX = 20
    LEFT_THUMB = 21
    RIGHT_THUMB = 22
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_HEEL = 29
    RIGHT_HEEL = 30
    LEFT_FOOT_INDEX = 31
    RIGHT_FOOT_INDEX = 32


def _to_point(raw_point: Any) -> LandmarkPoint:
    return LandmarkPoint(
        raw_point.x,
        raw_point.y,
        raw_point.z,
        getattr(raw_point, "visibility", None),
        getattr(raw_point, "presence", None),
    )


class Pose:
    """Hasil 33 landmark pose untuk satu orang utama."""

    def __init__(
        self,
        raw_pose: Any,
        owner: "PoseTracker",
        frame_size: tuple[int, int],
        *,
        raw_world: Any | None = None,
        mask: Any | None = None,
    ) -> None:
        self.raw = raw_pose
        self.raw_world = raw_world
        self._owner = owner
        self.width, self.height = frame_size
        self.mask = mask
        self.points: tuple[LandmarkPoint, ...] = tuple(
            _to_point(point) for point in raw_pose.landmark
        )
        if raw_world is None:
            self.world_points: tuple[LandmarkPoint, ...] = ()
        else:
            self.world_points = tuple(
                _to_point(point) for point in raw_world.landmark
            )

    def __len__(self) -> int:
        return len(self.points)

    def __getitem__(self, index: int) -> LandmarkPoint:
        return self.points[index]

    def point(self, index: int) -> LandmarkPoint:
        return self.points[index]

    def visible(self, index: int, *, confidence: float = 0.5) -> bool:
        visibility = self.points[index].visibility
        return visibility is None or visibility >= confidence

    def draw(
        self,
        frame,
        *,
        color: tuple[int, int, int] = (0, 255, 0),
        point_color: tuple[int, int, int] = (255, 0, 255),
        thickness: int = 2,
        radius: int = 2,
    ):
        """Gambar pose pada frame dan kembalikan frame yang sama."""
        self._owner.draw(
            frame,
            self,
            color=color,
            point_color=point_color,
            thickness=thickness,
            radius=radius,
        )
        return frame


class PoseTracker:
    """Pelacak satu pose utama dengan default yang cocok untuk webcam."""

    def __init__(
        self,
        *,
        model_complexity: int = 1,
        detection_confidence: float = 0.5,
        tracking_confidence: float = 0.5,
        smooth: bool = True,
        segmentation: bool = False,
        static: bool = False,
    ) -> None:
        try:
            import mediapipe as mp
        except ImportError as exc:
            raise ImportError(
                "MediaPipe belum terpasang. Jalankan: pip install mediapipe"
            ) from exc

        self.mp = mp
        self.model = mp.solutions.pose.Pose(
            static_image_mode=static,
            model_complexity=model_complexity,
            smooth_landmarks=smooth,
            enable_segmentation=segmentation,
            smooth_segmentation=smooth,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.raw_result: Any | None = None
        self._closed = False

    def detect(self, frame) -> Pose | None:
        try:
            import cv2
        except ImportError as exc:
            raise ImportError("OpenCV belum terpasang.") from exc

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        self.raw_result = self.model.process(rgb)

        raw_pose = self.raw_result.pose_landmarks
        if raw_pose is None:
            return None

        height, width = frame.shape[:2]
        return Pose(
            raw_pose,
            self,
            (width, height),
            raw_world=self.raw_result.pose_world_landmarks,
            mask=self.raw_result.segmentation_mask,
        )

    def draw(
        self,
        frame,
        pose: Pose,
        *,
        color: tuple[int, int, int] = (0, 255, 0),
        point_color: tuple[int, int, int] = (255, 0, 255),
        thickness: int = 2,
        radius: int = 2,
    ) -> None:
        drawing = self.mp.solutions.drawing_utils
        point_spec = drawing.DrawingSpec(
            color=point_color,
            thickness=thickness,
            circle_radius=radius,
        )
        connection_spec = drawing.DrawingSpec(
            color=color,
            thickness=thickness,
            circle_radius=radius,
        )
        drawing.draw_landmarks(
            image=frame,
            landmark_list=pose.raw,
            connections=self.mp.solutions.pose.POSE_CONNECTIONS,
            landmark_drawing_spec=point_spec,
            connection_drawing_spec=connection_spec,
        )

    def close(self) -> None:
        if not self._closed:
            self.model.close()
            self._closed = True

    def __enter__(self) -> "PoseTracker":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
