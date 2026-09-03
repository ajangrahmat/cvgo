"""Pelacakan tangan berbasis MediaPipe Hands."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Sequence

from ._validation import (
    boolean,
    choice,
    confidence,
    non_negative_int,
    positive_int,
)
from .face import LandmarkPoint
from .geometry import BoundingBox


HAND_CONNECTIONS = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (13, 17),
    (17, 18),
    (18, 19),
    (19, 20),
    (0, 17),
)


class HandLandmark(IntEnum):
    """Nama indeks untuk 21 landmark tangan."""

    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_FINGER_MCP = 5
    INDEX_FINGER_PIP = 6
    INDEX_FINGER_DIP = 7
    INDEX_FINGER_TIP = 8
    MIDDLE_FINGER_MCP = 9
    MIDDLE_FINGER_PIP = 10
    MIDDLE_FINGER_DIP = 11
    MIDDLE_FINGER_TIP = 12
    RING_FINGER_MCP = 13
    RING_FINGER_PIP = 14
    RING_FINGER_DIP = 15
    RING_FINGER_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20


@dataclass(frozen=True)
class HandBox(BoundingBox):
    """Kotak pembatas satu tangan dalam koordinat piksel."""

    confidence: float = 1.0

    def draw(
        self,
        frame,
        *,
        color: tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
        label: str | None = "Hand",
    ):
        return super().draw(
            frame,
            color=color,
            thickness=thickness,
            label=label,
        )


class Hand:
    """Hasil landmark, handedness, dan confidence untuk satu tangan."""

    def __init__(
        self,
        raw_hand: Any,
        owner: Any,
        frame_size: tuple[int, int],
        *,
        handedness: str = "Unknown",
        confidence: float = 0.0,
        raw_world: Any | None = None,
    ) -> None:
        self.raw = raw_hand
        self._owner = owner
        self.width, self.height = frame_size
        self.handedness = handedness
        self.confidence = float(confidence)
        raw_points = getattr(raw_hand, "landmark", raw_hand)
        self.points: tuple[LandmarkPoint, ...] = tuple(
            LandmarkPoint(point.x, point.y, point.z)
            for point in raw_points
        )
        self.raw_world = raw_world
        raw_world_points = raw_world if raw_world is not None else ()
        world_points = getattr(raw_world, "landmark", raw_world_points)
        self.world_points: tuple[LandmarkPoint, ...] = tuple(
            LandmarkPoint(point.x, point.y, point.z)
            for point in world_points
        )

    @property
    def is_left(self) -> bool:
        return self.handedness.lower() == "left"

    @property
    def is_right(self) -> bool:
        return self.handedness.lower() == "right"

    def __len__(self) -> int:
        return len(self.points)

    def __getitem__(self, index: int) -> LandmarkPoint:
        return self.points[index]

    def point(self, index: int) -> LandmarkPoint:
        return self.points[index]

    def box(self, *, padding: int = 10) -> HandBox:
        padding = non_negative_int("padding", padding)
        xs = [point.x for point in self.points]
        ys = [point.y for point in self.points]
        x1 = max(0, int(min(xs) * self.width) - padding)
        y1 = max(0, int(min(ys) * self.height) - padding)
        x2 = min(self.width - 1, int(max(xs) * self.width) + padding)
        y2 = min(self.height - 1, int(max(ys) * self.height) + padding)
        return HandBox(x1, y1, x2 - x1, y2 - y1, self.confidence)

    def draw(
        self,
        frame,
        *,
        color: tuple[int, int, int] = (0, 255, 0),
        point_color: tuple[int, int, int] = (255, 0, 255),
        thickness: int = 2,
        radius: int = 2,
    ):
        """Gambar landmark pada frame dan kembalikan frame yang sama."""
        self._owner.draw(
            frame,
            self,
            color=color,
            point_color=point_color,
            thickness=thickness,
            radius=radius,
        )
        return frame


class HandTracker:
    """Pelacak tangan dengan default yang cocok untuk webcam."""

    def __init__(
        self,
        *,
        max_hands: int = 2,
        model_complexity: int = 1,
        detection_confidence: float = 0.5,
        tracking_confidence: float = 0.5,
        static: bool = False,
        mirrored: bool = False,
    ) -> None:
        max_hands = positive_int("max_hands", max_hands)
        model_complexity = choice(
            "model_complexity",
            model_complexity,
            (0, 1),
        )
        detection_confidence = confidence(
            "detection_confidence",
            detection_confidence,
        )
        tracking_confidence = confidence(
            "tracking_confidence",
            tracking_confidence,
        )
        static = boolean("static", static)
        mirrored = boolean("mirrored", mirrored)
        try:
            import mediapipe as mp
        except ImportError as exc:
            raise ImportError(
                "MediaPipe belum terpasang. Jalankan: pip install mediapipe"
            ) from exc

        self.mp = mp
        self.mirrored = mirrored
        self.model = mp.solutions.hands.Hands(
            static_image_mode=static,
            max_num_hands=max_hands,
            model_complexity=model_complexity,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.raw_result: Any | None = None
        self._closed = False

    def detect(self, frame) -> list[Hand]:
        try:
            import cv2
        except ImportError as exc:
            raise ImportError("OpenCV belum terpasang.") from exc

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        self.raw_result = self.model.process(rgb)

        raw_hands: Sequence[Any] = self.raw_result.multi_hand_landmarks or ()
        world_hands: Sequence[Any] = (
            self.raw_result.multi_hand_world_landmarks or ()
        )
        handedness: Sequence[Any] = self.raw_result.multi_handedness or ()
        height, width = frame.shape[:2]
        hands = []

        for index, raw_hand in enumerate(raw_hands):
            label = "Unknown"
            confidence = 0.0

            if index < len(handedness) and handedness[index].classification:
                classification = handedness[index].classification[0]
                label = classification.label
                confidence = classification.score

                if not self.mirrored:
                    label = {"Left": "Right", "Right": "Left"}.get(
                        label,
                        label,
                    )

            hands.append(
                Hand(
                    raw_hand,
                    self,
                    (width, height),
                    handedness=label,
                    confidence=confidence,
                    raw_world=(
                        world_hands[index]
                        if index < len(world_hands)
                        else None
                    ),
                )
            )

        return hands

    def draw(
        self,
        frame,
        hand: Hand,
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
            landmark_list=hand.raw,
            connections=self.mp.solutions.hands.HAND_CONNECTIONS,
            landmark_drawing_spec=point_spec,
            connection_drawing_spec=connection_spec,
        )

    def close(self) -> None:
        if not self._closed:
            self.model.close()
            self._closed = True

    def __enter__(self) -> "HandTracker":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()


def draw_hand_points(
    frame,
    hand: Hand,
    *,
    color: tuple[int, int, int] = (0, 255, 0),
    point_color: tuple[int, int, int] = (255, 0, 255),
    thickness: int = 2,
    radius: int = 2,
) -> None:
    """Gambar hasil hand Tasks API tanpa mengubah data landmark."""
    try:
        import cv2
    except ImportError as exc:
        raise ImportError("OpenCV belum terpasang.") from exc

    pixels = [point.pixel((hand.width, hand.height)) for point in hand.points]

    for start, end in HAND_CONNECTIONS:
        cv2.line(frame, pixels[start], pixels[end], color, thickness)

    for pixel in pixels:
        cv2.circle(frame, pixel, radius, point_color, -1)
