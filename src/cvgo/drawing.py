"""Helper gambar OpenCV dengan default yang ramah pemula."""

from __future__ import annotations


def put_text(
    frame,
    text: str,
    position: tuple[int, int] = (20, 35),
    *,
    color: tuple[int, int, int] = (0, 255, 0),
    scale: float = 0.7,
    thickness: int = 2,
    background: bool = False,
):
    """Tulis teks pada frame dan kembalikan frame yang sama."""
    try:
        import cv2
    except ImportError as exc:
        raise ImportError("OpenCV belum terpasang.") from exc

    font = cv2.FONT_HERSHEY_SIMPLEX

    if background:
        size, baseline = cv2.getTextSize(
            text,
            font,
            scale,
            thickness,
        )
        x, y = position
        width, height = size
        cv2.rectangle(
            frame,
            (x - 6, y - height - 6),
            (x + width + 6, y + baseline + 6),
            (0, 0, 0),
            -1,
        )

    cv2.putText(
        frame,
        text,
        position,
        font,
        scale,
        color,
        thickness,
        cv2.LINE_AA,
    )
    return frame

