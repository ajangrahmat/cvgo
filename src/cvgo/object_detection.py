"""Object detection berbasis MediaPipe Tasks."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .models import resolve_model


@dataclass(frozen=True)
class ObjectBox:
    """Kotak object detection dalam koordinat piksel."""

    x: int
    y: int
    width: int
    height: int

    @property
    def xyxy(self) -> tuple[int, int, int, int]:
        return self.x, self.y, self.x + self.width, self.y + self.height


class DetectedObject:
    """Satu object detection beserta label, score, dan kotaknya."""

    def __init__(
        self,
        raw: Any,
        box: ObjectBox,
        *,
        label: str,
        score: float,
        category_index: int | None = None,
        display_name: str | None = None,
    ) -> None:
        self.raw = raw
        self.box = box
        self.label = label
        self.score = float(score)
        self.category_index = category_index
        self.display_name = display_name

    @property
    def is_person(self) -> bool:
        return self.label.lower() == "person"

    def draw(
        self,
        frame,
        *,
        color: tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
        show_score: bool = True,
    ):
        """Gambar kotak dan label pada frame."""
        try:
            import cv2
        except ImportError as exc:
            raise ImportError("OpenCV belum terpasang.") from exc

        x1, y1, x2, y2 = self.box.xyxy
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
        label = self.label
        if show_score:
            label = f"{label} {self.score:.2f}"
        cv2.putText(
            frame,
            label,
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            thickness,
            cv2.LINE_AA,
        )
        return frame


class ObjectDetector:
    """Deteksi objek umum dengan EfficientDet-Lite0 sebagai default."""

    def __init__(
        self,
        model_path: str | Path | None = None,
        *,
        confidence: float = 0.5,
        max_objects: int = 10,
        allow: Sequence[str] | None = None,
        deny: Sequence[str] | None = None,
        locale: str = "en",
        stream: bool = True,
        download: bool = True,
    ) -> None:
        if allow and deny:
            raise ValueError("allow dan deny tidak boleh dipakai bersamaan")
        if not 0 <= confidence <= 1:
            raise ValueError("confidence harus antara 0 dan 1")
        if max_objects <= 0:
            raise ValueError("max_objects harus lebih dari 0")
        if model_path is not None and not Path(model_path).expanduser().is_file():
            raise FileNotFoundError(f"Model tidak ditemukan: {model_path}")

        try:
            import mediapipe as mp
        except ImportError as exc:
            raise ImportError(
                "MediaPipe belum terpasang. Jalankan: pip install mediapipe"
            ) from exc

        self.mp = mp
        self.stream = stream
        self._last_timestamp = -1
        self.model_path = resolve_model(
            "object_detection",
            model_path,
            download=download,
        )
        options = mp.tasks.vision.ObjectDetectorOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=str(self.model_path),
            ),
            running_mode=(
                mp.tasks.vision.RunningMode.VIDEO
                if stream
                else mp.tasks.vision.RunningMode.IMAGE
            ),
            display_names_locale=locale,
            max_results=max_objects,
            score_threshold=confidence,
            category_allowlist=list(allow) if allow else None,
            category_denylist=list(deny) if deny else None,
        )
        self.model = mp.tasks.vision.ObjectDetector.create_from_options(options)
        self.raw_result: Any | None = None
        self._closed = False

    def detect(self, frame) -> list[DetectedObject]:
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
            self.raw_result = self.model.detect_for_video(
                image,
                self._timestamp(),
            )
        else:
            self.raw_result = self.model.detect(image)
        objects = []

        for detection in self.raw_result.detections:
            if not detection.categories:
                continue

            category = detection.categories[0]
            raw_box = detection.bounding_box
            box = ObjectBox(
                raw_box.origin_x,
                raw_box.origin_y,
                raw_box.width,
                raw_box.height,
            )
            label = category.category_name or category.display_name
            label = label or str(category.index)
            objects.append(
                DetectedObject(
                    detection,
                    box,
                    label=label,
                    score=category.score,
                    category_index=category.index,
                    display_name=category.display_name or None,
                )
            )

        return objects

    def _timestamp(self) -> int:
        timestamp = time.monotonic_ns() // 1_000_000
        if timestamp <= self._last_timestamp:
            timestamp = self._last_timestamp + 1
        self._last_timestamp = timestamp
        return timestamp

    def close(self) -> None:
        if not self._closed:
            self.model.close()
            self._closed = True

    def __enter__(self) -> "ObjectDetector":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
