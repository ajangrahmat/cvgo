"""Timer, smoothing, dan penghitung FPS yang dapat digunakan ulang."""

from __future__ import annotations

import time

from ._validation import non_negative_number, positive_number


class Timer:
    """Aktif setelah kondisi bertahan selama durasi tertentu."""

    def __init__(self, seconds: float = 1.0) -> None:
        self.seconds = non_negative_number("seconds", seconds)
        self.started_at: float | None = None
        self.elapsed = 0.0
        self.active = False

    @property
    def progress(self) -> float:
        if self.seconds == 0:
            return 1.0 if self.active else 0.0
        return min(self.elapsed / self.seconds, 1.0)

    def check(self, condition: bool, *, now: float | None = None) -> bool:
        """Perbarui timer dan kembalikan status aktif."""
        now = time.monotonic() if now is None else now

        if not condition:
            self.reset()
            return False

        if self.started_at is None:
            self.started_at = now

        self.elapsed = now - self.started_at
        self.active = self.elapsed >= self.seconds
        return self.active

    def reset(self) -> None:
        self.started_at = None
        self.elapsed = 0.0
        self.active = False


class Smoother:
    """Exponential moving average untuk menghaluskan nilai deteksi."""

    def __init__(self, alpha: float = 0.45) -> None:
        alpha = positive_number("alpha", alpha)
        if alpha > 1:
            raise ValueError("alpha harus lebih dari 0 dan maksimal 1")

        self.alpha = float(alpha)
        self.value: float | None = None

    def update(self, value: float) -> float:
        value = float(value)

        if self.value is None:
            self.value = value
        else:
            self.value = self.alpha * value + (1.0 - self.alpha) * self.value

        return self.value

    def reset(self) -> None:
        self.value = None


class FPS:
    """Penghitung frame per second."""

    def __init__(self, update_every: float = 1.0) -> None:
        self.update_every = positive_number("update_every", update_every)
        self.started_at = time.monotonic()
        self.frames = 0
        self.value = 0.0

    def update(self, *, now: float | None = None) -> float:
        now = time.monotonic() if now is None else now
        self.frames += 1
        elapsed = now - self.started_at

        if elapsed >= self.update_every:
            self.value = self.frames / elapsed
            self.frames = 0
            self.started_at = now

        return self.value

    def read(self, *, now: float | None = None) -> float:
        """Hitung satu frame dan kembalikan nilai FPS terbaru."""
        return self.update(now=now)

    def read_fps(self, *, now: float | None = None) -> float:
        """Alias eksplisit untuk ``read()``."""
        return self.read(now=now)

    def reset(self, *, now: float | None = None) -> None:
        self.started_at = time.monotonic() if now is None else now
        self.frames = 0
        self.value = 0.0
