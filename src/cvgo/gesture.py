"""Pengenalan gesture tangan berbasis MediaPipe Tasks."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .hand import Hand, draw_hand_points
from .models import resolve_model


class Gesture:
    """Satu gesture beserta hand landmarks dan confidence."""

    def __init__(
        self,
        hand: Hand,
        *,
        label: str,
        score: float,
        raw: Any | None = None,
    ) -> None:
        self.hand = hand
        self.label = label
        self.score = float(score)
        self.raw = raw

    @property
    def recognized(self) -> bool:
        return self.label not in ("", "None", "Unknown")

    def draw(
        self,
        frame,
        *,
        color: tuple[int, int, int] = (0, 255, 0),
        point_color: tuple[int, int, int] = (255, 0, 255),
    ):
        self.hand.draw(
            frame,
            color=color,
            point_color=point_color,
        )
        label = self.label
        if self.recognized:
            label = f"{label} {self.score:.2f}"
        self.hand.box().draw(frame, color=color, label=label)
        return frame


class GestureRecognizer:
    """Kenali tujuh gesture tangan umum dengan model default MediaPipe."""

    def __init__(
        self,
        model_path: str | Path | None = None,
        *,
        max_hands: int = 2,
        gesture_confidence: float = 0.5,
        detection_confidence: float = 0.5,
        presence_confidence: float = 0.5,
        tracking_confidence: float = 0.5,
        mirrored: bool = False,
        stream: bool = True,
        download: bool = True,
    ) -> None:
        if max_hands <= 0:
            raise ValueError("max_hands harus lebih dari 0")
        if model_path is not None and not Path(model_path).expanduser().is_file():
            raise FileNotFoundError(f"Model tidak ditemukan: {model_path}")
        for value in (
            gesture_confidence,
            detection_confidence,
            presence_confidence,
            tracking_confidence,
        ):
            if not 0 <= value <= 1:
                raise ValueError("Nilai confidence harus antara 0 dan 1")

        try:
            import mediapipe as mp
        except ImportError as exc:
            raise ImportError(
                "MediaPipe belum terpasang. Jalankan: pip install mediapipe"
            ) from exc

        self.mp = mp
        self.gesture_confidence = gesture_confidence
        self.mirrored = mirrored
        self.stream = stream
        self._last_timestamp = -1
        self.model_path = resolve_model(
            "gesture_recognizer",
            model_path,
            download=download,
        )
        options = mp.tasks.vision.GestureRecognizerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=str(self.model_path),
            ),
            running_mode=(
                mp.tasks.vision.RunningMode.VIDEO
                if stream
                else mp.tasks.vision.RunningMode.IMAGE
            ),
            num_hands=max_hands,
            min_hand_detection_confidence=detection_confidence,
            min_hand_presence_confidence=presence_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        recognizer = mp.tasks.vision.GestureRecognizer
        self.model = recognizer.create_from_options(options)
        self.raw_result: Any | None = None
        self._closed = False

    def detect(self, frame) -> list[Gesture]:
        try:
            import cv2
        except ImportError as exc:
            raise ImportError("OpenCV belum terpasang.") from exc

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = self.mp.Image(
            image_format=self.mp.ImageFormat.SRGB,
            data=rgb,
        )
        if self.stream:
            self.raw_result = self.model.recognize_for_video(
                image,
                self._timestamp(),
            )
        else:
            self.raw_result = self.model.recognize(image)
        height, width = frame.shape[:2]
        gestures = []

        for index, raw_hand in enumerate(self.raw_result.hand_landmarks):
            label = "None"
            score = 0.0
            raw_gesture = None

            if index < len(self.raw_result.gestures):
                categories = self.raw_result.gestures[index]
                if categories:
                    raw_gesture = categories[0]
                    score = raw_gesture.score
                    label = raw_gesture.category_name or "None"

            if score < self.gesture_confidence:
                label = "None"

            handedness = "Unknown"
            hand_score = 0.0
            if index < len(self.raw_result.handedness):
                categories = self.raw_result.handedness[index]
                if categories:
                    handedness = categories[0].category_name or "Unknown"
                    hand_score = categories[0].score

            if not self.mirrored:
                handedness = {
                    "Left": "Right",
                    "Right": "Left",
                }.get(handedness, handedness)

            raw_world = None
            if index < len(self.raw_result.hand_world_landmarks):
                raw_world = self.raw_result.hand_world_landmarks[index]

            hand = Hand(
                raw_hand,
                self,
                (width, height),
                handedness=handedness,
                confidence=hand_score,
                raw_world=raw_world,
            )
            gestures.append(
                Gesture(
                    hand,
                    label=label,
                    score=score,
                    raw=raw_gesture,
                )
            )

        return gestures

    def _timestamp(self) -> int:
        timestamp = time.monotonic_ns() // 1_000_000
        if timestamp <= self._last_timestamp:
            timestamp = self._last_timestamp + 1
        self._last_timestamp = timestamp
        return timestamp

    def draw(self, frame, hand: Hand, **kwargs) -> None:
        draw_hand_points(frame, hand, **kwargs)

    def close(self) -> None:
        if not self._closed:
            self.model.close()
            self._closed = True

    def __enter__(self) -> "GestureRecognizer":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
