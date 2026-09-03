"""Example 11: lightweight person security with a pose bounding box."""

import cvgo as go


camera = go.Camera()
tracker = go.PoseTracker(model_complexity=0)
presence_timer = go.Timer(0.5)
alarm = go.Alarm()
fps = go.FPS()

while True:
    frame = camera.read()

    if frame is None:
        break

    pose = tracker.detect(frame)
    person_detected = pose is not None
    alert = presence_timer.check(person_detected)

    status = "ALERT" if alert else "SAFE"
    color = (0, 0, 255) if alert else (0, 255, 0)

    if pose:
        pose.box(
            padding=30,
        ).draw(
            frame,
            color=color,
            label="Person",
        )

    go.put_text(frame, f"Status: {status}", color=color)
    go.put_text(frame, f"FPS: {fps.read():.1f}", (20, 70))
    alarm.trigger(alert)

    if not camera.show(frame, title="CVGO Person Security Lite"):
        break

camera.close()
tracker.close()
