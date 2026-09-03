"""Pengelolaan model MediaPipe Tasks yang dipakai CVGO."""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from ._validation import boolean, positive_number
from ._version import USER_AGENT


@dataclass(frozen=True)
class ModelInfo:
    filename: str
    url: str
    format: str
    sha256: str


MODELS = {
    "object_detection": ModelInfo(
        filename="efficientdet_lite0.tflite",
        url=(
            "https://storage.googleapis.com/mediapipe-models/"
            "object_detector/efficientdet_lite0/int8/1/"
            "efficientdet_lite0.tflite"
        ),
        format="tflite",
        sha256=(
            "0720bf247bd76e6594ea28fa9c6f7c52"
            "42be774818997dbbeffc4da460c723bb"
        ),
    ),
    "gesture_recognizer": ModelInfo(
        filename="gesture_recognizer.task",
        url=(
            "https://storage.googleapis.com/mediapipe-models/"
            "gesture_recognizer/gesture_recognizer/float16/1/"
            "gesture_recognizer.task"
        ),
        format="task",
        sha256=(
            "97952348cf6a6a4915c2ea1496b4b37e"
            "babc50cbbf80571435643c455f2b0482"
        ),
    ),
}


def model_cache_dir() -> Path:
    """Kembalikan folder cache model CVGO pada sistem operasi aktif."""
    custom = os.environ.get("CVGO_MODEL_DIR")
    if custom:
        return Path(custom).expanduser()

    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))

    return base / "cvgo" / "models"


def model_path(name: str, *, directory: str | os.PathLike | None = None) -> Path:
    """Kembalikan lokasi default sebuah model tanpa mengunduhnya."""
    try:
        info = MODELS[name]
    except KeyError as exc:
        choices = ", ".join(sorted(MODELS))
        raise ValueError(f"Model tidak dikenal. Pilih: {choices}") from exc

    root = Path(directory).expanduser() if directory else model_cache_dir()
    return root / info.filename


def _valid_model(path: Path, format_name: str, sha256: str) -> bool:
    if not path.is_file() or path.stat().st_size < 1024:
        return False

    digest = hashlib.sha256()
    with path.open("rb") as model_file:
        header = model_file.read(8)
        digest.update(header)
        while chunk := model_file.read(1024 * 1024):
            digest.update(chunk)

    if format_name == "tflite":
        valid_header = header[4:8] == b"TFL3"
    elif format_name == "task":
        valid_header = header.startswith(b"PK")
    else:
        valid_header = True
    return valid_header and digest.hexdigest() == sha256


def download_model(
    name: str,
    *,
    directory: str | os.PathLike | None = None,
    force: bool = False,
    timeout: float = 120.0,
) -> Path:
    """Unduh model resmi MediaPipe ke cache dan kembalikan lokasinya."""
    try:
        info = MODELS[name]
    except KeyError as exc:
        choices = ", ".join(sorted(MODELS))
        raise ValueError(f"Model tidak dikenal. Pilih: {choices}") from exc

    force = boolean("force", force)
    timeout = positive_number("timeout", timeout)
    destination = model_path(name, directory=directory)
    if not force and _valid_model(destination, info.format, info.sha256):
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        info.url,
        headers={"User-Agent": USER_AGENT},
    )
    temp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".part",
            delete=False,
        ) as output:
            temp_path = Path(output.name)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)

        if not _valid_model(temp_path, info.format, info.sha256):
            raise RuntimeError("File model yang diunduh tidak valid.")

        os.replace(temp_path, destination)
        return destination
    except (OSError, urllib.error.URLError) as exc:
        raise RuntimeError(
            "Model tidak dapat diunduh. Periksa internet atau isi model_path."
        ) from exc
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def resolve_model(
    name: str,
    path: str | os.PathLike | None = None,
    *,
    download: bool = True,
) -> Path:
    """Pakai model kustom atau siapkan model default CVGO."""
    download = boolean("download", download)
    if path is not None:
        custom_path = Path(path).expanduser()
        if not custom_path.is_file():
            raise FileNotFoundError(f"Model tidak ditemukan: {custom_path}")
        return custom_path

    cached = model_path(name)
    info = MODELS[name]
    if _valid_model(cached, info.format, info.sha256):
        return cached
    if download:
        return download_model(name)

    raise FileNotFoundError(
        f"Model belum tersedia. Jalankan download_model({name!r}) "
        "atau isi model_path."
    )
