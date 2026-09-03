"""Proyek gabungan pemantauan pengemudi untuk contoh akhir CVGO."""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

from ._validation import confidence, non_negative_number, positive_number
from .camera import Camera
from .face import FaceLandmarks, LandmarkFace
from .metrics import (
    LEFT_EYE,
    RIGHT_EYE,
    eye_ratio,
    pitch_ratio,
    single_eye_ratio,
    yaw_ratio,
)
from .serial_io import Serial
from .sound import Alarm
from .timing import FPS, Smoother


BIT_DROWSY = 0x1
BIT_LOOKING_AWAY = 0x2
BIT_HEAD_DOWN = 0x4
BIT_FACE_MISSING = 0x8


@dataclass
class EyeConfig:
    closed_threshold: float = 0.20
    open_threshold: float = 0.24
    alert_after: float = 1.5
    smoothing: float = 0.45

    def __post_init__(self) -> None:
        self.closed_threshold = non_negative_number(
            "closed_threshold",
            self.closed_threshold,
        )
        self.open_threshold = non_negative_number(
            "open_threshold",
            self.open_threshold,
        )
        self.alert_after = non_negative_number("alert_after", self.alert_after)
        self.smoothing = positive_number("smoothing", self.smoothing)
        if self.smoothing > 1:
            raise ValueError("smoothing harus maksimal 1")
        if self.open_threshold < self.closed_threshold:
            raise ValueError(
                "open_threshold tidak boleh lebih kecil dari closed_threshold"
            )


@dataclass
class HeadConfig:
    yaw_normal: float = 0.50
    turn_threshold: float = 0.12
    turn_release: float = 0.07
    turn_alert_after: float = 0.7
    pitch_normal: float = 0.50
    down_threshold: float = 0.055
    down_release: float = 0.030
    down_alert_after: float = 0.7

    def __post_init__(self) -> None:
        self.yaw_normal = confidence("yaw_normal", self.yaw_normal)
        self.pitch_normal = confidence("pitch_normal", self.pitch_normal)
        for name in (
            "turn_threshold",
            "turn_release",
            "turn_alert_after",
            "down_threshold",
            "down_release",
            "down_alert_after",
        ):
            setattr(self, name, non_negative_number(name, getattr(self, name)))
        if self.turn_release > self.turn_threshold:
            raise ValueError("turn_release harus <= turn_threshold")
        if self.down_release > self.down_threshold:
            raise ValueError("down_release harus <= down_threshold")


@dataclass
class FaceConfig:
    missing_alert_after: float = 2.0

    def __post_init__(self) -> None:
        self.missing_alert_after = non_negative_number(
            "missing_alert_after",
            self.missing_alert_after,
        )


@dataclass
class MonitorResult:
    """Hasil satu frame. Semua nilai tetap tersedia untuk logika custom."""

    frame: Any
    face_found: bool
    ear: float | None = None
    yaw: float | None = None
    pitch: float | None = None
    yaw_offset: float = 0.0
    pitch_offset: float = 0.0
    eyes_closed: bool = False
    drowsy: bool = False
    looking_away: bool = False
    look_direction: str | None = None
    head_down: bool = False
    face_missing: bool = False
    eye_duration: float = 0.0
    turn_duration: float = 0.0
    down_duration: float = 0.0
    missing_duration: float = 0.0
    fps: float = 0.0
    mask: int = 0
    landmarks: LandmarkFace | None = None

    @property
    def looking_left(self) -> bool:
        return self.looking_away and self.look_direction == "left"

    @property
    def looking_right(self) -> bool:
        return self.looking_away and self.look_direction == "right"

    @property
    def alert(self) -> bool:
        return self.mask != 0

    @property
    def mask_hex(self) -> str:
        return f"{self.mask:X}"


@dataclass
class _TimedState:
    active: bool = False
    started_at: float | None = None

    def enter(self, now: float) -> None:
        if not self.active:
            self.active = True
            self.started_at = now

    def leave(self) -> None:
        self.active = False
        self.started_at = None

    def duration(self, now: float) -> float:
        if not self.active or self.started_at is None:
            return 0.0
        return now - self.started_at


class DriverMonitor:
    """Gabungan deteksi kantuk, arah kepala, wajah hilang, alarm, dan serial.

    Gunakan ``run()`` untuk mode cepat atau iterasikan objek ini untuk membuat
    logika sendiri. Konfigurasi publik tersedia lewat ``eyes``, ``head``, dan
    ``face``.
    """

    BIT_DROWSY = BIT_DROWSY
    BIT_LOOKING_AWAY = BIT_LOOKING_AWAY
    BIT_HEAD_DOWN = BIT_HEAD_DOWN
    BIT_FACE_MISSING = BIT_FACE_MISSING

    RIGHT_EYE = RIGHT_EYE
    LEFT_EYE = LEFT_EYE

    EVENTS = (
        "drowsy",
        "looking_away",
        "looking_left",
        "looking_right",
        "head_down",
        "face_missing",
        "normal",
    )

    def __init__(
        self,
        camera: int | str | Camera = 0,
        *,
        serial: bool | Serial = False,
        sound: bool = False,
        eyes: EyeConfig | None = None,
        head: HeadConfig | None = None,
        face: FaceConfig | None = None,
    ) -> None:
        self.camera = camera if isinstance(camera, Camera) else Camera(camera)
        self.serial = Serial.auto(connect=False) if serial is True else serial or None
        self.sound = sound
        self.eyes = eyes or EyeConfig()
        self.head = head or HeadConfig()
        self.face = face or FaceConfig()
        self.landmarker = FaceLandmarks(max_faces=1, refine=False)

        self._eye = _TimedState()
        self._turn = _TimedState()
        self._down = _TimedState()
        self._missing = _TimedState()
        self._ear_smoother = Smoother(self.eyes.smoothing)
        self._fps = FPS()
        self._alarm = Alarm()
        self._callbacks: dict[
            str,
            list[Callable[[MonitorResult], None]],
        ] = defaultdict(list)
        self._previous_events: set[str] = set()
        self._last_mask: int | None = None
        self._last_serial_send = 0.0
        self.serial_repeat_after = 0.5
        self.result: MonitorResult | None = None
        self._closed = False

    def on(
        self,
        event: str,
        callback: Callable[[MonitorResult], None] | None = None,
    ):
        """Daftarkan callback; bisa dipakai sebagai fungsi atau decorator."""
        if event not in self.EVENTS:
            choices = ", ".join(self.EVENTS)
            raise ValueError(
                f"Event tidak dikenal: {event}. Pilih: {choices}"
            )

        def register(func: Callable[[MonitorResult], None]):
            self._callbacks[event].append(func)
            return func

        return register(callback) if callback is not None else register

    @classmethod
    def calculate_ear(cls, face: LandmarkFace, indices: tuple[int, ...]) -> float:
        return single_eye_ratio(
            face,
            indices,
        )

    @classmethod
    def calculate_yaw(cls, face: LandmarkFace) -> float:
        return yaw_ratio(face)

    @classmethod
    def calculate_pitch(cls, face: LandmarkFace) -> float:
        return pitch_ratio(face)

    def _reset_face_states(self) -> None:
        self._eye.leave()
        self._turn.leave()
        self._down.leave()
        self._ear_smoother.reset()

    def process(self, frame, *, now: float | None = None) -> MonitorResult:
        """Proses satu frame tanpa mengambil frame dari kamera."""
        now = time.monotonic() if now is None else now
        faces = self.landmarker.detect(frame)
        fps = self._fps.update(now=now)

        if not faces:
            if not self._missing.active:
                self._missing.enter(now)
                self._reset_face_states()
            duration = self._missing.duration(now)
            missing = duration >= self.face.missing_alert_after
            mask = self.BIT_FACE_MISSING if missing else 0
            result = MonitorResult(
                frame=frame,
                face_found=False,
                face_missing=missing,
                missing_duration=duration,
                fps=fps,
                mask=mask,
            )
            self._after_process(result, now)
            return result

        self._missing.leave()
        landmark_face = faces[0]

        ear = self._ear_smoother.update(
            eye_ratio(landmark_face),
        )

        yaw = yaw_ratio(landmark_face)
        pitch = pitch_ratio(landmark_face)
        yaw_offset = yaw - self.head.yaw_normal
        pitch_offset = pitch - self.head.pitch_normal

        if not self._eye.active and ear < self.eyes.closed_threshold:
            self._eye.enter(now)
        elif self._eye.active and ear > self.eyes.open_threshold:
            self._eye.leave()

        if not self._turn.active and abs(yaw_offset) > self.head.turn_threshold:
            self._turn.enter(now)
        elif self._turn.active and abs(yaw_offset) < self.head.turn_release:
            self._turn.leave()

        if not self._down.active and pitch_offset > self.head.down_threshold:
            self._down.enter(now)
        elif self._down.active and pitch_offset < self.head.down_release:
            self._down.leave()

        eye_duration = self._eye.duration(now)
        turn_duration = self._turn.duration(now)
        down_duration = self._down.duration(now)
        drowsy = self._eye.active and eye_duration >= self.eyes.alert_after
        looking_away = self._turn.active and turn_duration >= self.head.turn_alert_after
        head_down = self._down.active and down_duration >= self.head.down_alert_after
        direction = "right" if yaw_offset > 0 else "left"

        mask = 0
        if drowsy:
            mask |= self.BIT_DROWSY
        if looking_away:
            mask |= self.BIT_LOOKING_AWAY
        if head_down:
            mask |= self.BIT_HEAD_DOWN

        result = MonitorResult(
            frame=frame,
            face_found=True,
            ear=ear,
            yaw=yaw,
            pitch=pitch,
            yaw_offset=yaw_offset,
            pitch_offset=pitch_offset,
            eyes_closed=self._eye.active,
            drowsy=drowsy,
            looking_away=looking_away,
            look_direction=direction if self._turn.active else None,
            head_down=head_down,
            eye_duration=eye_duration,
            turn_duration=turn_duration,
            down_duration=down_duration,
            fps=fps,
            mask=mask,
            landmarks=landmark_face,
        )
        self._after_process(result, now)
        return result

    def read(self) -> MonitorResult | None:
        """Ambil dan proses satu frame dari kamera.

        Menghasilkan ``None`` jika frame tidak berhasil dibaca.
        """
        frame = self.camera.read()
        if frame is None:
            return None
        return self.process(frame)

    def show(
        self,
        result: MonitorResult,
        *,
        title: str = "CVGO Driver Monitor",
        draw_landmarks: bool = True,
        landmark_style: str = "contours",
        quit_key: str = "q",
    ) -> bool:
        """Tampilkan hasil Driver Monitor pada jendela OpenCV."""
        if draw_landmarks and result.landmarks is not None:
            result.landmarks.draw(
                result.frame,
                style=landmark_style,
            )

        return self.camera.show(
            result.frame,
            title=title,
            quit_key=quit_key,
        )

    def _after_process(self, result: MonitorResult, now: float) -> None:
        self.result = result
        events: set[str] = set()
        if result.drowsy:
            events.add("drowsy")
        if result.looking_away:
            events.add("looking_away")
            events.add("looking_right" if result.looking_right else "looking_left")
        if result.head_down:
            events.add("head_down")
        if result.face_missing:
            events.add("face_missing")
        if not events:
            events.add("normal")

        for event in events - self._previous_events:
            for callback in self._callbacks[event]:
                callback(result)
        self._previous_events = events

        if self.serial is not None:
            changed = result.mask != self._last_mask
            repeat = now - self._last_serial_send >= self.serial_repeat_after
            if changed or repeat:
                if self.serial.send(result.mask_hex):
                    self._last_mask = result.mask
                    self._last_serial_send = now

        if self.sound:
            self._alarm.trigger(result.alert)

    def beep(self) -> None:
        self._alarm.trigger()

    def frames(self) -> Iterator[MonitorResult]:
        try:
            for frame in self.camera:
                yield self.process(frame)
        finally:
            self.close()

    def __iter__(self) -> Iterator[MonitorResult]:
        return self.frames()

    def run(
        self,
        *,
        show: bool = False,
        draw_landmarks: bool = False,
        print_status: bool = True,
        quit_key: str = "q",
    ) -> None:
        """Mode cepat. Tekan ``q`` jika tampilan kamera diaktifkan."""
        last_print = 0.0
        for result in self:
            now = time.monotonic()
            if print_status and now - last_print >= 0.5:
                ear = "-" if result.ear is None else f"{result.ear:.3f}"
                print(
                    f"face={result.face_found} | ear={ear} | "
                    f"fps={result.fps:.1f} | mask={result.mask_hex}"
                )
                last_print = now

            if draw_landmarks and result.landmarks is not None:
                result.landmarks.draw(result.frame)
            if show:
                keep_running = self.camera.show(
                    result.frame,
                    title="CVGO Driver Monitor",
                    quit_key=quit_key,
                )
                if not keep_running:
                    break

    def close(self) -> None:
        if self._closed:
            return

        self.camera.close()
        self.landmarker.close()
        if self.serial is not None:
            if self.serial.connected:
                self.serial.send("0")
            self.serial.close()

        self._closed = True

    def __enter__(self) -> "DriverMonitor":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
