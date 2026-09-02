"""Contoh 16: blur latar belakang webcam."""

import cvgo as go


camera = go.Camera()
segmenter = go.SelfieSegmenter()

while True:
    frame = camera.read()

    if frame is None:
        break

    result = segmenter.segment(frame)
    frame = result.blur(frame)

    if not camera.show(frame, title="CVGO Selfie Segmentation"):
        break

camera.close()
segmenter.close()
