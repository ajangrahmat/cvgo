"""CVGO — Simple Computer Vision for Python."""

from importlib.metadata import PackageNotFoundError, version

from .camera import Camera
from .drawing import put_text
from .driver import (
    BIT_DROWSY,
    BIT_FACE_MISSING,
    BIT_HEAD_DOWN,
    BIT_LOOKING_AWAY,
    DriverMonitor,
    EyeConfig,
    FaceConfig,
    HeadConfig,
    MonitorResult,
)
from .face import FaceBox, FaceDetector, FaceLandmarks, LandmarkFace, LandmarkPoint
from .gesture import Gesture, GestureRecognizer
from .hand import Hand, HandBox, HandLandmark, HandTracker
from .holistic import HolisticResult, HolisticTracker
from .metrics import eye_ratio, pitch_ratio, yaw_ratio
from .models import download_model, model_cache_dir, model_path
from .object_detection import DetectedObject, ObjectBox, ObjectDetector
from .pose import Pose, PoseLandmark, PoseTracker
from .segmentation import SegmentationResult, SelfieSegmenter
from .serial_io import Serial
from .sound import Alarm
from .telegram import Telegram
from .timing import FPS, Smoother, Timer

__all__ = [
    "Alarm",
    "BIT_DROWSY",
    "BIT_FACE_MISSING",
    "BIT_HEAD_DOWN",
    "BIT_LOOKING_AWAY",
    "Camera",
    "DetectedObject",
    "DriverMonitor",
    "EyeConfig",
    "FPS",
    "FaceBox",
    "FaceConfig",
    "FaceDetector",
    "FaceLandmarks",
    "Gesture",
    "GestureRecognizer",
    "HeadConfig",
    "Hand",
    "HandBox",
    "HandLandmark",
    "HandTracker",
    "HolisticResult",
    "HolisticTracker",
    "LandmarkFace",
    "LandmarkPoint",
    "MonitorResult",
    "ObjectBox",
    "ObjectDetector",
    "Pose",
    "PoseLandmark",
    "PoseTracker",
    "SegmentationResult",
    "Serial",
    "SelfieSegmenter",
    "Smoother",
    "Telegram",
    "Timer",
    "eye_ratio",
    "download_model",
    "model_cache_dir",
    "model_path",
    "pitch_ratio",
    "put_text",
    "yaw_ratio",
]

try:
    __version__ = version("cvgo")
except PackageNotFoundError:  # Saat source dijalankan tanpa instalasi.
    __version__ = "0.1.1"
