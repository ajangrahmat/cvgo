"""Pengenalan gesture tangan berbasis MediaPipe Tasks."""

from __future__ import annotations

import time
from pathlib import Path
from threading import Lock
from typing import Any

from ._running_mode import resolve_running_mode
from ._validation import boolean, confidence, positive_int
from .hand import Hand, HandBox, draw_hand_points
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

    @property
    def handedness(self) -> str:
        return self.hand.handedness

    @property
    def points(self):
        return self.hand.points

    def box(self, *, padding: int = 10) -> HandBox:
        return self.hand.box(padding=padding)

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
        self.box().draw(frame, color=color, label=label)
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
        mode: str = "video",
        stream: bool | None = None,
        download: bool = True,
    ) -> None:
        max_hands = positive_int("max_hands", max_hands)
        if model_path is not None and not Path(model_path).expanduser().is_file():
            raise FileNotFoundError(f"Model tidak ditemukan: {model_path}")
        gesture_confidence = confidence(
            "gesture_confidence",
            gesture_confidence,
        )
        detection_confidence = confidence(
            "detection_confidence",
            detection_confidence,
        )
        presence_confidence = confidence(
            "presence_confidence",
            presence_confidence,
        )
        tracking_confidence = confidence(
            "tracking_confidence",
            tracking_confidence,
        )
        mirrored = boolean("mirrored", mirrored)
        download = boolean("download", download)

        self.mode = resolve_running_mode(mode, stream)

        try:
            import mediapipe as mp
        except ImportError as exc:
            raise ImportError(
                "MediaPipe belum terpasang. Jalankan: pip install mediapipe"
            ) from exc

        self.mp = mp
        self.gesture_confidence = gesture_confidence
        self.mirrored = mirrored
        self.stream = self.mode != "image"
        self._last_timestamp = -1
        self._result_lock = Lock()
        self._latest_gestures: list[Gesture] = []
        self.raw_result: Any | None = None
        self.result_timestamp: int | None = None
        self._closed = False
        self.model_path = resolve_model(
            "gesture_recognizer",
            model_path,
            download=download,
        )
        running_modes = {
            "image": mp.tasks.vision.RunningMode.IMAGE,
            "video": mp.tasks.vision.RunningMode.VIDEO,
            "live": mp.tasks.vision.RunningMode.LIVE_STREAM,
        }
        option_values = {
            "base_options": mp.tasks.BaseOptions(
                model_asset_path=str(self.model_path),
            ),
            "running_mode": running_modes[self.mode],
            "num_hands": max_hands,
            "min_hand_detection_confidence": detection_confidence,
            "min_hand_presence_confidence": presence_confidence,
            "min_tracking_confidence": tracking_confidence,
        }
        if self.mode == "live":
            option_values["result_callback"] = self._handle_live_result

        options = mp.tasks.vision.GestureRecognizerOptions(**option_values)
        recognizer = mp.tasks.vision.GestureRecognizer
        self.model = recognizer.create_from_options(options)

    def detect(self, frame) -> list[Gesture]:
        """Recognize gestures or return the latest completed live result."""
        if self._closed:
            raise RuntimeError("GestureRecognizer sudah ditutup")

        try:
            import cv2
        except ImportError as exc:
            raise ImportError("OpenCV belum terpasang.") from exc

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = self.mp.Image(
            image_format=self.mp.ImageFormat.SRGB,
            data=rgb,
        )

        if self.mode == "live":
            self.model.recognize_async(image, self._timestamp())
            return self._latest_result()

        timestamp = None
        if self.mode == "video":
            timestamp = self._timestamp()
            result = self.model.recognize_for_video(
                image,
                timestamp,
            )
        else:
            result = self.model.recognize(image)

        height, width = frame.shape[:2]
        return self._store_result(result, (width, height), timestamp)

    @property
    def result_ready(self) -> bool:
        """True after at least one result has completed."""
        with self._result_lock:
            return self.raw_result is not None

    def _gestures_from_result(
        self,
        result,
        frame_size: tuple[int, int],
    ) -> list[Gesture]:
        width, height = frame_size
        gestures = []

        for index, raw_hand in enumerate(result.hand_landmarks):
            label = "None"
            score = 0.0
            raw_gesture = None

            if index < len(result.gestures):
                categories = result.gestures[index]
                if categories:
                    raw_gesture = categories[0]
                    score = raw_gesture.score
                    label = raw_gesture.category_name or "None"

            if score < self.gesture_confidence:
                label = "None"

            handedness = "Unknown"
            hand_score = 0.0
            if index < len(result.handedness):
                categories = result.handedness[index]
                if categories:
                    handedness = categories[0].category_name or "Unknown"
                    hand_score = categories[0].score

            if not self.mirrored:
                handedness = {
                    "Left": "Right",
                    "Right": "Left",
                }.get(handedness, handedness)

            raw_world = None
            if index < len(result.hand_world_landmarks):
                raw_world = result.hand_world_landmarks[index]

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

    def _store_result(
        self,
        result,
        frame_size: tuple[int, int],
        timestamp: int | None,
    ) -> list[Gesture]:
        gestures = self._gestures_from_result(result, frame_size)

        with self._result_lock:
            if self._closed:
                return []
            self.raw_result = result
            self.result_timestamp = timestamp
            self._latest_gestures = gestures

        return list(gestures)

    def _latest_result(self) -> list[Gesture]:
        with self._result_lock:
            return list(self._latest_gestures)

    def _handle_live_result(
        self,
        result,
        output_image,
        timestamp: int,
    ) -> None:
        frame_size = (int(output_image.width), int(output_image.height))
        self._store_result(result, frame_size, timestamp)

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
            self._closed = True
            self.model.close()

    def __enter__(self) -> "GestureRecognizer":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
