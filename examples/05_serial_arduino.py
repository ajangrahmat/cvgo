"""Contoh 5: mengirim data ke Arduino."""

import cvgo as go


arduino = go.Serial()

if arduino.connected:
    arduino.send("1")

arduino.close()

