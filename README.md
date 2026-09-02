<p align="center">
    <img src="logo-cvgo.png" alt="CVGO" width="520">
</p>

<h1 align="center">CVGO</h1>

<p align="center"><strong>Simple Computer Vision for Python</strong></p>

<p align="center">
    <a href="https://kelasrobot.com">Homepage</a> ·
    <a href="examples/">Examples</a> ·
    <a href="LICENSE">MIT License</a>
</p>

CVGO simplifies the repetitive parts of OpenCV and MediaPipe while keeping the
main program flow visible. Users still write `while True`, read frames, inspect
detection results, make decisions, and display the GUI.

> Simple by default, customizable when needed.

## Installation

Once available on PyPI:

```bash
pip install cvgo
```

CVGO V1 pins the core versions that have been tested:

| Package | Version |
|---|---|
| CVGO | `0.1.1` |
| OpenCV Contrib | `4.11.0.86` |
| NumPy | `1.26.4` |
| MediaPipe | `0.10.21` |

The OpenCV package used is `opencv-contrib-python` to avoid installing two
separate `cv2` variants alongside MediaPipe dependencies.

Use Python 3.10, 3.11, or 3.12.

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

## CVGO V1 Features

| Feature | Main API | Output |
|---|---|---|
| Camera and GUI | `Camera` | OpenCV frames |
| Face detection | `FaceDetector` | Face boxes |
| Face landmarks | `FaceLandmarks` | Face landmarks and metrics |
| Hand tracking | `HandTracker` | 21 landmarks per hand |
| Pose tracking | `PoseTracker` | 33 body landmarks |
| Holistic tracking | `HolisticTracker` | Face, pose, and both hands |
| Gesture | `GestureRecognizer` | Gesture, score, and landmarks |
| Object detection | `ObjectDetector` | Labels, scores, and object boxes |
| Human segmentation | `SelfieSegmenter` | Human mask and background |
| Driver monitor | Modular components | Drowsiness, head direction, and alarms |
| Arduino | `Serial` | Serial communication |
| Telegram | `Telegram` | Text messages and photos from camera frames |

This is the full coverage of CVGO V1 for camera and learning projects.
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
| `FaceDetector()` | Maximum one face |
| `FaceLandmarks()` | Maximum one face |
| `HandTracker()` | Maximum two hands |
| `PoseTracker()` | One main pose |
| `HolisticTracker()` | One main person, 543 landmarks |
| `GestureRecognizer()` | Maximum two hands |
| `ObjectDetector()` | Maximum 10 objects, confidence `0.5` |
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

    if not camera.show(frame):
        break

camera.close()
tracker.close()
```

`PoseTracker` produces 33 body landmarks and world coordinates through
`pose.world_points`. Example access to a point:

```python
shoulder = pose.point(go.PoseLandmark.LEFT_SHOULDER)
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
`go.ObjectDetector(stream=False)`.

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
`Thumb_Down`, `Thumb_Up`, `Victory`, and `ILoveYou`. Each result also exposes
`gesture.hand`, `gesture.score`, and raw landmarks for custom logic.

Use `go.GestureRecognizer(stream=False)` for static images that are not part of a
continuous video stream.

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
telegram.send_photo(
    frame,
    "Peringatan: orang terdeteksi.",
    key="security",
)
```

`send_photo()` menerima frame OpenCV, bytes, atau path file gambar. Cooldown
default 30 detik mencegah satu kondisi mengirim terlalu banyak foto. Gunakan
`key` berbeda untuk setiap jenis peringatan atau ubah dengan
`go.Telegram(cooldown=60)`. Status pengiriman berupa `True`/`False`; detail
kegagalan tersedia melalui `telegram.last_error`.

Pada proyek deteksi kantuk, pemakaiannya tetap sederhana:

```python
if drowsy:
    telegram.send_photo(
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
