"""Object detection berbasis MediaPipe Tasks."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Sequence

from ._running_mode import resolve_running_mode
from ._validation import boolean, confidence as valid_confidence, positive_int
from .geometry import BoundingBox
from .models import resolve_model


@dataclass(frozen=True)
class ObjectBox(BoundingBox):
    """Kotak object detection dalam koordinat piksel."""


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
        label = self.label
        if show_score:
            label = f"{label} {self.score:.2f}"

        return self.box.draw(
            frame,
            color=color,
            thickness=thickness,
            label=label,
        )


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
        mode: str = "video",
        stream: bool | None = None,
        download: bool = True,
    ) -> None:
        if allow and deny:
            raise ValueError("allow dan deny tidak boleh dipakai bersamaan")
        confidence = valid_confidence("confidence", confidence)
        max_objects = positive_int("max_objects", max_objects)
        download = boolean("download", download)
        if model_path is not None and not Path(model_path).expanduser().is_file():
            raise FileNotFoundError(f"Model tidak ditemukan: {model_path}")

        self.mode = resolve_running_mode(mode, stream)

        try:
            import mediapipe as mp
        except ImportError as exc:
            raise ImportError(
                "MediaPipe belum terpasang. Jalankan: pip install mediapipe"
            ) from exc

        self.mp = mp
        self.stream = self.mode != "image"
        self._last_timestamp = -1
        self._result_lock = Lock()
        self._latest_objects: list[DetectedObject] = []
        self.raw_result: Any | None = None
        self.result_timestamp: int | None = None
        self._closed = False
        self.model_path = resolve_model(
            "object_detection",
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
            "display_names_locale": locale,
            "max_results": max_objects,
            "score_threshold": confidence,
            "category_allowlist": list(allow) if allow else None,
            "category_denylist": list(deny) if deny else None,
        }
        if self.mode == "live":
            option_values["result_callback"] = self._handle_live_result

        options = mp.tasks.vision.ObjectDetectorOptions(**option_values)
        self.model = mp.tasks.vision.ObjectDetector.create_from_options(options)

    def detect(self, frame) -> list[DetectedObject]:
        """Detect objects or return the latest completed live result."""
        if self._closed:
            raise RuntimeError("ObjectDetector sudah ditutup")

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
            self.model.detect_async(image, self._timestamp())
            return self._latest_result()

        timestamp = None
        if self.mode == "video":
            timestamp = self._timestamp()
            result = self.model.detect_for_video(
                image,
                timestamp,
            )
        else:
            result = self.model.detect(image)

        return self._store_result(result, timestamp)

    @property
    def result_ready(self) -> bool:
        """True after at least one result has completed."""
        with self._result_lock:
            return self.raw_result is not None

    def _objects_from_result(self, result) -> list[DetectedObject]:
        objects = []

        for detection in result.detections:
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

    def _store_result(
        self,
        result,
        timestamp: int | None,
    ) -> list[DetectedObject]:
        objects = self._objects_from_result(result)

        with self._result_lock:
            if self._closed:
                return []
            self.raw_result = result
            self.result_timestamp = timestamp
            self._latest_objects = objects

        return list(objects)

    def _latest_result(self) -> list[DetectedObject]:
        with self._result_lock:
            return list(self._latest_objects)

    def _handle_live_result(
        self,
        result,
        _output_image,
        timestamp: int,
    ) -> None:
        self._store_result(result, timestamp)

    def _timestamp(self) -> int:
        timestamp = time.monotonic_ns() // 1_000_000
        if timestamp <= self._last_timestamp:
            timestamp = self._last_timestamp + 1
        self._last_timestamp = timestamp
        return timestamp

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self.model.close()

    def __enter__(self) -> "ObjectDetector":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
