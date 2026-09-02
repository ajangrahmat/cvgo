"""Contoh 4: membaca EAR, yaw, dan pitch."""

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
        go.put_text(frame, f"Yaw: {yaw:.3f}", (20, 70))
        go.put_text(frame, f"Pitch: {pitch:.3f}", (20, 105))

        face.draw(frame)

    if not camera.show(frame):
        break

camera.close()
landmarker.close()

