"""Geometri umum untuk hasil deteksi CVGO."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BoundingBox:
    """Kotak piksel yang dapat diperiksa dan digambar."""

    x: int
    y: int
    width: int
    height: int

    @property
    def left(self) -> int:
        return self.x

    @property
    def top(self) -> int:
        return self.y

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    @property
    def xyxy(self) -> tuple[int, int, int, int]:
        return self.left, self.top, self.right, self.bottom

    @property
    def center(self) -> tuple[int, int]:
        return (
            self.x + self.width // 2,
            self.y + self.height // 2,
        )

    @property
    def area(self) -> int:
        return max(0, self.width) * max(0, self.height)

    def draw(
        self,
        frame,
        *,
        color: tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
        label: str | None = None,
    ):
        """Gambar kotak dan label opsional pada frame."""
        try:
            import cv2
        except ImportError as exc:
            raise ImportError("OpenCV belum terpasang.") from exc

        cv2.rectangle(
            frame,
            (self.left, self.top),
            (self.right, self.bottom),
            color,
            thickness,
        )

        if label:
            cv2.putText(
                frame,
                label,
                (self.left, max(20, self.top - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                thickness,
                cv2.LINE_AA,
            )

        return frame
