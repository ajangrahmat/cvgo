"""Example 20: send pose status to a WebSocket robot service."""

import cvgo as go


camera = go.Camera()
tracker = go.PoseTracker(model_complexity=0)
websocket = go.WebSocketClient("ws://localhost:8080", connect=True)
last_detected = None

while True:
    frame = camera.read()

    if frame is None:
        break

    pose = tracker.detect(frame)
    detected = pose is not None

    if detected != last_detected:
        websocket.send({"person_detected": detected})
        last_detected = detected

    if pose:
        pose.box(padding=30).draw(frame, label="Person")
    go.put_text(frame, f"Person detected: {detected}")

    if not camera.show(frame, title="CVGO WebSocket Robot"):
        break

camera.close()
tracker.close()
websocket.close()
