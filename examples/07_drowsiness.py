"""Example 7: detect drowsiness based on EAR and duration."""

import cvgo as go


EAR_THRESHOLD = 0.20

camera = go.Camera()
landmarker = go.FaceLandmarks()
eye_timer = go.Timer(1.5)
ear_smoother = go.Smoother()
alarm = go.Alarm()

while True:
    frame = camera.read()

    if frame is None:
        break

    faces = landmarker.detect(frame)
    drowsy = False

    if faces:
        face = faces[0]
        ear = ear_smoother.update(go.eye_ratio(face))
        eyes_closed = ear < EAR_THRESHOLD
        drowsy = eye_timer.check(eyes_closed)

        status = "DROWSY" if drowsy else "NORMAL"
        color = (0, 0, 255) if drowsy else (0, 255, 0)

        go.put_text(frame, f"Status: {status}", color=color)
        go.put_text(frame, f"EAR: {ear:.3f}", (20, 70))
        face.draw(frame, color=color)
    else:
        eye_timer.reset()
        ear_smoother.reset()

    alarm.trigger(drowsy)

    if not camera.show(frame):
        break

camera.close()
landmarker.close()

