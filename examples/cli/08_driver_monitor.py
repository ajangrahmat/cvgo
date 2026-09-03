"""CLI example 8: complete modular driver monitoring."""

import cvgo as go


EAR_THRESHOLD = 0.20
YAW_NORMAL = 0.50
YAW_LIMIT = 0.12
PITCH_NORMAL = 0.50
PITCH_LIMIT = 0.055

camera = go.Camera()
landmarker = go.FaceLandmarks()
arduino = go.Serial()
alarm = go.Alarm()
fps = go.FPS()

eye_timer = go.Timer(1.5)
turn_timer = go.Timer(0.7)
down_timer = go.Timer(0.7)
missing_timer = go.Timer(2.0)
ear_smoother = go.Smoother()
last_mask = None

try:
    while True:
        frame = camera.read()

        if frame is None:
            break

        faces = landmarker.detect(frame)
        ear = yaw = pitch = None
        drowsy = looking_away = head_down = face_missing = False

        if faces:
            face = faces[0]
            ear = ear_smoother.update(go.eye_ratio(face))
            yaw = go.yaw_ratio(face)
            pitch = go.pitch_ratio(face)

            drowsy = eye_timer.check(ear < EAR_THRESHOLD)
            looking_away = turn_timer.check(
                abs(yaw - YAW_NORMAL) > YAW_LIMIT
            )
            head_down = down_timer.check(
                pitch - PITCH_NORMAL > PITCH_LIMIT
            )
            missing_timer.reset()
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

        if mask != last_mask and arduino.send(f"{mask:X}"):
            last_mask = mask

        alerts = []

        if drowsy:
            alerts.append("DROWSY")
        if looking_away:
            alerts.append("LOOKING AWAY")
        if head_down:
            alerts.append("HEAD DOWN")
        if face_missing:
            alerts.append("FACE MISSING")

        status = ", ".join(alerts) if alerts else "NORMAL"
        ear_text = "---" if ear is None else f"{ear:.3f}"
        yaw_text = "---" if yaw is None else f"{yaw:.3f}"
        pitch_text = "---" if pitch is None else f"{pitch:.3f}"
        alarm.trigger(mask != 0)

        info = (
            f"Status: {status} | EAR: {ear_text} | Yaw: {yaw_text} | "
            f"Pitch: {pitch_text} | FPS: {fps.read():.1f} | Mask: {mask:X}"
        )
        print(f"\r{info:<130}", end="", flush=True)
except KeyboardInterrupt:
    pass
finally:
    print()
    camera.close()
    landmarker.close()
    arduino.close()
