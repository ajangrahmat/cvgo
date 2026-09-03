"""CLI example 5: send terminal input to Arduino."""

import cvgo as go


arduino = go.Serial()

try:
    if not arduino.connected:
        print("Arduino: NOT CONNECTED")
    else:
        print(f"Arduino: CONNECTED | Port: {arduino.port}")
        print("Type a value and press Enter. Type q to quit.")

        while True:
            value = input("Send > ").strip()

            if value.lower() == "q":
                break

            if value:
                status = "SENT" if arduino.send(value) else "FAILED"
                print(f"{status}: {value}")
except KeyboardInterrupt:
    print()
finally:
    arduino.close()
