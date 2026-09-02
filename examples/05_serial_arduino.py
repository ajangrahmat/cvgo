"""Example 5: send data to Arduino."""

import cvgo as go


arduino = go.Serial()

if arduino.connected:
    arduino.send("1")

arduino.close()

