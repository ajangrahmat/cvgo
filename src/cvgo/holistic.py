"""Face, pose, dan hand landmarks dalam satu pipeline MediaPipe."""

from __future__ import annotations

from typing import Any

from .face import LandmarkFace
from .hand import Hand
from .pose import Pose


class HolisticResult:
    """Hasil gabungan face, pose, kedua tangan, dan mask opsional."""

    def __init__(
        self,
        owner: "HolisticTracker",
        raw: Any,
        *,
        face: LandmarkFace | None,
        pose: Pose | None,
        left_hand: Hand | None,
        right_hand: Hand | None,
        mask: Any | None,
    ) -> None:
        self._owner = owner
        self.raw = raw
        self.face = face
        self.pose = pose
        self.left_hand = left_hand
        self.right_hand = right_hand
        self.mask = mask

    @property
    def found(self) -> bool:
        return any((self.face, self.pose, self.left_hand, self.right_hand))

    @property
    def hands(self) -> list[Hand]:
        return [
            hand
            for hand in (self.left_hand, self.right_hand)
            if hand is not None
        ]

    def draw(
        self,
        frame,
        *,
        face: bool = True,
        pose: bool = True,
        hands: bool = True,
    ):
        """Gambar bagian hasil yang dipilih pada frame."""
        if face and self.face:
            self.face.draw(frame)
        if pose and self.pose:
            self.pose.draw(frame)
        if hands:
            for hand in self.hands:
                hand.draw(frame)
        return frame


class HolisticTracker:
    """Lacak 543 landmark wajah, tubuh, dan kedua tangan."""

    def __init__(
        self,
        *,
        model_complexity: int = 1,
        detection_confidence: float = 0.5,
        tracking_confidence: float = 0.5,
        smooth: bool = True,
        refine_face: bool = False,
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
        self.model = mp.solutions.holistic.Holistic(
            static_image_mode=static,
            model_complexity=model_complexity,
            smooth_landmarks=smooth,
            enable_segmentation=segmentation,
            smooth_segmentation=smooth,
            refine_face_landmarks=refine_face,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.raw_result: Any | None = None
        self._closed = False

    def detect(self, frame) -> HolisticResult:
        try:
            import cv2
        except ImportError as exc:
            raise ImportError("OpenCV belum terpasang.") from exc

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        raw = self.model.process(rgb)
        self.raw_result = raw
        height, width = frame.shape[:2]
        size = (width, height)

        face = (
            LandmarkFace(raw.face_landmarks, self, size)
            if raw.face_landmarks
            else None
        )
        pose = (
            Pose(
                raw.pose_landmarks,
                self,
                size,
                raw_world=raw.pose_world_landmarks,
                mask=raw.segmentation_mask,
            )
            if raw.pose_landmarks
            else None
        )
        left_hand = (
            Hand(
                raw.left_hand_landmarks,
                self,
                size,
                handedness="Left",
                confidence=1.0,
            )
            if raw.left_hand_landmarks
            else None
        )
        right_hand = (
            Hand(
                raw.right_hand_landmarks,
                self,
                size,
                handedness="Right",
                confidence=1.0,
            )
            if raw.right_hand_landmarks
            else None
        )
        return HolisticResult(
            self,
            raw,
            face=face,
            pose=pose,
            left_hand=left_hand,
            right_hand=right_hand,
            mask=raw.segmentation_mask,
        )

    def draw(self, frame, part, **kwargs) -> None:
        if isinstance(part, LandmarkFace):
            self._draw_face(frame, part, **kwargs)
        elif isinstance(part, Pose):
            self._draw_pose(frame, part, **kwargs)
        elif isinstance(part, Hand):
            self._draw_hand(frame, part, **kwargs)
        else:
            raise TypeError("Bagian holistic tidak dikenal")

    def _specs(
        self,
        *,
        color,
        point_color,
        thickness,
        radius,
    ):
        drawing = self.mp.solutions.drawing_utils
        points = drawing.DrawingSpec(
            color=point_color,
            thickness=thickness,
            circle_radius=radius,
        )
        lines = drawing.DrawingSpec(
            color=color,
            thickness=thickness,
            circle_radius=radius,
        )
        return points, lines

    def _draw_face(
        self,
        frame,
        face: LandmarkFace,
        *,
        style: str = "contours",
        color=(0, 255, 0),
        thickness: int = 1,
        radius: int = 1,
        **_kwargs,
    ) -> None:
        mesh = self.mp.solutions.face_mesh
        connections = {
            "contours": mesh.FACEMESH_CONTOURS,
            "tesselation": mesh.FACEMESH_TESSELATION,
            "iris": mesh.FACEMESH_IRISES,
            "all": mesh.FACEMESH_TESSELATION,
        }
        if style not in connections:
            raise ValueError("style harus: contours, tesselation, iris, atau all")
        spec = self.mp.solutions.drawing_utils.DrawingSpec(
            color=color,
            thickness=thickness,
            circle_radius=radius,
        )
        self.mp.solutions.drawing_utils.draw_landmarks(
            frame,
            face.raw,
            connections[style],
            spec,
            spec,
        )

    def _draw_pose(
        self,
        frame,
        pose: Pose,
        *,
        color=(0, 255, 0),
        point_color=(255, 0, 255),
        thickness: int = 2,
        radius: int = 2,
        **_kwargs,
    ) -> None:
        points, lines = self._specs(
            color=color,
            point_color=point_color,
            thickness=thickness,
            radius=radius,
        )
        self.mp.solutions.drawing_utils.draw_landmarks(
            frame,
            pose.raw,
            self.mp.solutions.pose.POSE_CONNECTIONS,
            points,
            lines,
        )

    def _draw_hand(
        self,
        frame,
        hand: Hand,
        *,
        color=(0, 255, 0),
        point_color=(255, 0, 255),
        thickness: int = 2,
        radius: int = 2,
        **_kwargs,
    ) -> None:
        points, lines = self._specs(
            color=color,
            point_color=point_color,
            thickness=thickness,
            radius=radius,
        )
        self.mp.solutions.drawing_utils.draw_landmarks(
            frame,
            hand.raw,
            self.mp.solutions.hands.HAND_CONNECTIONS,
            points,
            lines,
        )

    def close(self) -> None:
        if not self._closed:
            self.model.close()
            self._closed = True

    def __enter__(self) -> "HolisticTracker":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
