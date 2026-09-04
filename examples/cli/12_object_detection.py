"""CLI example 12: print detected object labels and scores."""

import cvgo as go


camera = go.Camera()
detector = go.ObjectDetector()
fps = go.FPS()

try:
    while True:
        frame = camera.read()

        if frame is None:
            break

        objects = detector.detect(frame)
        labels = [
            f"{item.label} ({item.score:.2f})"
            for item in objects[:3]
        ]
        details = ", ".join(labels) if labels else "NONE"
        info = (
            f"Objects: {len(objects)} | Top: {details} | "
            f"Loop FPS: {fps.read():.1f}"
        )
        print(f"\r{info:<120}", end="", flush=True)
except KeyboardInterrupt:
    pass
finally:
    print()
    camera.close()
    detector.close()
