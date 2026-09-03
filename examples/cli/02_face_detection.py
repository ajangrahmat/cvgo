"""CLI example 2: print face detection status."""

import cvgo as go


camera = go.Camera()
detector = go.FaceDetector()
fps = go.FPS()

try:
    while True:
        frame = camera.read()

        if frame is None:
            break

        faces = detector.detect(frame)
        status = "DETECTED" if faces else "NOT DETECTED"
        info = (
            f"Face: {status} | Count: {len(faces)} | "
            f"FPS: {fps.read():.1f}"
        )
        print(f"\r{info:<70}", end="", flush=True)
except KeyboardInterrupt:
    pass
finally:
    print()
    camera.close()
    detector.close()
