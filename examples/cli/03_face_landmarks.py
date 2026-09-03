"""CLI example 3: print face and landmark counts."""

import cvgo as go


camera = go.Camera()
landmarker = go.FaceLandmarks()
fps = go.FPS()

try:
    while True:
        frame = camera.read()

        if frame is None:
            break

        faces = landmarker.detect(frame)
        points = sum(len(face) for face in faces)
        info = (
            f"Faces: {len(faces)} | Landmarks: {points} | "
            f"FPS: {fps.read():.1f}"
        )
        print(f"\r{info:<70}", end="", flush=True)
except KeyboardInterrupt:
    pass
finally:
    print()
    camera.close()
    landmarker.close()
