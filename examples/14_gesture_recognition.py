"""Example 14: hand gesture recognition."""

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

    if not camera.show(frame, title="CVGO Gesture Recognition"):
        break

camera.close()
recognizer.close()
