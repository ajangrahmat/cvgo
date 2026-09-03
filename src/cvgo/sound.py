"""Alarm suara non-blocking untuk proyek Computer Vision."""

from __future__ import annotations

import platform
import threading
import time

from ._validation import non_negative_number, positive_int


class Alarm:
    """Alarm sederhana dengan cooldown agar tidak bertumpuk."""

    def __init__(
        self,
        *,
        frequency: int = 1500,
        duration: int = 180,
        repeat: int = 3,
        cooldown: float = 0.8,
    ) -> None:
        self.frequency = positive_int("frequency", frequency)
        self.duration = positive_int("duration", duration)
        self.repeat = positive_int("repeat", repeat)
        self.cooldown = non_negative_number("cooldown", cooldown)
        self.last_triggered = 0.0
        self.busy = False

    def trigger(self, condition: bool = True) -> bool:
        """Bunyikan alarm jika kondisi benar dan cooldown sudah selesai."""
        now = time.monotonic()

        if not condition or self.busy:
            return False

        if now - self.last_triggered < self.cooldown:
            return False

        self.last_triggered = now
        self.busy = True

        threading.Thread(
            target=self._play,
            daemon=True,
        ).start()
        return True

    def _play(self) -> None:
        try:
            for _ in range(self.repeat):
                if platform.system() == "Windows":
                    import winsound

                    winsound.Beep(
                        self.frequency,
                        self.duration,
                    )
                else:
                    print(
                        "\a",
                        end="",
                        flush=True,
                    )
                    time.sleep(self.duration / 1000)

                time.sleep(0.08)
        finally:
            self.busy = False
