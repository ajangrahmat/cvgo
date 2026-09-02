"""Contoh 17: kirim foto Telegram saat orang terdeteksi."""

import cvgo as go


camera = go.Camera()
detector = go.ObjectDetector(allow=["person"])
telegram = go.Telegram()
presence_timer = go.Timer(0.5)
notified = False

while True:
    frame = camera.read()

    if frame is None:
        break

    people = detector.detect(frame)
    alert = presence_timer.check(bool(people))

    for person in people:
        person.draw(frame, color=(0, 0, 255))

    status = "ORANG TERDETEKSI" if alert else "AMAN"
    color = (0, 0, 255) if alert else (0, 255, 0)
    go.put_text(frame, f"Status: {status}", color=color)

    if alert and not notified:
        sent = telegram.send_photo(
            frame,
            f"Peringatan: {len(people)} orang terdeteksi.",
            key="security",
        )
        if not sent:
            print(f"Telegram: {telegram.last_error}")

    notified = alert

    if not camera.show(frame, title="CVGO Telegram Security"):
        break

camera.close()
detector.close()
