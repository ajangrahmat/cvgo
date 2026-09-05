# Changelog

All notable changes to CVGO are documented here.

## 0.3.0

- Added optional `MqttClient` and `WebSocketClient` integrations for robotics,
  device messaging, and real-time dashboards.
- Added JSON payload support, reconnect handling, async sending, subscriptions,
  receive operations, and context-manager lifecycle support for connectivity
  clients.

## 0.2.1

- Made `FaceDetector` use lightweight MediaPipe Face Detection by default while
  retaining a compatible `engine="mesh"` path for landmark-based behavior.
- Added confidence values to fast face boxes and near-range/full-range model
  selection.
- Added non-blocking `send_async()` serial output and
  `send_message_async()` / `send_photo_async()` Telegram queues.
- Added configurable serial `settle_time` for boards that do or do not reset
  when their port opens.
- Added `python -m cvgo check`, optional camera diagnostics, and JSON output for
  Windows, Linux, and AArch64/Armbian troubleshooting.
- Added SHA-256 verification for the pinned EfficientDet-Lite0 and Gesture
  Recognizer model downloads.
- Centralized package version and HTTP User-Agent values and expanded public
  parameter validation.
- Added Python 3.10–3.12 CI, release checks, tests, and updated documentation.

## 0.2.0

- Added the shared `BoundingBox` API with `xyxy`, `center`, `area`, and
  `draw()`.
- Added `PoseBox`, `Pose.box()`, and aggregate pose confidence.
- Added direct `box()`, `handedness`, and `points` access to gesture results.
- Allowed `LandmarkFace.box()` to use the frame size stored in its result.
- Made empty `HolisticResult` objects evaluate as false.
- Updated pose security to use Pose Lite and a person bounding box without
  drawing a skeleton.
- Added complete GUI and terminal examples to the documentation page.
- Added `image`, `video`, and asynchronous `live` modes to object detection and
  gesture recognition while preserving the legacy `stream` argument.

## 0.1.1

- Initial public release of CVGO.
