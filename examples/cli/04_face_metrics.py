"""CLI example 4: print EAR, yaw, and pitch values."""

import cvgo as go


camera = go.Camera()
landmarker = go.FaceLandmarks()
fps = go.FPS()

try:
    while True:
        frame = camera.read()

        if frame is None:
            break

        faces = landmarker.detect(frame)

        if faces:
            face = faces[0]
            ear = f"{go.eye_ratio(face):.3f}"
            yaw = f"{go.yaw_ratio(face):.3f}"
            pitch = f"{go.pitch_ratio(face):.3f}"
        else:
            ear = yaw = pitch = "---"

        info = (
            f"EAR: {ear} | Yaw: {yaw} | Pitch: {pitch} | "
            f"FPS: {fps.read():.1f}"
        )
        print(f"\r{info:<80}", end="", flush=True)
except KeyboardInterrupt:
    pass
finally:
    print()
    camera.close()
    landmarker.close()
