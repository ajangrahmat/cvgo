"""Example 19: publish pose status to an MQTT robot topic."""

import cvgo as go


camera = go.Camera()
tracker = go.PoseTracker(model_complexity=0)
mqtt = go.MqttClient(host="localhost", client_id="cvgo-camera", connect=True)
last_detected = None

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

    if pose:
        pose.box(padding=30).draw(frame, label="Person")
    go.put_text(frame, f"Person detected: {detected}")

    if not camera.show(frame, title="CVGO MQTT Robot"):
        break

camera.close()
tracker.close()
mqtt.close()
