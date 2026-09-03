# CVGO Terminal / CLI Examples

These examples process camera frames without opening an OpenCV preview window.
Results are updated on one terminal line, and the main `while True` flow remains
visible so every part can be customized.

Run an example from the project root:

```bash
python examples/cli/07_drowsiness.py
```

Press `Ctrl+C` to stop. The default camera is `0`. To use another camera, edit:

```python
camera = go.Camera(4)
```

Before running a camera example, the same source can be checked with:

```bash
python -m cvgo check --camera 4
```

## Available examples

| File | Topic |
|---|---|
| `01_camera.py` | Camera resolution and FPS |
| `02_face_detection.py` | Face count |
| `03_face_landmarks.py` | Face and landmark count |
| `04_face_metrics.py` | EAR, yaw, and pitch |
| `05_serial_arduino.py` | Interactive Arduino serial |
| `06_face_to_arduino.py` | Send face status to Arduino |
| `07_drowsiness.py` | Drowsiness detection and alarm |
| `08_driver_monitor.py` | Full modular driver monitor |
| `09_hand_tracking.py` | Hand count and handedness |
| `10_pose_tracking.py` | Body pose status |
| `11_security_pose.py` | Lightweight person security with Pose Lite |
| `12_object_detection.py` | Object labels and scores |
| `13_person_security.py` | Person count and alarm |
| `14_gesture_recognition.py` | Gesture labels and scores |
| `15_holistic_tracking.py` | Face, pose, and hand status |
| `16_selfie_segmentation.py` | Foreground coverage |
| `17_telegram_security.py` | Person alert with queued Telegram photo |

These are Python scripts, not commands such as `cvgo drowsy`. They use the same
public API as the GUI examples and work after `pip install cvgo`.
