"""Contoh 8: proyek akhir Driver Monitor yang tetap dapat dipelajari."""

import cvgo as go


# Threshold deteksi
EAR_THRESHOLD = 0.20
YAW_NORMAL = 0.50
YAW_LIMIT = 0.12
PITCH_NORMAL = 0.50
PITCH_LIMIT = 0.055

# Komponen
camera = go.Camera()
landmarker = go.FaceLandmarks()
arduino = go.Serial()
alarm = go.Alarm()
fps_counter = go.FPS()

# Timer kondisi
eye_timer = go.Timer(1.5)
turn_timer = go.Timer(0.7)
down_timer = go.Timer(0.7)
missing_timer = go.Timer(2.0)

# Penghalus nilai mata
ear_smoother = go.Smoother()

# Status serial terakhir
last_mask = None

while True:
    frame = camera.read()

    if frame is None:
        break

    faces = landmarker.detect(frame)
    fps = fps_counter.read()

    ear = None
    yaw = None
    pitch = None

    drowsy = False
    looking_away = False
    head_down = False
    face_missing = False

    if faces:
        face = faces[0]

        ear = ear_smoother.update(go.eye_ratio(face))
        yaw = go.yaw_ratio(face)
        pitch = go.pitch_ratio(face)

        eyes_closed = ear < EAR_THRESHOLD
        turn_condition = abs(yaw - YAW_NORMAL) > YAW_LIMIT
        down_condition = pitch - PITCH_NORMAL > PITCH_LIMIT

        drowsy = eye_timer.check(eyes_closed)
        looking_away = turn_timer.check(turn_condition)
        head_down = down_timer.check(down_condition)

        missing_timer.reset()
        face.draw(frame)
    else:
        eye_timer.reset()
        turn_timer.reset()
        down_timer.reset()
        ear_smoother.reset()

        face_missing = missing_timer.check(True)

    mask = 0

    if drowsy:
        mask |= go.BIT_DROWSY

    if looking_away:
        mask |= go.BIT_LOOKING_AWAY

    if head_down:
        mask |= go.BIT_HEAD_DOWN

    if face_missing:
        mask |= go.BIT_FACE_MISSING

    if mask != last_mask:
        if arduino.send(f"{mask:X}"):
            last_mask = mask

    alerts = []

    if drowsy:
        alerts.append("NGANTUK")

    if looking_away:
        alerts.append("NOLEH")

    if head_down:
        alerts.append("TUNDUK")

    if face_missing:
        alerts.append("WAJAH HILANG")

    status = " | ".join(alerts) if alerts else "NORMAL"
    color = (0, 0, 255) if alerts else (0, 255, 0)

    ear_text = "-" if ear is None else f"{ear:.3f}"
    yaw_text = "-" if yaw is None else f"{yaw:.3f}"
    pitch_text = "-" if pitch is None else f"{pitch:.3f}"

    go.put_text(
        frame,
        f"Status: {status}",
        (20, 35),
        color=color,
        background=True,
    )
    go.put_text(frame, f"EAR: {ear_text}", (20, 70))
    go.put_text(frame, f"Yaw: {yaw_text}", (20, 105))
    go.put_text(frame, f"Pitch: {pitch_text}", (20, 140))
    go.put_text(frame, f"FPS: {fps:.1f} | Mask: {mask:X}", (20, 175))

    alarm.trigger(mask != 0)

    if not camera.show(frame, title="CVGO Driver Monitor"):
        break

camera.close()
landmarker.close()
arduino.close()
