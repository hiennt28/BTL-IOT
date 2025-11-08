# mqtt_mock_publisher.py
import time
import json
import random
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect("localhost", 1883)

device_serial = "ESP32-001"  # phải trùng với Devices.device_serial
topic = f"health_monitor/patient/{device_serial}/data"

while True:
    payload = {
        "device_serial": device_serial,  # BẮT BUỘC để listener nhận đúng patient
        "bpm": random.randint(60, 130),
        "avg_bpm": round(random.uniform(70, 100), 1),
        "ir_value": round(random.uniform(0.7, 1.0), 2),
        "accel_x": round(random.uniform(-1, 1), 2),
        "accel_y": round(random.uniform(-1, 1), 2),
        "accel_z": round(random.uniform(-1, 1), 2),
        # a_total sẽ được listener tính toán, nhưng có thể mock luôn
        "a_total": round(random.uniform(0, 2), 2)
    }
    client.publish(topic, json.dumps(payload))
    print("[MOCK SENT]", payload)
    time.sleep(3)
