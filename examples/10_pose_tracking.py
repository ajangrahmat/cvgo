"""Contoh 10: pelacakan pose tubuh."""

import cvgo as go


camera = go.Camera()
tracker = go.PoseTracker()
fps = go.FPS()

while True:
    frame = camera.read()

    if frame is None:
        break

    pose = tracker.detect(frame)
    person_detected = pose is not None

    if pose:
        pose.draw(frame)

    status = "POSE TERDETEKSI" if person_detected else "TIDAK ADA POSE"
    color = (0, 255, 0) if person_detected else (0, 0, 255)

    go.put_text(frame, status, color=color)
    go.put_text(frame, f"FPS: {fps.read():.1f}", (20, 70))

    if not camera.show(frame, title="CVGO Pose Tracking"):
        break

camera.close()
tracker.close()
