"""Contoh 2: mendeteksi wajah."""

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

