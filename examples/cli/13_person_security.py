"""CLI example 13: detect people for a terminal security monitor."""

import cvgo as go


camera = go.Camera()
detector = go.ObjectDetector(allow=["person"], mode="live")
presence_timer = go.Timer(0.5)
alarm = go.Alarm()
fps = go.FPS()

try:
    while True:
        frame = camera.read()

        if frame is None:
            break

        people = detector.detect(frame)
        alert = presence_timer.check(bool(people))
        status = "ALERT" if alert else "SAFE"
        info = (
            f"Security: {status} | People: {len(people)} | "
            f"Loop FPS: {fps.read():.1f}"
        )

        alarm.trigger(alert)
        print(f"\r{info:<70}", end="", flush=True)
except KeyboardInterrupt:
    pass
finally:
    print()
    camera.close()
    detector.close()
