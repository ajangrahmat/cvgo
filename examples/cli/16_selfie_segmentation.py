"""CLI example 16: print foreground coverage from segmentation."""

import cvgo as go


camera = go.Camera()
segmenter = go.SelfieSegmenter()
fps = go.FPS()

try:
    while True:
        frame = camera.read()

        if frame is None:
            break

        result = segmenter.segment(frame)
        coverage = result.foreground().mean() * 100
        info = (
            f"Person coverage: {coverage:.1f}% | "
            f"FPS: {fps.read():.1f}"
        )
        print(f"\r{info:<70}", end="", flush=True)
except KeyboardInterrupt:
    pass
finally:
    print()
    camera.close()
    segmenter.close()
