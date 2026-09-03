"""Example 12: general object detection."""

import cvgo as go


camera = go.Camera()
detector = go.ObjectDetector(mode="live")
fps = go.FPS()

while True:
    frame = camera.read()

    if frame is None:
        break

    objects = detector.detect(frame)

    for item in objects:
        item.draw(frame)

    go.put_text(frame, f"Objects: {len(objects)}")
    go.put_text(frame, f"Loop FPS: {fps.read():.1f}", (20, 70))

    if not camera.show(frame, title="CVGO Object Detection"):
        break

camera.close()
detector.close()
