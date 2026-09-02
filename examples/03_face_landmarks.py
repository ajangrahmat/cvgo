"""Example 3: display face landmarks."""

import cvgo as go


camera = go.Camera()
landmarker = go.FaceLandmarks()

while True:
    frame = camera.read()

    if frame is None:
        break

    faces = landmarker.detect(frame)

    for face in faces:
        face.draw(frame)

    if not camera.show(frame):
        break

camera.close()
landmarker.close()

