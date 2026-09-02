"""Kamera dan tampilan OpenCV dengan API yang ringkas."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any


class Camera:
    """Sumber frame dari webcam, video, atau URL stream.

    Kamera baru dibuka ketika ``open()``, context manager, atau iterasi dimulai.
    Backend default adalah ``cv2.CAP_ANY`` agar OpenCV memilih yang paling cocok.
    Objek ``capture`` tetap tersedia agar pengguna lanjut dapat memakai seluruh
    API ``cv2.VideoCapture``.
    """

    def __init__(
        self,
        source: int | str = 0,
        *,
        width: int | None = None,
        height: int | None = None,
        fps: float | None = None,
        backend: int | None = None,
    ) -> None:
        self.source = source
        self.width = width
        self.height = height
        self.requested_fps = fps
        self.backend = backend
        self.capture: Any | None = None

    @staticmethod
    def _cv2():
        try:
            import cv2
        except ImportError as exc:
            raise ImportError(
                "OpenCV belum terpasang. Jalankan: pip install opencv-contrib-python"
            ) from exc
        return cv2

    @property
    def opened(self) -> bool:
        return bool(self.capture is not None and self.capture.isOpened())

    @property
    def size(self) -> tuple[int, int]:
        if not self.opened:
            return (0, 0)
        cv2 = self._cv2()
        return (
            int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )

    def open(self) -> "Camera":
        if self.opened:
            return self

        cv2 = self._cv2()
        backend = cv2.CAP_ANY if self.backend is None else self.backend

        self.capture = cv2.VideoCapture(self.source, backend)
        if not self.capture.isOpened():
            self.capture.release()
            self.capture = None
            raise RuntimeError(f"Kamera/sumber {self.source!r} tidak bisa dibuka.")

        if self.width is not None:
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        if self.height is not None:
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        if self.requested_fps is not None:
            self.capture.set(cv2.CAP_PROP_FPS, self.requested_fps)
        return self

    def read(self):
        """Ambil satu frame; menghasilkan ``None`` jika pembacaan gagal."""
        if not self.opened:
            self.open()
        ok, frame = self.capture.read()
        return frame if ok else None

    def frames(self) -> Iterator[Any]:
        """Iterasi frame sampai sumber habis atau kamera ditutup."""
        if not self.opened:
            self.open()
        while self.opened:
            frame = self.read()
            if frame is None:
                break
            yield frame

    def show(
        self,
        frame,
        *,
        title: str = "CVGO",
        delay: int = 1,
        quit_key: str = "q",
    ) -> bool:
        """Tampilkan frame. Menghasilkan ``False`` ketika tombol keluar ditekan."""
        cv2 = self._cv2()
        cv2.imshow(title, frame)
        key = cv2.waitKey(delay) & 0xFF
        return key != ord(quit_key)

    def close(self) -> None:
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        self.close_windows()

    @staticmethod
    def close_windows() -> None:
        Camera._cv2().destroyAllWindows()

    def __iter__(self) -> Iterator[Any]:
        return self.frames()

    def __enter__(self) -> "Camera":
        return self.open()

    def __exit__(self, *_exc) -> None:
        self.close()
