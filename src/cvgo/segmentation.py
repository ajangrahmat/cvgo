"""Selfie segmentation berbasis MediaPipe."""

from __future__ import annotations

from typing import Any


class SegmentationResult:
    """Mask segmentasi manusia dan helper untuk mengganti latar."""

    def __init__(self, mask, *, raw: Any | None = None) -> None:
        self.mask = mask
        self.raw = raw

    def foreground(self, *, threshold: float = 0.5):
        return self.mask > threshold

    def apply(
        self,
        frame,
        *,
        background=(0, 0, 0),
        threshold: float = 0.5,
    ):
        """Kembalikan frame baru dengan latar warna atau gambar lain."""
        try:
            import numpy as np
        except ImportError as exc:
            raise ImportError("NumPy belum terpasang.") from exc

        if hasattr(background, "shape"):
            if background.shape != frame.shape:
                raise ValueError("Ukuran background harus sama dengan frame")
            background_image = background
        else:
            background_image = np.empty_like(frame)
            background_image[:] = background

        condition = self.foreground(threshold=threshold)[..., None]
        return np.where(condition, frame, background_image)

    def blur(
        self,
        frame,
        *,
        amount: int = 35,
        threshold: float = 0.5,
    ):
        """Kembalikan frame baru dengan latar diburamkan."""
        try:
            import cv2
        except ImportError as exc:
            raise ImportError("OpenCV belum terpasang.") from exc

        if amount <= 0:
            raise ValueError("amount harus lebih dari 0")
        if amount % 2 == 0:
            amount += 1

        background = cv2.GaussianBlur(frame, (amount, amount), 0)
        return self.apply(
            frame,
            background=background,
            threshold=threshold,
        )


class SelfieSegmenter:
    """Pisahkan manusia utama dari latar belakang."""

    def __init__(self, *, model: int = 1) -> None:
        if model not in (0, 1):
            raise ValueError("model harus 0 (general) atau 1 (landscape)")

        try:
            import mediapipe as mp
        except ImportError as exc:
            raise ImportError(
                "MediaPipe belum terpasang. Jalankan: pip install mediapipe"
            ) from exc

        self.mp = mp
        self.model = mp.solutions.selfie_segmentation.SelfieSegmentation(
            model_selection=model,
        )
        self.raw_result: Any | None = None
        self._closed = False

    def segment(self, frame) -> SegmentationResult:
        try:
            import cv2
        except ImportError as exc:
            raise ImportError("OpenCV belum terpasang.") from exc

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        self.raw_result = self.model.process(rgb)
        return SegmentationResult(
            self.raw_result.segmentation_mask,
            raw=self.raw_result,
        )

    def close(self) -> None:
        if not self._closed:
            self.model.close()
            self._closed = True

    def __enter__(self) -> "SelfieSegmenter":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
