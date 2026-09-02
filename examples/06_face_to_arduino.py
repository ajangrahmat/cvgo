"""Example 6: send face detection status to Arduino."""

import cvgo as go


camera = go.Camera()
detector = go.FaceDetector()
arduino = go.Serial()
last_status = None

while True:
    frame = camera.read()

    if frame is None:
        break

    faces = detector.detect(frame)
    status = 1 if faces else 0

    if status != last_status:
        if arduino.send(status):
            last_status = status

    for face in faces:
        face.draw(frame)

    if not camera.show(frame):
        break

camera.close()
detector.close()
arduino.close()

