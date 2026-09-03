"""CLI example 10: print body pose status."""

import cvgo as go


camera = go.Camera()
tracker = go.PoseTracker()
fps = go.FPS()

try:
    while True:
        frame = camera.read()

        if frame is None:
            break

        pose = tracker.detect(frame)
        status = "DETECTED" if pose else "NOT DETECTED"
        points = len(pose) if pose else 0
        info = (
            f"Pose: {status} | Landmarks: {points} | "
            f"FPS: {fps.read():.1f}"
        )
        print(f"\r{info:<80}", end="", flush=True)
except KeyboardInterrupt:
    pass
finally:
    print()
    camera.close()
    tracker.close()
