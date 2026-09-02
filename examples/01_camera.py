"""Contoh 1: membuka dan menampilkan kamera."""

import cvgo as go


camera = go.Camera()

while True:
    frame = camera.read()

    if frame is None:
        break

    if not camera.show(frame):
        break

camera.close()

