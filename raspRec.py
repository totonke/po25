import serial
import requests
import datetime

SERIAL_PORT = "/dev/ttyS0"
BAUDRATE = 9600

SERVER_IP = "192.168.52.239"  # change to your server
POST_URL = f"http://{SERVER_IP}/formpost"

ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)

seq = 0

print("Gateway started")

try:
    while True:
        raw = ser.readline()
        if raw is None or len(raw) == 0:
            continue

        line = raw.decode("utf-8", errors="ignore").strip()
        if len(line) == 0:
            continue

        # Example expected: device1,23.40,456,2025/12/17 15:10:00
        parts = line.split(",")

        if len(parts) < 4:
            print(f"SKIP (bad format): {line}")
            continue

        device = parts[0].strip()
        temp = parts[1].strip()
        light = parts[2].strip()
        time_str = ",".join(parts[3:]).strip()  # safe if time contains spaces

        seq += 1

        payload = {
            "seq": str(seq),
            "device": device,
            "temp": temp,
            "light": light,
            "time": time_str
        }

        print(f"RECV: {payload}")

        try:
            r = requests.post(POST_URL, data=payload, timeout=3)
            print(f"POST: {r.status_code} {r.text[:80]}")
        except Exception as e:
            print(f"POST ERROR: {e}")

except KeyboardInterrupt:
    print("Stopped by user")

finally:
    ser.close()
    print("Gateway stopped")
