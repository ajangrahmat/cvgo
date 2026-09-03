"""CLI example 1: read camera information without a preview window."""

import cvgo as go


camera = go.Camera()
fps = go.FPS()

try:
    while True:
        frame = camera.read()

        if frame is None:
            break

        height, width = frame.shape[:2]
        info = f"Camera: ON | Size: {width}x{height} | FPS: {fps.read():.1f}"
        print(f"\r{info:<70}", end="", flush=True)
except KeyboardInterrupt:
    pass
finally:
    print()
    camera.close()
