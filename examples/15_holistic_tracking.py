"""Contoh 15: wajah, pose, dan tangan dalam satu pipeline."""

import cvgo as go


camera = go.Camera()
tracker = go.HolisticTracker()

while True:
    frame = camera.read()

    if frame is None:
        break

    result = tracker.detect(frame)
    result.draw(frame)

    if not camera.show(frame, title="CVGO Holistic Tracking"):
        break

camera.close()
tracker.close()
