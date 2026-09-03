"""CLI example 17: send a Telegram photo when a person is detected."""

import cvgo as go


camera = go.Camera()
detector = go.ObjectDetector(allow=["person"], mode="live")
telegram = go.Telegram()
presence_timer = go.Timer(0.5)
fps = go.FPS()
notified = False
telegram_status = "WAITING"
pending = None

try:
    while True:
        frame = camera.read()

        if frame is None:
            break

        people = detector.detect(frame)
        alert = presence_timer.check(bool(people))

        if pending is not None and pending.done():
            sent = pending.result()
            telegram_status = "SENT" if sent else "FAILED"
            pending = None

        if alert and not notified and pending is None:
            pending = telegram.send_photo_async(
                frame,
                f"Warning: {len(people)} person(s) detected.",
                key="security",
            )
            telegram_status = "QUEUED"
            notified = True
        elif not alert:
            notified = False
            telegram_status = "WAITING"

        status = "PERSON DETECTED" if alert else "SAFE"
        info = (
            f"Security: {status} | People: {len(people)} | "
            f"Telegram: {telegram_status} | "
            f"Loop FPS: {fps.read():.1f}"
        )
        print(f"\r{info:<110}", end="", flush=True)

        if telegram_status == "FAILED":
            print(f"\nTelegram: {telegram.last_error}")
            telegram_status = "ERROR SHOWN"
except KeyboardInterrupt:
    pass
finally:
    print()
    camera.close()
    detector.close()
    telegram.close()
