"""Informasi sistem dan pemeriksaan instalasi CVGO."""

from __future__ import annotations

import platform
import sys
from importlib import metadata
from typing import Any

from ._version import __version__


DEPENDENCIES = {
    "numpy": ("NumPy", "1.26.4"),
    "opencv-contrib-python": ("OpenCV", "4.11.0.86"),
    "mediapipe": ("MediaPipe", "0.10.21"),
    "pyserial": ("PySerial", ">=3.5"),
}


def _installed_version(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def _version_numbers(value: str) -> tuple[int, ...]:
    numbers = []
    for part in value.split("."):
        digits = "".join(character for character in part if character.isdigit())
        if not digits:
            break
        numbers.append(int(digits))
    return tuple(numbers)


def _matches(version: str | None, expected: str) -> bool:
    if version is None:
        return False
    if expected.startswith(">="):
        return _version_numbers(version) >= _version_numbers(expected[2:])
    return version == expected


def system_info() -> dict[str, Any]:
    """Kembalikan versi runtime dan status dependency tanpa membuka kamera."""
    dependencies = {}
    for distribution, (label, expected) in DEPENDENCIES.items():
        installed = _installed_version(distribution)
        dependencies[distribution] = {
            "name": label,
            "version": installed,
            "expected": expected,
            "ok": _matches(installed, expected),
        }

    python_version = platform.python_version()
    return {
        "cvgo": __version__,
        "python": python_version,
        "python_supported": (3, 10) <= sys.version_info[:2] < (3, 13),
        "implementation": platform.python_implementation(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "dependencies": dependencies,
    }


def check_camera(
    source: int | str = 0,
    *,
    backend: int | None = None,
) -> dict[str, Any]:
    """Coba membaca satu frame untuk membantu diagnosis webcam/STB."""
    from .camera import Camera

    camera = Camera(source, backend=backend)
    try:
        frame = camera.read()
        if frame is None:
            return {
                "source": source,
                "ok": False,
                "error": "Kamera terbuka, tetapi frame tidak terbaca.",
            }

        height, width = frame.shape[:2]
        return {
            "source": source,
            "ok": True,
            "width": int(width),
            "height": int(height),
        }
    except Exception as exc:
        return {
            "source": source,
            "ok": False,
            "error": str(exc),
        }
    finally:
        camera.close(windows=False)


def checks_passed(info: dict[str, Any]) -> bool:
    return bool(
        info["python_supported"]
        and all(item["ok"] for item in info["dependencies"].values())
    )
