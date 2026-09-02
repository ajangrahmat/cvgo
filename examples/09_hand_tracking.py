"""Example 9: hand tracking, hand labels, and FPS."""

import cvgo as go


camera = go.Camera()
tracker = go.HandTracker()
fps = go.FPS()

while True:
    frame = camera.read()

    if frame is None:
        break

    hands = tracker.detect(frame)

    for hand in hands:
        hand.draw(frame)
        label = f"{hand.handedness}: {hand.confidence:.2f}"
        hand.box().draw(frame, label=label)

    go.put_text(frame, f"Hands: {len(hands)}")
    go.put_text(frame, f"FPS: {fps.read():.1f}", (20, 70))

    if not camera.show(frame, title="CVGO Hand Tracking"):
        break

camera.close()
tracker.close()
