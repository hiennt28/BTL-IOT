# mqtt_listenner (Python Script) - Đã sửa lỗi đèn không tắt khi dừng đo
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
MQTT_CONTROL_TOPIC = "health/control" 

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
            # print("Bo qua: Payload thieu 'device_serial'")
            return

        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            # 1. KIỂM TRA THIẾT BỊ
            cur.execute("SELECT device_id, is_measuring FROM Devices WHERE device_serial=%s", (device_serial,))
            device_row = cur.fetchone()

            if not device_row:
                print(f"Thiet bi la: {device_serial}")
                conn.close()
                return

            device_id = device_row['device_id']
           
            # Update trạng thái Online
            cur.execute("""
                UPDATE Devices 
                SET status='online', last_seen=NOW() 
                WHERE device_id=%s
            """, (device_id,))
            
            # ===========================================================
            # SỬA LỖI: NẾU ĐANG DỪNG ĐO -> GỬI LỆNH TẮT ĐÈN RỒI MỚI BỎ QUA
            # ===========================================================
            if device_row['is_measuring'] == 0:
                # Gửi lệnh OFF để đảm bảo đèn tắt
                control_payload = json.dumps({
                     "device_serial": device_serial,
                     "command": "LED_OFF"
                })
                client.publish(MQTT_CONTROL_TOPIC, control_payload)
                
                # print(f"[DA DUNG DO] {device_serial} -> Da gui lenh tat den.")
                
                conn.commit() 
                conn.close()
                return
            
            # ... (Các phần xử lý bên dưới giữ nguyên) ...
            
            # Tìm patient_id
            cur.execute("SELECT patient_id FROM Patients WHERE device_id=%s", (device_id,))
            patient_row = cur.fetchone()
            
            if not patient_row:
                print(f"Thiet bi {device_serial} chua duoc gan cho benh nhan nao.")
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
            print(f"[DATA] Patient {patient_id} | BPM: {bpm} | AI: {predicted_label}")

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

            # 6. XỬ LÝ CẢNH BÁO VÀ ĐIỀU KHIỂN ĐÈN
            dangerous_keywords = ["nguy hiểm", "bất thường", "ngã", "cảnh báo"]
            is_dangerous = any(keyword in predicted_label.lower() for keyword in dangerous_keywords)

            if is_dangerous:
                 # A. Lưu cảnh báo
                 cur.execute("""
                    INSERT INTO Alerts (patient_id, alert_type, message, status)
                    VALUES (%s, %s, %s, 'new')
                 """, (patient_id, "Cảnh báo AI", f"Phát hiện: {predicted_label}"))
                 
                 print(f"CANH BAO: {predicted_label} -> GUI LENH BAT DEN")

                 # B. Bật đèn
                 control_payload = json.dumps({
                     "device_serial": device_serial,
                     "command": "LED_ON",
                     "reason": predicted_label
                 })
                 client.publish(MQTT_CONTROL_TOPIC, control_payload)

            else:
                # Tắt đèn nếu bình thường
                if "bình thường" in predicted_label.lower() or "tốt" in predicted_label.lower():
                    control_payload = json.dumps({
                        "device_serial": device_serial,
                        "command": "LED_OFF"
                    })
                    client.publish(MQTT_CONTROL_TOPIC, control_payload)

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