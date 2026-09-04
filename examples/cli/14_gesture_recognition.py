"""CLI example 14: print recognized hand gestures."""

import cvgo as go


camera = go.Camera()
recognizer = go.GestureRecognizer()
fps = go.FPS()

try:
    while True:
        frame = camera.read()

        if frame is None:
            break

        gestures = recognizer.detect(frame)
        labels = [
            f"{gesture.label} ({gesture.score:.2f})"
            for gesture in gestures
            if gesture.recognized
        ]
        details = ", ".join(labels) if labels else "NONE"
        info = f"Gestures: {details} | Loop FPS: {fps.read():.1f}"
        print(f"\r{info:<100}", end="", flush=True)
except KeyboardInterrupt:
    pass
finally:
    print()
    camera.close()
    recognizer.close()
