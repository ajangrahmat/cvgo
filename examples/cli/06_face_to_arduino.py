"""CLI example 6: send face presence to Arduino."""

import cvgo as go


camera = go.Camera()
detector = go.FaceDetector()
arduino = go.Serial()
fps = go.FPS()
last_status = None

try:
    while True:
        frame = camera.read()

        if frame is None:
            break

        faces = detector.detect(frame)
        status = 1 if faces else 0

        if status != last_status and arduino.send(status):
            last_status = status

        face_text = "DETECTED" if status else "NOT DETECTED"
        serial_text = "CONNECTED" if arduino.connected else "DISCONNECTED"
        info = (
            f"Face: {face_text} | Arduino: {serial_text} | "
            f"Sent: {last_status} | FPS: {fps.read():.1f}"
        )
        print(f"\r{info:<100}", end="", flush=True)
except KeyboardInterrupt:
    pass
finally:
    print()
    camera.close()
    detector.close()
    arduino.close()
