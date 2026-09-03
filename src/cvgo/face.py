"""Deteksi wajah dan landmark berbasis MediaPipe Face Mesh."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from ._validation import (
    boolean,
    choice,
    confidence,
    non_negative_int,
    positive_int,
)
from .geometry import BoundingBox


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

    def box(self, frame=None, *, padding: int = 10) -> "FaceBox":
        padding = non_negative_int("padding", padding)
        if frame is None:
            width, height = self.width, self.height
        else:
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
class FaceBox(BoundingBox):
    confidence: float = 1.0

    def draw(
        self,
        frame,
        *,
        color: tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
        label: str | None = "Face",
    ):
        return super().draw(
            frame,
            color=color,
            thickness=thickness,
            label=label,
        )


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
        max_faces = positive_int("max_faces", max_faces)
        refine = boolean("refine", refine)
        detection_confidence = confidence(
            "detection_confidence",
            detection_confidence,
        )
        tracking_confidence = confidence(
            "tracking_confidence",
            tracking_confidence,
        )
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
    """Deteksi kotak wajah dengan mesin cepat sebagai default.

    ``engine="fast"`` memakai MediaPipe Face Detection. Pilih ``engine="mesh"``
    bila aplikasi juga membutuhkan kompatibilitas hasil Face Mesh lama.
    ``engine="auto"`` memilih mesh hanya saat opsi khusus mesh digunakan.
    """

    def __init__(
        self,
        *,
        max_faces: int = 1,
        padding: int = 10,
        model: int = 0,
        detection_confidence: float = 0.5,
        engine: str = "auto",
        refine: bool = False,
        tracking_confidence: float = 0.5,
    ) -> None:
        max_faces = positive_int("max_faces", max_faces)
        padding = non_negative_int("padding", padding)
        model = choice("model", model, (0, 1))
        detection_confidence = confidence(
            "detection_confidence",
            detection_confidence,
        )
        engine = choice("engine", engine, ("auto", "fast", "mesh"))
        refine = boolean("refine", refine)
        tracking_confidence = confidence(
            "tracking_confidence",
            tracking_confidence,
        )

        mesh_options_used = refine or tracking_confidence != 0.5
        if engine == "auto":
            engine = "mesh" if mesh_options_used else "fast"
        elif engine == "fast" and mesh_options_used:
            raise ValueError(
                "refine dan tracking_confidence hanya tersedia pada engine='mesh'"
            )

        self.engine = engine
        self.max_faces = max_faces
        self.padding = padding
        self.model_selection = model
        self.faces: list[LandmarkFace] = []
        self.landmarks: FaceLandmarks | None = None
        self.model: Any | None = None
        self._raw_result: Any | None = None
        self._closed = False

        if self.engine == "mesh":
            self.landmarks = FaceLandmarks(
                max_faces=max_faces,
                refine=refine,
                detection_confidence=detection_confidence,
                tracking_confidence=tracking_confidence,
            )
            self.model = self.landmarks.model
            return

        try:
            import mediapipe as mp
        except ImportError as exc:
            raise ImportError(
                "MediaPipe belum terpasang. Jalankan: pip install mediapipe"
            ) from exc

        self.mp = mp
        self.model = mp.solutions.face_detection.FaceDetection(
            model_selection=model,
            min_detection_confidence=detection_confidence,
        )

    def detect(self, frame) -> list[FaceBox]:
        if self._closed:
            raise RuntimeError("FaceDetector sudah ditutup")

        if self.engine == "mesh":
            self.faces = self.landmarks.detect(frame)
            return [face.box(frame, padding=self.padding) for face in self.faces]

        try:
            import cv2
        except ImportError as exc:
            raise ImportError("OpenCV belum terpasang.") from exc

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        self._raw_result = self.model.process(rgb)
        height, width = frame.shape[:2]
        boxes = []

        for detection in self._raw_result.detections or ():
            relative = detection.location_data.relative_bounding_box
            x1 = min(
                width - 1,
                max(0, int(relative.xmin * width) - self.padding),
            )
            y1 = min(
                height - 1,
                max(0, int(relative.ymin * height) - self.padding),
            )
            x2 = min(
                width - 1,
                int((relative.xmin + relative.width) * width) + self.padding,
            )
            y2 = min(
                height - 1,
                int((relative.ymin + relative.height) * height) + self.padding,
            )
            score = detection.score[0] if detection.score else 0.0
            boxes.append(
                FaceBox(
                    x1,
                    y1,
                    max(0, x2 - x1),
                    max(0, y2 - y1),
                    float(score),
                )
            )

        return boxes[: self.max_faces]

    @property
    def raw_result(self):
        if self.engine == "mesh":
            return self.landmarks.raw_result
        return self._raw_result

    def close(self) -> None:
        if self._closed:
            return
        if self.landmarks is not None:
            self.landmarks.close()
        elif self.model is not None:
            self.model.close()
        self._closed = True

    def __enter__(self) -> "FaceDetector":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
