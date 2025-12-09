import json
import pymysql
import math
import ssl
import time
import threading
import paho.mqtt.client as mqtt
from model_loader import predict_status
from datetime import datetime
import base64

# ===================== CẤU HÌNH MQTT =====================
MQTT_BROKER = "d2c7e1d6b7ff4636af82a88c157ff0a5.s1.eu.hivemq.cloud"
MQTT_USER = "nhom5"
MQTT_PASSWORD = "Abc123456"
MQTT_PORT = 8883
MQTT_TOPIC = "health/data"
MQTT_CONTROL_TOPIC = "health/control"
MQTT_OTA_TOPIC = "health/ota"
MQTT_OTA_STATUS_TOPIC = "health/ota_status"

# ===================== CẤU HÌNH DATABASE =====================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "db": "health_monitor",
    "cursorclass": pymysql.cursors.DictCursor
}

# ===================== STORE OTA STATUS =====================
ota_status_store = {}  # lưu trạng thái OTA của các thiết bị

# ===================== MQTT CLIENT =====================
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.tls_set(tls_version=ssl.PROTOCOL_TLS)

# ===================== HÀM XỬ LÝ =====================
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("MQTT kết nối thành công!")
        client.subscribe(MQTT_TOPIC)
        client.subscribe(MQTT_OTA_STATUS_TOPIC)
        print(f"Đang lắng nghe topics: {MQTT_TOPIC}, {MQTT_OTA_STATUS_TOPIC}")
    else:
        print(f"MQTT kết nối thất bại, rc={rc}")

def handle_health_data(data):
    """Xử lý dữ liệu health từ ESP32"""
    device_serial = data.get("device_serial")
    if not device_serial:
        return

    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            # Kiểm tra thiết bị
            cur.execute("SELECT device_id, is_measuring FROM Devices WHERE device_serial=%s", (device_serial,))
            device_row = cur.fetchone()
            if not device_row:
                conn.close()
                return

            device_id = device_row['device_id']
            cur.execute("UPDATE Devices SET status='online', last_seen=NOW() WHERE device_id=%s", (device_id,))

            if device_row['is_measuring'] == 0:
                # Gửi LED_OFF nếu đang dừng đo
                control_payload = json.dumps({"device_serial": device_serial, "command": "LED_OFF"})
                client.publish(MQTT_CONTROL_TOPIC, control_payload, qos=1)
                conn.commit()
                conn.close()
                return

            # Tìm patient
            cur.execute("SELECT patient_id FROM Patients WHERE device_id=%s", (device_id,))
            patient_row = cur.fetchone()
            if not patient_row:
                conn.close()
                return
            patient_id = patient_row["patient_id"]

            # Tính toán dữ liệu
            bpm = float(data.get("bpm", 0))
            accel_x = float(data.get("accel_x", 0))
            accel_y = float(data.get("accel_y", 0))
            accel_z = float(data.get("accel_z", 0))
            a_total = math.sqrt(accel_x**2 + accel_y**2 + accel_z**2)

            # Dự đoán AI
            predicted_label = predict_status(bpm, a_total)
            print(f"[DATA] Patient {patient_id} | BPM: {bpm} | AI: {predicted_label}")

            # Lưu HealthData
            cur.execute("""
                INSERT INTO HealthData (patient_id, bpm, ir_value, accel_x, accel_y, accel_z, a_total, predicted_status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (patient_id, bpm, data.get("ir_value", 0), accel_x, accel_y, accel_z, a_total, predicted_label))

            # Cập nhật trạng thái bệnh nhân
            cur.execute("UPDATE Patients SET current_health_status=%s WHERE patient_id=%s", (predicted_label, patient_id))

            # Xử lý cảnh báo
            dangerous_keywords = ["nguy hiểm", "bất thường", "ngã", "cảnh báo"]
            is_dangerous = any(keyword in predicted_label.lower() for keyword in dangerous_keywords)
            if is_dangerous:
                cur.execute("""
                    INSERT INTO Alerts (patient_id, alert_type, message, status)
                    VALUES (%s, %s, %s, 'new')
                """, (patient_id, "Cảnh báo AI", f"Phát hiện: {predicted_label}"))

                control_payload = json.dumps({"device_serial": device_serial, "command": "LED_ON", "reason": predicted_label})
                client.publish(MQTT_CONTROL_TOPIC, control_payload, qos=1)
            else:
                control_payload = json.dumps({"device_serial": device_serial, "command": "LED_OFF"})
                client.publish(MQTT_CONTROL_TOPIC, control_payload, qos=1)

            conn.commit()
        conn.close()
    except Exception as e:
        print(f"Lỗi xử lý health data: {e}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        if msg.topic == MQTT_TOPIC:
            handle_health_data(payload)
        elif msg.topic == MQTT_OTA_STATUS_TOPIC:
            handle_ota_status(payload)
    except Exception as e:
        print(f"Lỗi khi nhận message: {e}")

# Hàm kiểm tra offline
def check_offline():
    while True:
        try:
            conn = pymysql.connect(**DB_CONFIG)
            with conn.cursor() as cur:
                cur.execute("UPDATE Devices SET status='offline' WHERE last_seen < NOW() - INTERVAL 60 SECOND")
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"Lỗi khi cập nhật offline: {e}")
        time.sleep(30)

# ===================== RUN STANDALONE =====================

ota_start_times = {}
from datetime import datetime, timedelta
def check_ota_timeout():
    """Kiểm tra các OTA timeout (quá 5 phút không có phản hồi)"""
    while True:
        try:
            current_time = datetime.now()
            timeout_devices = []
            
            for device_serial, start_time in ota_start_times.items():
                if current_time - start_time > timedelta(minutes=5):
                    # Timeout
                    if device_serial in ota_status_store:
                        status = ota_status_store[device_serial].get("status")
                        if status not in ["success","error"]:
                            ota_status_store[device_serial] = {
                                "progress": 0,
                                "status": "error",
                                "reason": "Timeout - Thiết bị không phản hồi"
                            }
                            timeout_devices.append(device_serial)
            
            # Xóa các thiết bị đã timeout khỏi tracking
            for device_serial in timeout_devices:
                ota_start_times.pop(device_serial, None)
                print(f"[OTA TIMEOUT] {device_serial} không phản hồi sau 5 phút")
            
        except Exception as e:
            print(f"Lỗi kiểm tra OTA timeout: {e}")
        
        time.sleep(60)  # Kiểm tra mỗi phút


# ============================================
# CẬP NHẬT: Hàm gửi OTA với tracking
# File: mqtt_listener.py - Cập nhật hàm send_ota_command
# ============================================

def send_ota_command(device_serial, firmware_file_path):
    """Gửi lệnh OTA với tracking thời gian"""
    try:
        with open(firmware_file_path, "rb") as f:
            firmware_data = f.read()
        
        firmware_b64 = base64.b64encode(firmware_data).decode()
        
        # Khởi tạo trạng thái
        ota_status_store[device_serial] = {
            "progress": 0,
            "status": "idle",
            "reason": ""
        }
        
        # Lưu thời gian bắt đầu
        ota_start_times[device_serial] = datetime.now()
        
        payload = {
            "device_serial": device_serial,
            "command": "START_OTA",
            "firmware_data": firmware_b64
        }
        
        client.publish(MQTT_OTA_TOPIC, json.dumps(payload))
        print(f"[OTA] Đã gửi lệnh OTA tới {device_serial}")
        
    except Exception as e:
        print(f"[OTA ERROR] Không thể gửi OTA: {e}")
        ota_status_store[device_serial] = {
            "progress": 0,
            "status": "error",
            "reason": str(e)
        }


# ============================================
# CẬP NHẬT: Hàm xử lý OTA status với cleanup
# File: mqtt_listener.py - Cập nhật handle_ota_status
# ============================================

def handle_ota_status(data):
    """Xử lý trạng thái OTA từ ESP32 với cleanup"""
    device_serial = data.get("device_serial")
    progress = data.get("progress")
    status = data.get("status")
    reason = data.get("reason", "")

    if device_serial and progress is not None:
        ota_status_store[device_serial] = {
            "progress": progress,
            "status": status,
            "reason": reason
        }
        print(f"[OTA STATUS] {device_serial} -> {progress}% | Status: {status}")
        
        # Nếu hoàn thành hoặc lỗi, xóa khỏi tracking
        if status in ["success", "error"]:
            ota_start_times.pop(device_serial, None)
            
            # Tự động xóa sau 1 phút để không làm đầy bộ nhớ
            def clear_status():
                time.sleep(60)
                ota_status_store.pop(device_serial, None)
                print(f"[OTA] Đã xóa trạng thái của {device_serial}")
            
            threading.Thread(target=clear_status, daemon=True).start()


if __name__ == "__main__":
    offline_thread = threading.Thread(target=check_offline, daemon=True)
    offline_thread.start()

    client.on_connect = on_connect
    client.on_message = on_message
    
    # Thread kiểm tra OTA timeout
    ota_timeout_thread = threading.Thread(target=check_ota_timeout, daemon=True)
    ota_timeout_thread.start()

    print(f"Đang kết nối MQTT: {MQTT_BROKER}")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.loop_forever()
    except Exception as e:
        print(f"KHÔNG THỂ KẾT NỐI MQTT! {e}")
else:
    print("[MQTT_LISTENER] Được import từ Flask, khởi động background loop...")
    try:
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()  # Background loop
        print("[MQTT_LISTENER] MQTT client sẵn sàng (background mode)")
    except Exception as e:
        print(f"[MQTT_LISTENER] Lỗi: {e}")