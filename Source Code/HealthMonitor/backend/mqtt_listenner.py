# mqtt_listener.py
import json
import pymysql
import math
import paho.mqtt.client as mqtt

# === Cấu hình DB ===
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "db": "health_monitor",
    "cursorclass": pymysql.cursors.DictCursor  # để fetch dict thay vì tuple
}

# === Hàm xử lý dữ liệu MQTT ===
def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        print(f"[MQTT RECEIVED] {data}")

        device_serial = data.get("device_serial")
        if not device_serial:
            print("⚠️  Payload thiếu device_serial!")
            return

        # Mở kết nối DB
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            # Lấy patient_id từ device_serial
            cur.execute("""
                SELECT patient_id FROM Patients
                WHERE device_id = (SELECT device_id FROM Devices WHERE device_serial=%s)
            """, (device_serial,))
            patient_row = cur.fetchone()
            if not patient_row:
                print(f"⚠️  Không tìm thấy bệnh nhân cho thiết bị {device_serial}")
                return
            patient_id = patient_row["patient_id"]

            # Tính a_total
            accel_x = float(data.get("accel_x", 0))
            accel_y = float(data.get("accel_y", 0))
            accel_z = float(data.get("accel_z", 0))
            a_total = math.sqrt(accel_x**2 + accel_y**2 + accel_z**2)

            # Lưu vào HealthData
            cur.execute("""
                INSERT INTO HealthData 
                (patient_id, bpm, ir_value, accel_x, accel_y, accel_z, a_total)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                patient_id,
                data.get("bpm"),
                data.get("ir_value", 0),
                accel_x,
                accel_y,
                accel_z,
                a_total
            ))
            conn.commit()

            # Kiểm tra cảnh báo nhịp tim
            bpm = data.get("bpm", 0)
            if bpm > 100:
                alert_msg = f"Nhịp tim cao: {bpm}"
                cur.execute("""
                    INSERT INTO Alerts (patient_id, alert_type, message)
                    VALUES (%s, %s, %s)
                """, (patient_id, "High BPM", alert_msg))
                conn.commit()
                print(f"⚠️  Cảnh báo đã lưu: {alert_msg}")

        conn.close()

    except Exception as e:
        print("Lỗi xử lý MQTT:", e)


# === Khởi tạo MQTT client ===
client = mqtt.Client()
client.on_message = on_message
client.connect("localhost", 1883)
client.subscribe("health_monitor/patient/+/data")  # subscribe tất cả patient

print("MQTT Listener is running...")
client.loop_forever()
