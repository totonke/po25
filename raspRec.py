import serial
import requests
import datetime

SERIAL_PORT = "/dev/ttyS0"
BAUDRATE = 9600

SERVER_IP = "192.168.52.210"
PORT = 8000
PATH = "/gn/receive"

POST_URL = f"http://{SERVER_IP}:{PORT}{PATH}"


ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)

# dataNo = 0 #データ番号
dataAmount = 3 # Arduinoが時間送るなら4、送らないなら3

print("Gateway started")

try:
    while True:
        data = ser.readline()
        if data is None or len(data) == 0:
            continue

        line = data.decode("utf-8", errors="ignore").strip()
        if len(line) == 0:
            continue

        # Example expected: device1,23.40,456,2025/12/17 15:10:00
        parts = line.split(",")

        if len(parts) < dataAmount :
            print(f"SKIP (bad format): {line}")
            continue

        device = parts[0].strip()
        temp = parts[1].strip()
        light = parts[2].strip()
        now = datetime.datetime.now()
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")

        # dataNo += 1

        payload = {
            # "dataNo": str(dataNo),
            "device": device,
            "temp": temp,
            "light": light,
            "time": time_str
        }

        print(f"RECV: {payload}")

        # SDカード（ローカル）保存
        log_line = f"{device},{temp},{light},{time_str}\n"

        try:
            with open("LoRa_test.txt", "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            print(f"SD WRITE ERROR: {e}")
        
        
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
