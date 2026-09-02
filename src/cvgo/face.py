"""Deteksi wajah dan landmark berbasis MediaPipe Face Mesh."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class LandmarkPoint:
    """Satu titik landmark dalam koordinat normal 0–1."""

    x: float
    y: float
    z: float
    visibility: float | None = None
    presence: float | None = None

    def pixel(self, frame_or_size) -> tuple[int, int]:
        if hasattr(frame_or_size, "shape"):
            height, width = frame_or_size.shape[:2]
        else:
            width, height = frame_or_size
        return int(self.x * width), int(self.y * height)


class LandmarkFace:
    """Landmark untuk satu wajah."""

    def __init__(
        self,
        raw_face: Any,
        owner: "FaceLandmarks",
        frame_size: tuple[int, int],
    ) -> None:
        self.raw = raw_face
        self._owner = owner
        self.width, self.height = frame_size
        self.points: tuple[LandmarkPoint, ...] = tuple(
            LandmarkPoint(p.x, p.y, p.z) for p in raw_face.landmark
        )

    def __len__(self) -> int:
        return len(self.points)

    def __getitem__(self, index: int) -> LandmarkPoint:
        return self.points[index]

    def point(self, index: int) -> LandmarkPoint:
        return self.points[index]

    def box(self, frame, *, padding: int = 10) -> "FaceBox":
        height, width = frame.shape[:2]
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        x1 = max(0, int(min(xs) * width) - padding)
        y1 = max(0, int(min(ys) * height) - padding)
        x2 = min(width - 1, int(max(xs) * width) + padding)
        y2 = min(height - 1, int(max(ys) * height) + padding)
        return FaceBox(x1, y1, x2 - x1, y2 - y1)

    def draw(
        self,
        frame,
        *,
        style: str = "contours",
        color: tuple[int, int, int] = (0, 255, 0),
        thickness: int = 1,
        radius: int = 1,
    ):
        """Gambar landmark langsung pada frame dan kembalikan frame yang sama."""
        self._owner.draw(
            frame,
            self,
            style=style,
            color=color,
            thickness=thickness,
            radius=radius,
        )
        return frame


@dataclass(frozen=True)
class FaceBox:
    x: int
    y: int
    width: int
    height: int
    confidence: float = 1.0

    @property
    def xyxy(self) -> tuple[int, int, int, int]:
        return self.x, self.y, self.x + self.width, self.y + self.height

    def draw(
        self,
        frame,
        *,
        color: tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
        label: str | None = "Face",
    ):
        try:
            import cv2
        except ImportError as exc:
            raise ImportError("OpenCV belum terpasang.") from exc
        x1, y1, x2, y2 = self.xyxy
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
        if label:
            cv2.putText(
                frame,
                label,
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                thickness,
                cv2.LINE_AA,
            )
        return frame


class FaceLandmarks:
    """Detektor landmark wajah yang tetap membuka akses ke hasil mentah."""

    def __init__(
        self,
        *,
        max_faces: int = 1,
        refine: bool = False,
        detection_confidence: float = 0.5,
        tracking_confidence: float = 0.5,
    ) -> None:
        try:
            import mediapipe as mp
        except ImportError as exc:
            raise ImportError(
                "MediaPipe belum terpasang. Jalankan: pip install mediapipe"
            ) from exc

        self.mp = mp
        self.model = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=max_faces,
            refine_landmarks=refine,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.raw_result: Any | None = None
        self._closed = False

    def detect(self, frame) -> list[LandmarkFace]:
        try:
            import cv2
        except ImportError as exc:
            raise ImportError("OpenCV belum terpasang.") from exc

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        self.raw_result = self.model.process(rgb)
        raw_faces: Sequence[Any] = self.raw_result.multi_face_landmarks or ()
        height, width = frame.shape[:2]
        return [
            LandmarkFace(
                face,
                self,
                (width, height),
            )
            for face in raw_faces
        ]

    def draw(
        self,
        frame,
        face: LandmarkFace,
        *,
        style: str = "contours",
        color: tuple[int, int, int] = (0, 255, 0),
        thickness: int = 1,
        radius: int = 1,
    ) -> None:
        mesh = self.mp.solutions.face_mesh
        connections = {
            "contours": mesh.FACEMESH_CONTOURS,
            "tesselation": mesh.FACEMESH_TESSELATION,
            "iris": mesh.FACEMESH_IRISES,
        }
        if style == "all":
            connections = mesh.FACEMESH_TESSELATION
        elif style not in connections:
            raise ValueError("style harus: contours, tesselation, iris, atau all")
        else:
            connections = connections[style]

        spec = self.mp.solutions.drawing_utils.DrawingSpec(
            color=color,
            thickness=thickness,
            circle_radius=radius,
        )
        self.mp.solutions.drawing_utils.draw_landmarks(
            image=frame,
            landmark_list=face.raw,
            connections=connections,
            landmark_drawing_spec=spec,
            connection_drawing_spec=spec,
        )

    def close(self) -> None:
        if not self._closed:
            self.model.close()
            self._closed = True

    def __enter__(self) -> "FaceLandmarks":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()


class FaceDetector:
    """Deteksi kotak wajah dengan mesin landmark yang sama."""

    def __init__(self, *, max_faces: int = 1, padding: int = 10, **kwargs) -> None:
        self.padding = padding
        self.landmarks = FaceLandmarks(max_faces=max_faces, **kwargs)
        self.faces: list[LandmarkFace] = []

    def detect(self, frame) -> list[FaceBox]:
        self.faces = self.landmarks.detect(frame)
        return [face.box(frame, padding=self.padding) for face in self.faces]

    @property
    def raw_result(self):
        return self.landmarks.raw_result

    def close(self) -> None:
        self.landmarks.close()

    def __enter__(self) -> "FaceDetector":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
