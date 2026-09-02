"""Contoh 12: object detection umum."""

import cvgo as go


camera = go.Camera()
detector = go.ObjectDetector()
fps = go.FPS()

while True:
    frame = camera.read()

    if frame is None:
        break

    objects = detector.detect(frame)

    for item in objects:
        item.draw(frame)

    go.put_text(frame, f"Objects: {len(objects)}")
    go.put_text(frame, f"FPS: {fps.read():.1f}", (20, 70))

    if not camera.show(frame, title="CVGO Object Detection"):
        break

camera.close()
detector.close()
