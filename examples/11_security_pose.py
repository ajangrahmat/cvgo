"""Example 11: simple security alarm based on pose presence."""

import cvgo as go


camera = go.Camera()
tracker = go.PoseTracker()
presence_timer = go.Timer(0.5)
alarm = go.Alarm()

while True:
    frame = camera.read()

    if frame is None:
        break

    pose = tracker.detect(frame)
    person_detected = pose is not None
    alert = presence_timer.check(person_detected)

    if pose:
        pose.draw(frame)

    status = "ALERT" if alert else "SAFE"
    color = (0, 0, 255) if alert else (0, 255, 0)

    go.put_text(frame, f"Status: {status}", color=color)
    alarm.trigger(alert)

    if not camera.show(frame, title="CVGO Security Pose"):
        break

camera.close()
tracker.close()
