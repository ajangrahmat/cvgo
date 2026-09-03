"""CLI example 15: print face, pose, and hand status."""

import cvgo as go


camera = go.Camera()
tracker = go.HolisticTracker()
fps = go.FPS()

try:
    while True:
        frame = camera.read()

        if frame is None:
            break

        result = tracker.detect(frame)
        face = "YES" if result.face else "NO"
        pose = "YES" if result.pose else "NO"
        info = (
            f"Face: {face} | Pose: {pose} | Hands: {len(result.hands)} | "
            f"FPS: {fps.read():.1f}"
        )
        print(f"\r{info:<80}", end="", flush=True)
except KeyboardInterrupt:
    pass
finally:
    print()
    camera.close()
    tracker.close()
