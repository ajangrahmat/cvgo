<p align="center">
    <img src="logo-cvgo.png" alt="CVGO" width="520">
</p>

<h1 align="center">CVGO</h1>

<p align="center"><strong>Simple Computer Vision for Python</strong></p>

<p align="center">
    <a href="https://kelasrobot.com">Homepage</a> ·
    <a href="examples/">Examples</a> ·
    <a href="CHANGELOG.md">Changelog</a> ·
    <a href="LICENSE">MIT License</a>
</p>

CVGO simplifies the repetitive parts of OpenCV and MediaPipe while keeping the
main program flow visible. Users still write `while True`, read frames, inspect
detection results, make decisions, and display the GUI.

> Simple by default, customizable when needed.

## Installation

Install CVGO from PyPI:

```bash
pip install cvgo
```

CVGO 0.2 pins the core versions that have been tested:

| Package | Version |
|---|---|
| CVGO | `0.2.1` |
| OpenCV Contrib | `4.11.0.86` |
| NumPy | `1.26.4` |
| MediaPipe | `0.10.21` |

The OpenCV package used is `opencv-contrib-python` to avoid installing two
separate `cv2` variants alongside MediaPipe dependencies.

Use Python 3.10, 3.11, or 3.12.

Check the installed stack, and optionally test camera `4`:

```bash
python -m cvgo check
python -m cvgo check --camera 4
```

It is recommended to install CVGO in a dedicated virtual environment:

```powershell
py -3.11 -m venv .venv-cvgo
.venv-cvgo\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install cvgo
```

In a new virtual environment, `pip` installs dependencies once. If the
installation command is run again in the same environment, matching packages are
reported as `Requirement already satisfied`.

Do not install `opencv-python`, `opencv-python-headless`, or other OpenCV
variants alongside `opencv-contrib-python`. They all provide the same `cv2`
module.

`ObjectDetector` and `GestureRecognizer` use official MediaPipe models that are
downloaded automatically on first use. The computer only needs internet access
for the first download; afterward, the model is reused from cache.

## Import

```python
import cvgo as go
```

All components can also be imported directly:

```python
from cvgo import Camera, ObjectDetector, Telegram
```

## CVGO 0.2 Features

| Feature | Main API | Output |
|---|---|---|
| Camera and GUI | `Camera` | OpenCV frames |
| Face detection | `FaceDetector` | Fast face boxes with confidence |
| Face landmarks | `FaceLandmarks` | Face landmarks and metrics |
| Hand tracking | `HandTracker` | 21 landmarks per hand |
| Pose tracking | `PoseTracker` | 33 landmarks and a person box |
| Holistic tracking | `HolisticTracker` | Face, pose, and both hands |
| Gesture | `GestureRecognizer` | Gesture, score, landmarks, and task modes |
| Object detection | `ObjectDetector` | Labels, boxes, and image/video/live modes |
| Human segmentation | `SelfieSegmenter` | Human mask and background |
| Driver monitor | Modular components | Drowsiness, head direction, and alarms |
| Arduino | `Serial` | Serial communication, sync or queued |
| Telegram | `Telegram` | Text and photos, sync or non-blocking |
| Shared geometry | `BoundingBox` | Coordinates, center, area, and drawing |

This is the full coverage of CVGO 0.2 for camera and learning projects.
MediaPipe features outside this scope can still be added in later versions without
changing the main API pattern.

## Python Naming Style

CVGO follows common Python naming conventions (PEP 8):

- classes use `PascalCase`: `HandTracker`, `PoseTracker`;
- functions and methods use `snake_case`: `read_fps()`, `put_text()`;
- constants use `UPPER_CASE`: `BIT_DROWSY`, `LEFT_WRIST`.

So use `read_fps()`, not `readFPS()`. Since the object is already named `FPS`,
the shortest form is `fps.read()`. `fps.read_fps()` remains available as a more
explicit alias.

## Simple Defaults

```python
camera = go.Camera()
faces = go.FaceDetector()
landmarks = go.FaceLandmarks()
hands = go.HandTracker()
pose = go.PoseTracker()
objects = go.ObjectDetector()
arduino = go.Serial()
timer = go.Timer()
```

Main defaults:

| Component | Default |
|---|---|
| `Camera()` | Camera `0` |
| `FaceDetector()` | Fast engine, maximum one face |
| `FaceLandmarks()` | Maximum one face |
| `HandTracker()` | Maximum two hands |
| `PoseTracker()` | One main pose |
| `HolisticTracker()` | One main person, 543 landmarks |
| `GestureRecognizer()` | Video mode, maximum two hands |
| `ObjectDetector()` | Video mode, 10 objects, confidence `0.5` |
| `SelfieSegmenter()` | Landscape model for webcams |
| `Serial()` | Automatic port, `9600` baud |
| `Telegram()` | Environment-based configuration, 30-second cooldown |
| `Timer()` | One-second duration |
| `Smoother()` | Alpha `0.45` |

Only set parameters when you want to change the default behavior:

```python
camera = go.Camera(1, width=1280, height=720)
arduino = go.Serial("COM5", baud=115200)
timer = go.Timer(1.5)
hands = go.HandTracker(max_hands=1, detection_confidence=0.7)
pose = go.PoseTracker(model_complexity=0)
objects = go.ObjectDetector(confidence=0.7, allow=["person"])
telegram = go.Telegram(cooldown=60)
```

## Advanced Parameter Guide

The complete examples intentionally start with simple defaults. For advanced
projects, add only the parameters that need to change; the remaining parameters
keep their defaults.

```python
camera = go.Camera()  # All defaults
camera = go.Camera(4)  # Change only the camera source
camera = go.Camera(4, width=1280, height=720, fps=30)
```

Parameters written after `*` in the signatures below are keyword-only. Write
their names explicitly, such as `width=1280`, so the code remains readable.

Common rules:

| Value | Meaning |
|---|---|
| Confidence | A value from `0.0` to `1.0`; higher is stricter |
| OpenCV color | BGR order, for example green is `(0, 255, 0)` |
| `None` | Let CVGO, OpenCV, or the operating system use its default |
| `static=True` | Optimize for unrelated still images instead of sequential frames |
| `mode="live"` | Keep a camera loop responsive using asynchronous task results |

### Camera and Drawing Parameters

`go.Camera(source=0, *, width=None, height=None, fps=None, backend=None)`

| Parameter | Default | Description |
|---|---|---|
| `source` | `0` | Camera index, video path, or stream URL |
| `width` | `None` | Requested capture width in pixels |
| `height` | `None` | Requested capture height in pixels |
| `fps` | `None` | Requested camera frame rate |
| `backend` | `None` | OpenCV backend; `None` uses `cv2.CAP_ANY` |

Camera resolution and FPS are requests. The camera driver can select the nearest
supported value. After the camera opens, inspect `camera.size` or use the raw
`camera.capture` object for other OpenCV properties.

`camera.show(frame, *, title="CVGO", delay=1, quit_key="q")`

| Parameter | Default | Description |
|---|---|---|
| `title` | `"CVGO"` | Window title |
| `delay` | `1` | `cv2.waitKey` delay in milliseconds |
| `quit_key` | `"q"` | One keyboard character that closes the loop |

`camera.close(windows=True)` releases capture. Set `windows=False` in a purely
headless process when no OpenCV GUI windows should be destroyed.

`go.put_text(frame, text, position=(20, 35), *, color=(0, 255, 0), scale=0.7, thickness=2, background=False)`

| Parameter | Default | Description |
|---|---|---|
| `position` | `(20, 35)` | Text origin in pixels |
| `color` | `(0, 255, 0)` | Text color in BGR |
| `scale` | `0.7` | OpenCV font scale |
| `thickness` | `2` | Text stroke width |
| `background` | `False` | Draw a black background behind the text |

All shared boxes also accept `color=(0, 255, 0)`, `thickness=2`, and
`label=None` in `box.draw()`. Face, hand, and pose boxes provide the default
labels `"Face"`, `"Hand"`, and `"Person"`.

```python
camera = go.Camera(1, width=1280, height=720, fps=30)

go.put_text(
    frame,
    "Security active",
    color=(0, 255, 255),
    background=True,
)
camera.show(frame, title="Security Camera", quit_key="x")
```

### Face Parameters

`go.FaceDetector(*, max_faces=1, padding=10, model=0, detection_confidence=0.5, engine="auto", refine=False, tracking_confidence=0.5)`

`go.FaceLandmarks(*, max_faces=1, refine=False, detection_confidence=0.5, tracking_confidence=0.5)`

| Parameter | Default | Description |
|---|---|---|
| `max_faces` | `1` | Maximum faces returned per frame |
| `padding` | `10` | Extra pixels around a `FaceDetector` box |
| `model` | `0` | Fast model: `0` for near-range or `1` for full-range faces |
| `engine` | `"auto"` | Select `auto`, `fast`, or Face Mesh-compatible `mesh` |
| `refine` | `False` | Refine eye and lip landmarks and add iris landmarks |
| `detection_confidence` | `0.5` | Minimum confidence for the initial face detection |
| `tracking_confidence` | `0.5` | Minimum confidence for landmark tracking |

The default `auto` mode uses MediaPipe Face Detection, which is lighter than
running every Face Mesh landmark just to calculate a box. It automatically keeps
the legacy mesh engine when `refine=True` or a custom `tracking_confidence` is
used. Choose `engine="mesh"` explicitly when that behavior is required.
`detector.raw_result` remains available in both modes; `detector.faces` contains
landmark faces only in mesh mode.

| Result method | Parameter | Default | Description |
|---|---|---|---|
| `face.box()` | `padding` | `10` | Extra pixels around landmark bounds |
| `face.draw()` | `style` | `"contours"` | `contours`, `tesselation`, `iris`, or `all` |
| `face.draw()` | `color` | `(0, 255, 0)` | Landmark and connection color |
| `face.draw()` | `thickness` | `1` | Connection thickness |
| `face.draw()` | `radius` | `1` | Landmark radius |
| `FaceBox.draw()` | `color` | `(0, 255, 0)` | Box and label color |
| `FaceBox.draw()` | `thickness` | `2` | Box and label thickness |
| `FaceBox.draw()` | `label` | `"Face"` | Box label; use `None` to hide it |

Every fast `FaceBox` also exposes `confidence`. To tune only box detection:

```python
detector = go.FaceDetector(
    max_faces=2,
    detection_confidence=0.7,
    model=0,
)
```

```python
landmarker = go.FaceLandmarks(
    max_faces=2,
    refine=True,
    detection_confidence=0.7,
)

faces = landmarker.detect(frame)

for face in faces:
    face.draw(frame, style="tesselation", color=(255, 180, 0))
    face.box(padding=20).draw(frame, label="Tracked face")
```

### Hand Parameters

`go.HandTracker(*, max_hands=2, model_complexity=1, detection_confidence=0.5, tracking_confidence=0.5, static=False, mirrored=False)`

| Parameter | Default | Description |
|---|---|---|
| `max_hands` | `2` | Maximum hands returned per frame |
| `model_complexity` | `1` | `0` is lighter; `1` is more accurate |
| `detection_confidence` | `0.5` | Minimum confidence for hand detection |
| `tracking_confidence` | `0.5` | Minimum confidence for landmark tracking |
| `static` | `False` | Set `True` for independent still images |
| `mirrored` | `False` | Set `True` when the input frame was already flipped horizontally |

| Result method | Parameter | Default | Description |
|---|---|---|---|
| `hand.box()` | `padding` | `10` | Extra pixels around the hand |
| `hand.draw()` | `color` | `(0, 255, 0)` | Connection color |
| `hand.draw()` | `point_color` | `(255, 0, 255)` | Landmark color |
| `hand.draw()` | `thickness` | `2` | Connection thickness |
| `hand.draw()` | `radius` | `2` | Landmark radius |
| `HandBox.draw()` | `label` | `"Hand"` | Box label; use `None` to hide it |

```python
tracker = go.HandTracker(
    max_hands=1,
    model_complexity=0,
    detection_confidence=0.7,
)

hands = tracker.detect(frame)

for hand in hands:
    hand.draw(frame, color=(255, 200, 0), point_color=(0, 0, 255))
```

### Pose Parameters

`go.PoseTracker(*, model_complexity=1, detection_confidence=0.5, tracking_confidence=0.5, smooth=True, segmentation=False, static=False)`

| Parameter | Default | Description |
|---|---|---|
| `model_complexity` | `1` | `0` Lite, `1` Full, or `2` Heavy |
| `detection_confidence` | `0.5` | Minimum confidence for pose detection |
| `tracking_confidence` | `0.5` | Minimum confidence for landmark tracking |
| `smooth` | `True` | Smooth landmarks and an optional segmentation mask |
| `segmentation` | `False` | Also produce `pose.mask` |
| `static` | `False` | Set `True` for independent still images |

| Result method | Parameter | Default | Description |
|---|---|---|---|
| `pose.visible()` | `confidence` | `0.5` | Required landmark visibility |
| `pose.box()` | `padding` | `20` | Extra pixels around the visible body |
| `pose.box()` | `min_visibility` | `0.5` | Ignore weaker landmarks when building the box |
| `pose.draw()` | `color` | `(0, 255, 0)` | Skeleton connection color |
| `pose.draw()` | `point_color` | `(255, 0, 255)` | Landmark color |
| `pose.draw()` | `thickness` | `2` | Connection thickness |
| `pose.draw()` | `radius` | `2` | Landmark radius |
| `PoseBox.draw()` | `label` | `"Person"` | Box label; use `None` to hide it |

Use `model_complexity=0` for a lighter model on an STB or low-power board.

```python
tracker = go.PoseTracker(
    model_complexity=0,
    detection_confidence=0.6,
    segmentation=True,
)

pose = tracker.detect(frame)

if pose:
    pose.box(padding=30, min_visibility=0.6).draw(
        frame,
        label="Person",
    )
```

### Holistic Parameters

`go.HolisticTracker(*, model_complexity=1, detection_confidence=0.5, tracking_confidence=0.5, smooth=True, refine_face=False, segmentation=False, static=False)`

| Parameter | Default | Description |
|---|---|---|
| `model_complexity` | `1` | Pose model complexity: `0`, `1`, or `2` |
| `detection_confidence` | `0.5` | Minimum initial detection confidence |
| `tracking_confidence` | `0.5` | Minimum landmark tracking confidence |
| `smooth` | `True` | Smooth landmarks and an optional mask |
| `refine_face` | `False` | Refine face landmarks around the eyes and lips |
| `segmentation` | `False` | Also produce `result.mask` |
| `static` | `False` | Set `True` for independent still images |

`result.draw(frame, face=True, pose=True, hands=True)` lets each group be shown
or hidden independently. Each Boolean parameter defaults to `True`.

```python
tracker = go.HolisticTracker(model_complexity=0, refine_face=True)
result = tracker.detect(frame)

if result:
    result.draw(frame, face=False, pose=True, hands=True)
```

### Object Detection Parameters

`go.ObjectDetector(model_path=None, *, confidence=0.5, max_objects=10, allow=None, deny=None, locale="en", mode="video", stream=None, download=True)`

| Parameter | Default | Description |
|---|---|---|
| `model_path` | `None` | Path to a compatible custom `.tflite` model |
| `confidence` | `0.5` | Minimum object score |
| `max_objects` | `10` | Maximum results returned per frame |
| `allow` | `None` | Return only these labels, for example `["person"]` |
| `deny` | `None` | Exclude these labels |
| `locale` | `"en"` | Preferred display-name locale in model metadata |
| `mode` | `"video"` | `image`, `video`, or asynchronous `live` |
| `stream` | `None` | Legacy mode option; new code should use `mode` |
| `download` | `True` | Download the default model when it is not cached |

`allow` and `deny` cannot be used together. In `live` mode, `detect()` returns
the latest completed result and `detector.result_ready` reports whether the first
result has completed.

| Result method | Parameter | Default | Description |
|---|---|---|---|
| `item.draw()` | `color` | `(0, 255, 0)` | Box and label color |
| `item.draw()` | `thickness` | `2` | Box and label thickness |
| `item.draw()` | `show_score` | `True` | Include confidence in the label |

```python
detector = go.ObjectDetector(
    confidence=0.65,
    max_objects=3,
    allow=["person", "car"],
)
```

### Gesture Parameters

`go.GestureRecognizer(model_path=None, *, max_hands=2, gesture_confidence=0.5, detection_confidence=0.5, presence_confidence=0.5, tracking_confidence=0.5, mirrored=False, mode="video", stream=None, download=True)`

| Parameter | Default | Description |
|---|---|---|
| `model_path` | `None` | Path to a compatible custom `.task` model |
| `max_hands` | `2` | Maximum hands recognized per frame |
| `gesture_confidence` | `0.5` | Minimum score before a gesture is considered recognized |
| `detection_confidence` | `0.5` | Minimum hand detection confidence |
| `presence_confidence` | `0.5` | Minimum hand presence confidence |
| `tracking_confidence` | `0.5` | Minimum landmark tracking confidence |
| `mirrored` | `False` | Set `True` when the input frame was already flipped |
| `mode` | `"video"` | `image`, `video`, or asynchronous `live` |
| `stream` | `None` | Legacy mode option; new code should use `mode` |
| `download` | `True` | Download the default model when it is not cached |

| Result method | Parameter | Default | Description |
|---|---|---|---|
| `gesture.box()` | `padding` | `10` | Extra pixels around the gesture hand |
| `gesture.draw()` | `color` | `(0, 255, 0)` | Hand connections and box color |
| `gesture.draw()` | `point_color` | `(255, 0, 255)` | Hand landmark color |

```python
recognizer = go.GestureRecognizer(
    max_hands=1,
    gesture_confidence=0.7,
)
```

The task models can be prepared before an offline deployment:

```python
model = go.download_model(
    "gesture_recognizer",
    directory="models",
    timeout=180,
)
recognizer = go.GestureRecognizer(model)
```

| `download_model()` parameter | Default | Description |
|---|---|---|
| `name` | Required | `"object_detection"` or `"gesture_recognizer"` |
| `directory` | `None` | Custom download folder |
| `force` | `False` | Download again even when a valid model exists |
| `timeout` | `120.0` | Download timeout in seconds |

Set `CVGO_MODEL_DIR` to change the shared default model cache directory.
CVGO verifies the header and SHA-256 checksum of both pinned official models.
A damaged or incomplete cache file is downloaded again before it is used.

### Segmentation and Timing Parameters

| API | Parameter | Default | Description |
|---|---|---|---|
| `SelfieSegmenter()` | `model` | `1` | `0` general model; `1` landscape/webcam model |
| `result.foreground()` | `threshold` | `0.5` | Minimum mask value treated as foreground |
| `result.apply()` | `background` | `(0, 0, 0)` | BGR color or image with the same frame size |
| `result.apply()` | `threshold` | `0.5` | Foreground cutoff |
| `result.blur()` | `amount` | `35` | Gaussian blur kernel; even values are raised to the next odd value |
| `result.blur()` | `threshold` | `0.5` | Foreground cutoff |
| `Timer()` | `seconds` | `1.0` | Time a condition must stay true |
| `Smoother()` | `alpha` | `0.45` | EMA weight; lower is smoother, higher reacts faster |
| `FPS()` | `update_every` | `1.0` | Seconds between displayed FPS updates |

```python
segmenter = go.SelfieSegmenter(model=0)
timer = go.Timer(1.5)
smoother = go.Smoother(alpha=0.3)
fps = go.FPS(update_every=0.5)

result = segmenter.segment(frame)
frame = result.blur(frame, amount=51, threshold=0.6)
```

### Serial, Telegram, and Alarm Parameters

`go.Serial(port=None, *, baud=9600, timeout=1.0, reconnect_after=5.0, settle_time=2.0, newline=False, connect=True)`

| Parameter | Default | Description |
|---|---|---|
| `port` | `None` | Auto-detect a serial port; or use `COM5`, `/dev/ttyUSB0`, and so on |
| `baud` | `9600` | Serial baud rate; it must match the board |
| `timeout` | `1.0` | Serial read timeout in seconds |
| `reconnect_after` | `5.0` | Minimum delay between reconnect attempts |
| `settle_time` | `2.0` | Wait after a board resets on connect; use `0` when unnecessary |
| `newline` | `False` | Append `\n` to outgoing values |
| `connect` | `True` | Connect during construction |

Use `send(value)` when the result is needed immediately. In a camera loop,
`send_async(value)` queues the write on one background worker and returns a
`Future`. Call `close()` during cleanup; `close(wait=False)` cancels queued work.

`go.Telegram(token=None, chat_id=None, *, cooldown=30.0, timeout=15.0, silent=False, protect=False)`

| Parameter | Default | Description |
|---|---|---|
| `token` | Environment | Bot token or `CVGO_TELEGRAM_TOKEN` |
| `chat_id` | Environment | Target ID or `CVGO_TELEGRAM_CHAT_ID` |
| `cooldown` | `30.0` | Minimum seconds between messages with the same `key` |
| `timeout` | `15.0` | HTTP request timeout in seconds |
| `silent` | `False` | Send without a notification sound |
| `protect` | `False` | Ask Telegram to protect message content |

`telegram.send_message(text, *, key="message", force=False, silent=None, protect=None, parse_mode=None)`

| Parameter | Default | Description |
|---|---|---|
| `text` | Required | Message text, from 1 to 4096 characters |
| `key` | `"message"` | Independent cooldown name |
| `force` | `False` | Bypass cooldown intentionally |
| `silent` | `None` | Use the constructor setting, or override it |
| `protect` | `None` | Use the constructor setting, or override it |
| `parse_mode` | `None` | Telegram formatting mode such as `"HTML"` |

`telegram.send_photo(photo, caption="", *, key="photo", force=False, filename=None, quality=85, silent=None, protect=None, parse_mode=None)`

| Parameter | Default | Description |
|---|---|---|
| `photo` | Required | OpenCV frame, image bytes, or image path |
| `caption` | `""` | Caption up to 1024 characters |
| `key` | `"photo"` | Independent cooldown name |
| `force` | `False` | Bypass cooldown intentionally |
| `filename` | `None` | Optional uploaded filename |
| `quality` | `85` | JPEG quality from 1 to 100 for OpenCV frames |
| `silent` | `None` | Use the constructor setting, or override it |
| `protect` | `None` | Use the constructor setting, or override it |
| `parse_mode` | `None` | Telegram caption formatting mode |

`send_message_async()` and `send_photo_async()` accept the same parameters and
return a `Future[bool]`. They share one ordered background queue so a slow
network does not freeze frame capture. OpenCV frames are copied before being
queued. Call `telegram.close()` after the loop; its `wait=True` default finishes
queued sends first.

`go.Alarm(*, frequency=1500, duration=180, repeat=3, cooldown=0.8)`

| Parameter | Default | Description |
|---|---|---|
| `frequency` | `1500` | Beep frequency in Hz on Windows |
| `duration` | `180` | Length of each beep in milliseconds |
| `repeat` | `3` | Number of beeps per trigger |
| `cooldown` | `0.8` | Minimum seconds between alarm starts |

```python
arduino = go.Serial("/dev/ttyUSB0", baud=115200, newline=True)
telegram = go.Telegram(cooldown=60, silent=True)
alarm = go.Alarm(frequency=1800, repeat=2, cooldown=1.0)

arduino.send_async("1")
telegram.send_message_async("CVGO active")
```

### Advanced Driver Monitor Parameters

`DriverMonitor` groups its thresholds into small configuration objects. This
keeps the constructor readable and lets each part be calibrated separately.

| `EyeConfig` parameter | Default | Description |
|---|---|---|
| `closed_threshold` | `0.20` | Enter the closed-eye state below this EAR |
| `open_threshold` | `0.24` | Leave the closed-eye state above this EAR |
| `alert_after` | `1.5` | Closed-eye seconds before drowsiness is active |
| `smoothing` | `0.45` | EAR smoother alpha |

| `HeadConfig` parameter | Default | Description |
|---|---|---|
| `yaw_normal` | `0.50` | Calibrated straight-ahead yaw ratio |
| `turn_threshold` | `0.12` | Enter looking-away state beyond this offset |
| `turn_release` | `0.07` | Leave looking-away state below this offset |
| `turn_alert_after` | `0.7` | Looking-away seconds before an alert |
| `pitch_normal` | `0.50` | Calibrated upright pitch ratio |
| `down_threshold` | `0.055` | Enter head-down state beyond this offset |
| `down_release` | `0.030` | Leave head-down state below this offset |
| `down_alert_after` | `0.7` | Head-down seconds before an alert |

| Other parameter | Default | Description |
|---|---|---|
| `FaceConfig.missing_alert_after` | `2.0` | Missing-face seconds before an alert |
| `DriverMonitor.camera` | `0` | Camera index, path, URL, or a configured `Camera` object |
| `DriverMonitor.serial` | `False` | `True` for auto serial, or pass a `Serial` object |
| `DriverMonitor.sound` | `False` | Enable its built-in alarm |
| `serial_repeat_after` | `0.5` | Public attribute controlling repeated mask transmissions |

```python
eyes = go.EyeConfig(
    closed_threshold=0.22,
    open_threshold=0.26,
    alert_after=1.2,
)
head = go.HeadConfig(turn_threshold=0.10, down_threshold=0.05)
face = go.FaceConfig(missing_alert_after=3.0)

monitor = go.DriverMonitor(
    camera=go.Camera(4, width=640, height=480),
    serial=go.Serial("/dev/ttyUSB0", baud=115200),
    sound=True,
    eyes=eyes,
    head=head,
    face=face,
)
monitor.serial_repeat_after = 1.0
```

Available events for `monitor.on(...)` are `drowsy`, `looking_away`,
`looking_left`, `looking_right`, `head_down`, `face_missing`, and `normal`.
`MonitorResult` keeps the measured `ear`, `yaw`, `pitch`, durations, `fps`,
landmarks, alert booleans, numeric `mask`, and Arduino-ready `mask_hex` available
for fully custom logic.

| Method parameter | Default | Description |
|---|---|---|
| `show.title` | `"CVGO Driver Monitor"` | GUI window title |
| `show.draw_landmarks` | `True` | Draw face landmarks before showing |
| `show.landmark_style` | `"contours"` | Face drawing style |
| `show.quit_key` | `"q"` | GUI quit key |
| `run.show` | `False` | Enable a GUI window in shortcut mode |
| `run.draw_landmarks` | `False` | Draw landmarks in shortcut mode |
| `run.print_status` | `True` | Print status twice per second |
| `run.quit_key` | `"q"` | GUI quit key when `show=True` |

### Raw Results for Further Customization

CVGO does not lock advanced users into its helpers:

| Access | Raw object |
|---|---|
| `camera.capture` | OpenCV `VideoCapture` |
| `tracker.raw_result` | Latest raw MediaPipe result |
| `face.raw`, `hand.raw`, `pose.raw` | Raw MediaPipe landmarks |
| `item.raw`, `gesture.raw` | Raw MediaPipe Tasks result/category |
| `face.points`, `hand.points`, `pose.points` | Readable CVGO landmark points |

## Consistent Bounding Boxes

`FaceBox`, `HandBox`, `PoseBox`, and `ObjectBox` share the
`BoundingBox` API:

```python
box = pose.box()

print(box.xyxy)
print(box.center)
print(box.area)

box.draw(
    frame,
    label="Person",
)
```

Face and hand landmark results use the same pattern:

```python
face.box().draw(frame)
hand.box().draw(frame)
```

The original landmark points remain available, so padding, visibility, colors,
labels, and the surrounding project logic are still customizable.

## Camera

By default, CVGO leaves OpenCV to choose the best camera backend (`CAP_ANY`). A
custom backend can still be passed using the `backend` parameter.

```python
import cvgo as go


camera = go.Camera()

while True:
    frame = camera.read()

    if frame is None:
        break

    if not camera.show(frame):
        break

camera.close()
```

Press `q` to quit.

## Face Detection

```python
import cvgo as go


camera = go.Camera()
detector = go.FaceDetector()

while True:
    frame = camera.read()

    if frame is None:
        break

    faces = detector.detect(frame)

    for face in faces:
        face.draw(frame)

    if not camera.show(frame):
        break

camera.close()
detector.close()
```

## Face Landmarks and Metrics

```python
import cvgo as go


camera = go.Camera()
landmarker = go.FaceLandmarks()

while True:
    frame = camera.read()

    if frame is None:
        break

    faces = landmarker.detect(frame)

    if faces:
        face = faces[0]

        ear = go.eye_ratio(face)
        yaw = go.yaw_ratio(face)
        pitch = go.pitch_ratio(face)

        go.put_text(frame, f"EAR: {ear:.3f}")
        face.draw(frame)

    if not camera.show(frame):
        break

camera.close()
landmarker.close()
```

## Hand Tracking

```python
import cvgo as go


camera = go.Camera()
tracker = go.HandTracker()

while True:
    frame = camera.read()

    if frame is None:
        break

    hands = tracker.detect(frame)

    for hand in hands:
        hand.draw(frame)

    if not camera.show(frame):
        break

camera.close()
tracker.close()
```

Each `Hand` has 21 points, `handedness`, `confidence`, `box()`, and raw MediaPipe
results via `raw`. Named landmarks make customization clearer:

```python
tip = hand.point(go.HandLandmark.INDEX_FINGER_TIP)
x, y = tip.pixel(frame)
```

OpenCV gives webcam frames without mirroring, so `HandTracker` automatically
adjusts left/right labels by default. If the frame is already flipped horizontally
before detection, use `go.HandTracker(mirrored=True)`.

## Pose Tracking

```python
import cvgo as go


camera = go.Camera()
tracker = go.PoseTracker()

while True:
    frame = camera.read()

    if frame is None:
        break

    pose = tracker.detect(frame)

    if pose:
        pose.draw(frame)
        pose.box().draw(
            frame,
            label="Person",
        )

    if not camera.show(frame):
        break

camera.close()
tracker.close()
```

`PoseTracker` produces 33 body landmarks, a visibility-based
`pose.confidence`, a person box, and world coordinates through
`pose.world_points`. Example access to a point:

```python
shoulder = pose.point(go.PoseLandmark.LEFT_SHOULDER)
```

For lightweight person-presence detection without drawing a skeleton:

```python
tracker = go.PoseTracker(
    model_complexity=0,
)

pose = tracker.detect(frame)

if pose:
    pose.box(
        padding=30,
    ).draw(
        frame,
        label="Person",
    )
```

`pose is not None` means the model found a sufficiently visible body pose. This can
be used as a signal for the presence of one main person, but it is not a general
person detector or a multi-person counter. For distant CCTV, multi-person, or
crowd counting scenarios, use the object detection model.

## FPS

```python
fps = go.FPS()

while True:
    frame = camera.read()
    value = fps.read()
```

The value is updated every second by default. The interval can be changed with
`go.FPS(update_every=0.5)`.

## MediaPipe Task Modes

`ObjectDetector` and `GestureRecognizer` support three running modes:

| Mode | Behavior | Recommended for |
|---|---|---|
| `image` | Synchronous, each image is independent | Photos and unrelated images |
| `video` | Synchronous, sequential frames with timestamps | Video files and simple loops |
| `live` | Asynchronous, returns the latest completed result | Cameras, GUI, and low-power boards |

`video` remains the default, so existing code still waits for and receives the
result of the current frame. For a responsive camera loop, select live mode:

```python
detector = go.ObjectDetector()
```

In live mode, `detect(frame)` submits a frame and immediately returns the latest
completed result. The first calls can return an empty list while the first result
is still being processed. Check `detector.result_ready` when that distinction
matters. MediaPipe can skip incoming frames while its model is busy to keep
latency low.

`fps.read()` measures the camera loop in a live example, not the number of model
results produced per second. The most recent result can be reused across several
display frames.

The old `stream` argument remains compatible: `stream=True` selects `video` and
`stream=False` selects `image`. New code should use `mode` because its intent is
clearer.

## Object Detection

```python
import cvgo as go


camera = go.Camera()
detector = go.ObjectDetector()

while True:
    frame = camera.read()

    if frame is None:
        break

    objects = detector.detect(frame)

    for item in objects:
        item.draw(frame)

    if not camera.show(frame):
        break

camera.close()
detector.close()
```

Each `DetectedObject` has `label`, `score`, `box`, `is_person`, and raw results via
`raw`. For person detection specifically:

```python
detector = go.ObjectDetector(allow=["person"])
```

The official MediaPipe EfficientDet-Lite0 model is downloaded automatically once
on first use. After that, the model is read from cache. Custom models can still be
used:

```python
detector = go.ObjectDetector("models/custom_model.tflite")
```

The model can also be prepared in advance:

```python
go.download_model("object_detection")
```

To process separate images instead of sequential video frames, use
`go.ObjectDetector(mode="image")`.

## Gesture Recognition

```python
import cvgo as go


camera = go.Camera()
recognizer = go.GestureRecognizer()

while True:
    frame = camera.read()

    if frame is None:
        break

    gestures = recognizer.detect(frame)

    for gesture in gestures:
        gesture.draw(frame)

    if not camera.show(frame):
        break

camera.close()
recognizer.close()
```

The default model recognizes `Closed_Fist`, `Open_Palm`, `Pointing_Up`,
`Thumb_Down`, `Thumb_Up`, `Victory`, and `ILoveYou`. Each result exposes
`gesture.hand`, `gesture.handedness`, `gesture.points`, `gesture.box()`,
`gesture.score`, and the raw result for custom logic.

Use `go.GestureRecognizer(mode="image")` for static images that are not part of
a continuous video stream.

## Holistic Tracking

```python
import cvgo as go


camera = go.Camera()
tracker = go.HolisticTracker()

while True:
    frame = camera.read()

    if frame is None:
        break

    result = tracker.detect(frame)

    if result:
        result.draw(frame)

    if not camera.show(frame):
        break

camera.close()
tracker.close()
```

The result parts can still be accessed directly through `result.face`,
`result.pose`, `result.left_hand`, and `result.right_hand`.

## Selfie Segmentation

```python
import cvgo as go


camera = go.Camera()
segmenter = go.SelfieSegmenter()

while True:
    frame = camera.read()

    if frame is None:
        break

    result = segmenter.segment(frame)
    frame = result.blur(frame)

    if not camera.show(frame):
        break

camera.close()
segmenter.close()
```

Replace the background with a color or image:

```python
frame = result.apply(frame, background=(40, 40, 40))
frame = result.apply(frame, background=background_image)
```

## Condition Timer

`Timer` becomes active when a condition remains true for the configured duration.

```python
eye_timer = go.Timer(1.5)

eyes_closed = ear < 0.20
drowsy = eye_timer.check(eyes_closed)
```

When `eyes_closed` becomes false again, the timer resets automatically.

## Easy-to-Understand Drowsiness Detection

```python
import cvgo as go


EAR_THRESHOLD = 0.20

camera = go.Camera()
landmarker = go.FaceLandmarks()
eye_timer = go.Timer(1.5)
ear_smoother = go.Smoother()
alarm = go.Alarm()

while True:
    frame = camera.read()

    if frame is None:
        break

    faces = landmarker.detect(frame)
    drowsy = False

    if faces:
        face = faces[0]
        ear = ear_smoother.update(go.eye_ratio(face))
        drowsy = eye_timer.check(ear < EAR_THRESHOLD)

        status = "DROWSY" if drowsy else "NORMAL"
        color = (0, 0, 255) if drowsy else (0, 255, 0)

        go.put_text(frame, f"Status: {status}", color=color)
        go.put_text(frame, f"EAR: {ear:.3f}", (20, 70))
        face.draw(frame, color=color)
    else:
        eye_timer.reset()
        ear_smoother.reset()

    alarm.trigger(drowsy)

    if not camera.show(frame):
        break

camera.close()
landmarker.close()
```

Bagian penting tetap terlihat: EAR, threshold, smoothing, timer, status, alarm,
dan GUI.

## Serial Arduino

```python
import cvgo as go


arduino = go.Serial()

if arduino.connected:
    arduino.send("1")

arduino.close()
```

## Telegram

Buat bot melalui `@BotFather`, lalu simpan token dan chat ID di environment
variable. Jangan menulis token asli di source code atau repository.

Windows PowerShell:

```powershell
$env:CVGO_TELEGRAM_TOKEN="TOKEN_DARI_BOTFATHER"
$env:CVGO_TELEGRAM_CHAT_ID="CHAT_ID"
```

Linux/macOS:

```bash
export CVGO_TELEGRAM_TOKEN="TOKEN_DARI_BOTFATHER"
export CVGO_TELEGRAM_CHAT_ID="CHAT_ID"
```

Jika chat ID belum diketahui, kirim `/start` ke bot lalu jalankan:

```python
import cvgo as go


telegram = go.Telegram(token="TOKEN_DARI_BOTFATHER")
print(telegram.find_chat_id())
```

Mengirim teks dan frame OpenCV:

```python
telegram = go.Telegram()

telegram.send_message("CVGO aktif")
telegram.send_photo_async(
    frame,
    "Peringatan: orang terdeteksi.",
    key="security",
)
telegram.close()
```

`send_photo()` dan `send_photo_async()` menerima frame OpenCV, bytes, atau path
file gambar. Cooldown
default 30 detik mencegah satu kondisi mengirim terlalu banyak foto. Gunakan
`key` berbeda untuk setiap jenis peringatan atau ubah dengan
`go.Telegram(cooldown=60)`. Status pengiriman berupa `True`/`False`; detail
kegagalan tersedia melalui `telegram.last_error`.

Pada proyek deteksi kantuk, pemakaiannya tetap sederhana:

```python
if drowsy:
    telegram.send_photo_async(
        frame,
        "Peringatan: pengemudi mengantuk.",
        key="drowsy",
    )
```

Contoh lengkap deteksi orang dan pengiriman foto berada di
`examples/17_telegram_security.py`.

## Proyek akhir Driver Monitor

Contoh lengkap proyek akhir berada di:

```text
examples/08_driver_monitor.py
```

Proyek tersebut menggabungkan:

- EAR dan smoothing;
- deteksi noleh serta tunduk;
- timer untuk setiap kondisi;
- deteksi wajah hilang;
- bitmask serial Arduino;
- foto peringatan Telegram dapat ditambahkan dengan `go.Telegram()`;
- alarm suara;
- status dan nilai sensor pada GUI;
- penghitung FPS.

Algoritmanya disusun dari komponen kecil CVGO, bukan satu fungsi instan.

## Shortcut opsional

`DriverMonitor` tetap tersedia bagi pengguna yang membutuhkan prototipe cepat:

```python
from cvgo import DriverMonitor
```

Contoh pembelajaran utama tidak menggunakannya agar algoritma tetap terlihat.

## Terminal / CLI Examples

Every GUI topic now has a terminal-only Python example in `examples/cli/`.
These examples do not open an OpenCV window and update their results on one
terminal line. The detection flow remains visible and editable.

For example, run drowsiness detection with:

```bash
python examples/cli/07_drowsiness.py
```

Press `Ctrl+C` to stop. To use camera `4`, change the example to:

```python
camera = go.Camera(4)
```

See [`examples/cli/README.md`](examples/cli/README.md) for all 17 CLI examples.

## Installation Diagnostics

`python -m cvgo check` reports the CVGO, Python, NumPy, OpenCV, MediaPipe, and
PySerial versions without starting a vision model. This makes it easier to
compare a Windows development machine with an AArch64 Armbian device.

```bash
python -m cvgo check
python -m cvgo check --camera 4
python -m cvgo check --camera 4 --json
```

The command exits with status `0` when the pinned stack is correct and the
optional camera test succeeds. Camera drivers, MediaPipe wheels, display support,
serial permissions, and Telegram network access still need to be tested on the
target STB.

CVGO itself builds as a universal `py3-none-any` wheel, including on AArch64.
`pip` must still find compatible wheels for the pinned OpenCV and MediaPipe
dependencies on the target operating system; do not install an x86 wheel on an
AArch64 device.

The same checks are available to custom tools as `go.system_info()` and
`go.check_camera(source=0, backend=None)`.

## Daftar contoh

```text
examples/
├── 01_camera.py
├── 02_face_detection.py
├── 03_face_landmarks.py
├── 04_face_metrics.py
├── 05_serial_arduino.py
├── 06_face_to_arduino.py
├── 07_drowsiness.py
├── 08_driver_monitor.py
├── 09_hand_tracking.py
├── 10_pose_tracking.py
├── 11_security_pose.py
├── 12_object_detection.py
├── 13_person_security.py
├── 14_gesture_recognition.py
├── 15_holistic_tracking.py
├── 16_selfie_segmentation.py
├── 17_telegram_security.py
└── cli/
    ├── 01_camera.py
    ├── 02_face_detection.py
    ├── ...
    └── 17_telegram_security.py
```

## Pengembangan lokal

```bash
pip install -e .
```

Untuk alat build dan publikasi:

```bash
pip install -e ".[dev]"
```

Panduan TestPyPI dan PyPI tersedia di [`PUBLISHING.md`](PUBLISHING.md).

## Lisensi

MIT License.
