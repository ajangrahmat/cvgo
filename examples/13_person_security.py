"""Example 13: detect multiple people for simple security."""

import cvgo as go


camera = go.Camera()
detector = go.ObjectDetector(allow=["person"], mode="live")
presence_timer = go.Timer(0.5)
alarm = go.Alarm()

while True:
    frame = camera.read()

    if frame is None:
        break

    people = detector.detect(frame)
    alert = presence_timer.check(bool(people))

    for person in people:
        person.draw(frame, color=(0, 0, 255))

    status = "ALERT" if alert else "SAFE"
    color = (0, 0, 255) if alert else (0, 255, 0)

    go.put_text(frame, f"Status: {status}", color=color)
    go.put_text(frame, f"Count: {len(people)}", (20, 70))
    alarm.trigger(alert)

    if not camera.show(frame, title="CVGO Person Security"):
        break

camera.close()
detector.close()
