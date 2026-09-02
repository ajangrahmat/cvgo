# CVGO

**Simple Computer Vision for Python**

CVGO menyederhanakan bagian OpenCV dan MediaPipe yang berulang, tetapi tetap
memperlihatkan alur utama program. Pengguna masih menulis `while True`, membaca
frame, mengambil hasil deteksi, membuat keputusan, dan menampilkan GUI.

> Simple by default, customizable when needed.

## Instalasi

Setelah tersedia di PyPI:

```bash
pip install cvgo
```

CVGO V1 mengunci versi inti yang sudah diuji:

| Paket | Versi |
|---|---|
| CVGO | `0.1.1` |
| OpenCV Contrib | `4.11.0.86` |
| NumPy | `1.26.4` |
| MediaPipe | `0.10.21` |

Paket OpenCV yang dipakai adalah `opencv-contrib-python` agar tidak memasang dua
varian `cv2` sekaligus dengan dependensi MediaPipe.

Gunakan Python 3.10, 3.11, atau 3.12.

Disarankan memasang CVGO di virtual environment khusus:

```powershell
py -3.11 -m venv .venv-cvgo
.venv-cvgo\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install cvgo
```

Pada virtual environment baru, `pip` akan memasang dependency satu kali. Jika
perintah instalasi dijalankan lagi pada environment yang sama, paket yang sudah
sesuai akan ditandai sebagai `Requirement already satisfied`.

Jangan memasang `opencv-python`, `opencv-python-headless`, atau varian OpenCV
lain bersama `opencv-contrib-python`. Semua varian tersebut menyediakan modul
`cv2` yang sama.

`ObjectDetector` dan `GestureRecognizer` memakai model resmi MediaPipe yang
diunduh otomatis saat pertama digunakan. Komputer hanya memerlukan internet
pada unduhan pertama; sesudah itu model digunakan dari cache.

## Import

```python
import cvgo as go
```

Semua komponen juga dapat di-import langsung:

```python
from cvgo import Camera, ObjectDetector, Telegram
```

## Fitur CVGO V1

| Fitur | API utama | Hasil |
|---|---|---|
| Kamera dan GUI | `Camera` | Frame OpenCV |
| Deteksi wajah | `FaceDetector` | Kotak wajah |
| Landmark wajah | `FaceLandmarks` | Landmark dan metrik wajah |
| Hand tracking | `HandTracker` | 21 landmark per tangan |
| Pose tracking | `PoseTracker` | 33 landmark tubuh |
| Holistic tracking | `HolisticTracker` | Wajah, pose, dan kedua tangan |
| Gesture | `GestureRecognizer` | Gesture, score, dan landmark |
| Object detection | `ObjectDetector` | Label, score, dan kotak objek |
| Segmentasi manusia | `SelfieSegmenter` | Mask manusia dan latar |
| Driver monitor | Komponen modular | Kantuk, arah kepala, dan alarm |
| Arduino | `Serial` | Komunikasi serial |
| Telegram | `Telegram` | Pesan teks dan foto dari frame kamera |

Ini adalah cakupan lengkap CVGO V1 untuk proyek kamera dan pembelajaran.
Fitur MediaPipe di luar cakupan tersebut tetap dapat ditambahkan pada versi
berikutnya tanpa mengubah pola API utama.

## Gaya nama Python

CVGO mengikuti gaya umum Python (PEP 8):

- class memakai `PascalCase`: `HandTracker`, `PoseTracker`;
- fungsi dan method memakai `snake_case`: `read_fps()`, `put_text()`;
- konstanta memakai `UPPER_CASE`: `BIT_DROWSY`, `LEFT_WRIST`.

Jadi gunakan `read_fps()`, bukan `readFPS()`. Karena objeknya sudah bernama
`FPS`, bentuk yang paling ringkas adalah `fps.read()`; `fps.read_fps()` tetap
tersedia sebagai alias yang lebih eksplisit.

## Default yang sederhana

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

Default utamanya:

| Komponen | Default |
|---|---|
| `Camera()` | Kamera `0` |
| `FaceDetector()` | Maksimal satu wajah |
| `FaceLandmarks()` | Maksimal satu wajah |
| `HandTracker()` | Maksimal dua tangan |
| `PoseTracker()` | Satu pose utama |
| `HolisticTracker()` | Satu orang utama, 543 landmark |
| `GestureRecognizer()` | Maksimal dua tangan |
| `ObjectDetector()` | Maksimal 10 objek, confidence `0.5` |
| `SelfieSegmenter()` | Model landscape untuk webcam |
| `Serial()` | Port otomatis, `9600` baud |
| `Telegram()` | Konfigurasi dari environment, cooldown 30 detik |
| `Timer()` | Durasi satu detik |
| `Smoother()` | Alpha `0.45` |

Isi parameter hanya ketika ingin mengubah default:

```python
camera = go.Camera(1, width=1280, height=720)
arduino = go.Serial("COM5", baud=115200)
timer = go.Timer(1.5)
hands = go.HandTracker(max_hands=1, detection_confidence=0.7)
pose = go.PoseTracker(model_complexity=0)
objects = go.ObjectDetector(confidence=0.7, allow=["person"])
telegram = go.Telegram(cooldown=60)
```

## Kamera

Secara default, CVGO membiarkan OpenCV memilih backend kamera terbaik
(`CAP_ANY`). Backend khusus tetap dapat diberikan melalui parameter `backend`.

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

Tekan `q` untuk keluar.

## Deteksi wajah

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

## Landmark dan metrik wajah

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

## Hand tracking

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

Setiap `Hand` memiliki 21 titik, `handedness`, `confidence`, `box()`, dan hasil
mentah MediaPipe melalui `raw`. Landmark bernama membuat kustomisasi tetap jelas:

```python
tip = hand.point(go.HandLandmark.INDEX_FINGER_TIP)
x, y = tip.pixel(frame)
```

OpenCV memberikan frame webcam yang tidak dicerminkan, sehingga `HandTracker`
menyesuaikan label kiri/kanan secara default. Jika frame sudah di-flip secara
horizontal sebelum dideteksi, gunakan `go.HandTracker(mirrored=True)`.

## Pose tracking

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

`PoseTracker` menghasilkan 33 landmark tubuh dan koordinat dunia melalui
`pose.world_points`. Contoh akses titik:

```python
shoulder = pose.point(go.PoseLandmark.LEFT_SHOULDER)
```

`pose is not None` berarti model menemukan pose tubuh yang cukup terlihat.
Ini dapat dipakai sebagai indikator keberadaan satu orang utama, tetapi bukan
detektor orang umum atau penghitung banyak orang. Untuk CCTV jarak jauh,
multi-person, atau menghitung orang, gunakan model object detection khusus.

## FPS

```python
fps = go.FPS()

while True:
    frame = camera.read()
    value = fps.read()
```

Nilai diperbarui setiap satu detik secara default. Interval dapat diubah dengan
`go.FPS(update_every=0.5)`.

## Object detection

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

Setiap `DetectedObject` memiliki `label`, `score`, `box`, `is_person`, dan
hasil mentah melalui `raw`. Untuk khusus deteksi orang:

```python
detector = go.ObjectDetector(allow=["person"])
```

Model EfficientDet-Lite0 resmi MediaPipe diunduh otomatis satu kali saat
pertama digunakan. Setelah itu model dibaca dari cache. Model kustom tetap bisa
dipakai:

```python
detector = go.ObjectDetector("models/custom_model.tflite")
```

Model juga dapat disiapkan lebih awal:

```python
go.download_model("object_detection")
```

Untuk memproses gambar-gambar terpisah dan bukan frame video berurutan, gunakan
`go.ObjectDetector(stream=False)`.

## Gesture recognition

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

Model default mengenali `Closed_Fist`, `Open_Palm`, `Pointing_Up`,
`Thumb_Down`, `Thumb_Up`, `Victory`, dan `ILoveYou`. Setiap hasil juga membuka
`gesture.hand`, `gesture.score`, serta landmark mentah untuk logika kustom.

Gunakan `go.GestureRecognizer(stream=False)` untuk gambar statis yang tidak
berasal dari satu video berurutan.

## Holistic tracking

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

Bagian hasil tetap dapat diakses sendiri melalui `result.face`, `result.pose`,
`result.left_hand`, dan `result.right_hand`.

## Selfie segmentation

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

Mengganti latar dengan warna atau gambar:

```python
frame = result.apply(frame, background=(40, 40, 40))
frame = result.apply(frame, background=background_image)
```

## Timer kondisi

`Timer` aktif jika kondisi terus benar selama durasi yang ditentukan.

```python
eye_timer = go.Timer(1.5)

eyes_closed = ear < 0.20
drowsy = eye_timer.check(eyes_closed)
```

Saat `eyes_closed` kembali salah, timer otomatis di-reset.

## Deteksi kantuk yang tetap mudah dipelajari

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

        status = "NGANTUK" if drowsy else "NORMAL"
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
