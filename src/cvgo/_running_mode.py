"""Shared running-mode helpers for MediaPipe Tasks APIs."""

from __future__ import annotations


_MODE_ALIASES = {
    "image": "image",
    "video": "video",
    "live": "live",
    "livestream": "live",
    "live_stream": "live",
}


def resolve_running_mode(
    mode: str,
    stream: bool | None,
) -> str:
    """Normalize the public mode while preserving the old stream option."""
    if not isinstance(mode, str):
        raise TypeError("mode harus berupa string")

    key = mode.strip().lower().replace("-", "_").replace(" ", "_")

    try:
        normalized = _MODE_ALIASES[key]
    except KeyError as exc:
        raise ValueError(
            "mode harus 'image', 'video', atau 'live'"
        ) from exc

    if stream is None:
        return normalized
    if not isinstance(stream, bool):
        raise TypeError("stream harus True, False, atau None")

    legacy_mode = "video" if stream else "image"

    if normalized not in ("video", legacy_mode):
        raise ValueError("mode dan stream tidak boleh bertentangan")

    return legacy_mode
