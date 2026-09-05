"""CVGO — Simple Computer Vision for Python."""

from ._version import __version__

from .camera import Camera
from .drawing import put_text
from .diagnostics import check_camera, system_info
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
from .geometry import BoundingBox
from .hand import Hand, HandBox, HandLandmark, HandTracker
from .holistic import HolisticResult, HolisticTracker
from .metrics import eye_ratio, pitch_ratio, yaw_ratio
from .models import download_model, model_cache_dir, model_path
from .mqtt import MqttClient
from .object_detection import DetectedObject, ObjectBox, ObjectDetector
from .pose import Pose, PoseBox, PoseLandmark, PoseTracker
from .segmentation import SegmentationResult, SelfieSegmenter
from .serial_io import Serial
from .sound import Alarm
from .telegram import Telegram
from .timing import FPS, Smoother, Timer
from .websocket import WebSocketClient

__all__ = [
    "Alarm",
    "BIT_DROWSY",
    "BIT_FACE_MISSING",
    "BIT_HEAD_DOWN",
    "BIT_LOOKING_AWAY",
    "BoundingBox",
    "Camera",
    "check_camera",
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
    "MqttClient",
    "ObjectBox",
    "ObjectDetector",
    "Pose",
    "PoseBox",
    "PoseLandmark",
    "PoseTracker",
    "SegmentationResult",
    "Serial",
    "SelfieSegmenter",
    "Smoother",
    "system_info",
    "Telegram",
    "Timer",
    "WebSocketClient",
    "eye_ratio",
    "download_model",
    "model_cache_dir",
    "model_path",
    "pitch_ratio",
    "put_text",
    "yaw_ratio",
]
