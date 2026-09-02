"""Example 1: open and display the camera."""

import cvgo as go


camera = go.Camera()

while True:
    frame = camera.read()

    if frame is None:
        break

    if not camera.show(frame):
        break

camera.close()

