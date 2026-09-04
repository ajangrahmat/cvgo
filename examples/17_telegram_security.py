"""Example 17: send a Telegram photo when a person is detected."""

import cvgo as go


camera = go.Camera()
detector = go.ObjectDetector(allow=["person"])
telegram = go.Telegram()
presence_timer = go.Timer(0.5)
notified = False
pending = None

while True:
    frame = camera.read()

    if frame is None:
        break

    people = detector.detect(frame)
    alert = presence_timer.check(bool(people))

    if pending is not None and pending.done():
        if not pending.result():
            print(f"Telegram: {telegram.last_error}")
        pending = None

    for person in people:
        person.draw(frame, color=(0, 0, 255))

    status = "PERSON DETECTED" if alert else "SAFE"
    color = (0, 0, 255) if alert else (0, 255, 0)
    go.put_text(frame, f"Status: {status}", color=color)

    if alert and not notified and pending is None:
        pending = telegram.send_photo_async(
            frame,
            f"Warning: {len(people)} person(s) detected.",
            key="security",
        )

    notified = alert

    if not camera.show(frame, title="CVGO Telegram Security"):
        break

camera.close()
detector.close()
telegram.close()
