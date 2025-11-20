# mqtt_listenner (Python Script)
import json
import pymysql
import math
import ssl
import time
import paho.mqtt.client as mqtt
from model_loader import predict_status
from datetime import datetime

# =================================================================
# CẤU HÌNH MQTT
# =================================================================
MQTT_BROKER = "8c9b9eafe2434729af707f153e31a91f.s1.eu.hivemq.cloud"
MQTT_USER = "nhom5"
MQTT_PASSWORD = "Abc123456"
MQTT_PORT = 8883
MQTT_TOPIC = "health/data"

# =================================================================
# CẤU HÌNH DATABASE
# =================================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",    
    "db": "health_monitor",
    "cursorclass": pymysql.cursors.DictCursor
}

# =================================================================
# HÀM XỬ LÝ
# =================================================================

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("KET NOI THANH CONG toi HiveMQ Cloud!")
        client.subscribe(MQTT_TOPIC)
        print(f"Dang lang nghe topic: {MQTT_TOPIC}")
    else:
        print(f"Ket noi that bai! Ma loi (rc): {rc}")

def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode('utf-8')
        data = json.loads(payload_str)

        device_serial = data.get("device_serial")
        if not device_serial:
            print("Bo qua: Payload thieu 'device_serial'")
            return

        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            # 1. KIỂM TRA THIẾT BỊ
            cur.execute("SELECT device_id, is_measuring FROM Devices WHERE device_serial=%s", (device_serial,))
            device_row = cur.fetchone()

            if not device_row:
                print(f"⚠️ Thiet bi la: {device_serial}")
                conn.close()
                return

            device_id = device_row['device_id']

           
            # Dòng này sẽ giúp web hiển thị "Online" ngay khi có dữ liệu
            cur.execute("""
                UPDATE Devices 
                SET status='online', last_seen=NOW() 
                WHERE device_id=%s
            """, (device_id,))
            # ===========================================================

            # NẾU ĐANG DỪNG ĐO -> BỎ QUA (Nhưng vẫn update online ở trên để biết thiết bị sống)
            if device_row['is_measuring'] == 0:
                # print(f"⏸️ [DUNG DO] Thiet bi {device_serial} dang tat chuc nang do.")
                conn.commit() # Commit để lưu trạng thái Online
                conn.close()
                return
            
            # Tìm patient_id
            cur.execute("SELECT patient_id FROM Patients WHERE device_id=%s", (device_id,))
            patient_row = cur.fetchone()
            
            if not patient_row:
                print(f"⚠️ Thiet bi {device_serial} chua duoc gan cho benh nhan nao.")
                conn.close()
                return

            patient_id = patient_row["patient_id"]

            # 2. Tính toán dữ liệu
            bpm = float(data.get("bpm", 0))
            accel_x = float(data.get("accel_x", 0))
            accel_y = float(data.get("accel_y", 0))
            accel_z = float(data.get("accel_z", 0))
            a_total = math.sqrt(accel_x**2 + accel_y**2 + accel_z**2)

            # 3. GỌI AI DỰ ĐOÁN
            predicted_label = predict_status(bpm, a_total)
            print(f"🟢 [DATA] Patient {patient_id} | BPM: {bpm} | AI: {predicted_label}")

            # 4. Lưu HealthData
            sql_insert = """
                INSERT INTO HealthData 
                (patient_id, bpm, ir_value, accel_x, accel_y, accel_z, a_total, predicted_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql_insert, (
                patient_id, bpm, data.get("ir_value", 0),
                accel_x, accel_y, accel_z, a_total, predicted_label
            ))
            
            # 5. Cập nhật trạng thái bệnh nhân
            cur.execute("UPDATE Patients SET current_health_status = %s WHERE patient_id = %s", (predicted_label, patient_id))

            # 6. Tạo cảnh báo nếu cần
            if "nguy hiểm" in predicted_label.lower() or "bất thường" in predicted_label.lower() or "ngã" in predicted_label.lower():
                 cur.execute("""
                    INSERT INTO Alerts (patient_id, alert_type, message, status)
                    VALUES (%s, %s, %s, 'new')
                 """, (patient_id, "Cảnh báo AI", f"Phát hiện: {predicted_label}"))
                 print(f"🚨 CANH BAO: {predicted_label}")

            conn.commit()

        conn.close()

    except json.JSONDecodeError:
        print("Loi: Payload JSON khong hop le")
    except Exception as e:
        print(f"Loi he thong: {e}")

# =================================================================
# CHẠY CHƯƠNG TRÌNH
# =================================================================
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.tls_set(tls_version=ssl.PROTOCOL_TLS)
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

print("---------------------------------------------------")
print(f"Dang ket noi toi HiveMQ Cloud: {MQTT_BROKER}")
print("---------------------------------------------------")

try:
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_forever()
except Exception as e:
    print(f"\nKHONG THE KET NOI MQTT! {e}")