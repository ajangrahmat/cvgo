"""CLI example 19: publish pose status to an MQTT robot topic."""

import cvgo as go


camera = go.Camera()
tracker = go.PoseTracker(model_complexity=0)
mqtt = go.MqttClient(host="localhost", client_id="cvgo-camera", connect=True)
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
            mqtt.publish(
                "robot/camera/pose",
                {"person_detected": detected},
            )
            last_detected = detected

        info = (
            f"MQTT: {'DETECTED' if detected else 'CLEAR'} | "
            f"FPS: {fps.read():.1f}"
        )
        print(f"\r{info:<70}", end="", flush=True)
except KeyboardInterrupt:
    pass
finally:
    print()
    camera.close()
    tracker.close()
    mqtt.close()
