"""CLI example 20: send pose status to a WebSocket robot service."""

import cvgo as go


camera = go.Camera()
tracker = go.PoseTracker(model_complexity=0)
websocket = go.WebSocketClient("ws://localhost:8080", connect=True)
fps = go.FPS()
last_detected = None

try:
    while True:
        frame = camera.read()

        if frame is None:
            break

        pose = tracker.detect(frame)
        detected = pose is not None

        if detected != last_detected:
            websocket.send({"person_detected": detected})
            last_detected = detected

        info = (
            f"WebSocket: {'DETECTED' if detected else 'CLEAR'} | "
            f"FPS: {fps.read():.1f}"
        )
        print(f"\r{info:<70}", end="", flush=True)
except KeyboardInterrupt:
    pass
finally:
    print()
    camera.close()
    tracker.close()
    websocket.close()
