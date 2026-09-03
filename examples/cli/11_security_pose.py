"""CLI example 11: run lightweight person security with Pose Lite."""

import cvgo as go


camera = go.Camera()
tracker = go.PoseTracker(model_complexity=0)
presence_timer = go.Timer(0.5)
alarm = go.Alarm()
fps = go.FPS()

try:
    while True:
        frame = camera.read()

        if frame is None:
            break

        pose = tracker.detect(frame)
        alert = presence_timer.check(pose is not None)
        status = "ALERT" if alert else "SAFE"
        info = f"Security: {status} | FPS: {fps.read():.1f}"

        alarm.trigger(alert)
        print(f"\r{info:<60}", end="", flush=True)
except KeyboardInterrupt:
    pass
finally:
    print()
    camera.close()
    tracker.close()
