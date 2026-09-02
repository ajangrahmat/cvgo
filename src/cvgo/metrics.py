"""Metrik wajah sederhana dari landmark MediaPipe."""

from __future__ import annotations

import math

from .face import LandmarkFace


RIGHT_EYE = (33, 160, 158, 133, 153, 144)
LEFT_EYE = (362, 385, 387, 263, 373, 380)

FACE_LEFT = 234
FACE_RIGHT = 454
NOSE = 1
FOREHEAD = 10
CHIN = 152


def _pixel(face: LandmarkFace, index: int) -> tuple[float, float]:
    point = face[index]
    width = getattr(face, "width", 1)
    height = getattr(face, "height", 1)
    return point.x * width, point.y * height


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(
        a[0] - b[0],
        a[1] - b[1],
    )


def single_eye_ratio(
    face: LandmarkFace,
    indices: tuple[int, ...],
) -> float:
    """Hitung Eye Aspect Ratio untuk satu mata."""
    p1, p2, p3, p4, p5, p6 = [
        _pixel(face, index)
        for index in indices
    ]

    horizontal = _distance(p1, p4)
    if horizontal == 0:
        return 0.0

    vertical = _distance(p2, p6) + _distance(p3, p5)
    return vertical / (2.0 * horizontal)


def eye_ratio(face: LandmarkFace, eye: str = "both") -> float:
    """Hitung EAR mata kanan, kiri, atau rata-rata keduanya."""
    right = single_eye_ratio(face, RIGHT_EYE)
    left = single_eye_ratio(face, LEFT_EYE)

    if eye == "right":
        return right
    if eye == "left":
        return left
    if eye == "both":
        return (right + left) / 2.0

    raise ValueError("eye harus: both, right, atau left")


def yaw_ratio(face: LandmarkFace) -> float:
    """Posisi horizontal hidung terhadap lebar wajah.

    Nilai sekitar 0.5 berarti wajah menghadap ke depan.
    """
    left = face[FACE_LEFT].x
    right = face[FACE_RIGHT].x
    width = right - left

    if width == 0:
        return 0.5

    return (face[NOSE].x - left) / width


def pitch_ratio(face: LandmarkFace) -> float:
    """Posisi vertikal hidung terhadap tinggi wajah.

    Nilai sekitar 0.5 berarti kepala berada di posisi normal.
    """
    forehead = face[FOREHEAD].y
    chin = face[CHIN].y
    height = chin - forehead

    if height == 0:
        return 0.5

    return (face[NOSE].y - forehead) / height
