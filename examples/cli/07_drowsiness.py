"""CLI example 7: detect drowsiness and print the result."""

import cvgo as go


EAR_THRESHOLD = 0.30

camera = go.Camera()
landmarker = go.FaceLandmarks()
eye_timer = go.Timer(0.5)
ear_smoother = go.Smoother()
alarm = go.Alarm()
fps = go.FPS()

try:
    while True:
        frame = camera.read()

        if frame is None:
            break

        faces = landmarker.detect(frame)
        drowsy = False
        status = "NO FACE"
        ear_text = "---"

        if faces:
            ear = ear_smoother.update(go.eye_ratio(faces[0]))
            drowsy = eye_timer.check(ear < EAR_THRESHOLD)
            status = "DROWSY" if drowsy else "NORMAL"
            ear_text = f"{ear:.3f}"
        else:
            eye_timer.reset()
            ear_smoother.reset()

        alarm.trigger(drowsy)

        info = (
            f"Status: {status} | EAR: {ear_text} | "
            f"FPS: {fps.read():.1f}"
        )
        print(f"\r{info:<70}", end="", flush=True)
except KeyboardInterrupt:
    pass
finally:
    print()
    camera.close()
    landmarker.close()
