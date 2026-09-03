"""CLI example 9: print hand tracking results."""

import cvgo as go


camera = go.Camera()
tracker = go.HandTracker()
fps = go.FPS()

try:
    while True:
        frame = camera.read()

        if frame is None:
            break

        hands = tracker.detect(frame)
        labels = [
            f"{hand.handedness} ({hand.confidence:.2f})"
            for hand in hands
        ]
        details = ", ".join(labels) if labels else "NONE"
        info = (
            f"Hands: {len(hands)} | Detail: {details} | "
            f"FPS: {fps.read():.1f}"
        )
        print(f"\r{info:<100}", end="", flush=True)
except KeyboardInterrupt:
    pass
finally:
    print()
    camera.close()
    tracker.close()
