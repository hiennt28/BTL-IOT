# mqtt_listener.py
import json
import pymysql
import math
import paho.mqtt.client as mqtt
from model_loader import predict_status # <-- IMPORT HÀM DỰ ĐOÁN AI

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
                conn.close() # Đóng kết nối trước khi return
                return
                
            patient_id = patient_row["patient_id"]

            # Lấy dữ liệu và tính toán
            bpm = float(data.get("bpm", 0)) # Lấy BPM
            accel_x = float(data.get("accel_x", 0))
            accel_y = float(data.get("accel_y", 0))
            accel_z = float(data.get("accel_z", 0))
            a_total = math.sqrt(accel_x**2 + accel_y**2 + accel_z**2) # Tính A_total

            # === BẮT ĐẦU TÍCH HỢP AI ===
            # Gọi mô hình AI để dự đoán
            predicted_label = predict_status(bpm, a_total)
            print(f"[AI PREDICTION] Patient {patient_id}: {predicted_label}")
            # === KẾT THÚC TÍCH HỢP AI ===

            # Lưu vào HealthData (bao gồm cả dự đoán)
            cur.execute("""
                INSERT INTO HealthData 
                (patient_id, bpm, ir_value, accel_x, accel_y, accel_z, a_total, predicted_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                patient_id,
                bpm,
                data.get("ir_value", 0),
                accel_x,
                accel_y,
                accel_z,
                a_total,
                predicted_label # <-- Thêm trạng thái dự đoán
            ))
            
            # Cập nhật trạng thái mới nhất cho Bệnh nhân
            cur.execute("""
                UPDATE Patients 
                SET current_health_status = %s
                WHERE patient_id = %s
            """, (predicted_label, patient_id))

            conn.commit()

            # (Xóa logic cảnh báo BPM cũ, vì AI đã xử lý)
            # Bạn có thể giữ lại nếu muốn cảnh báo song song

        conn.close()

    except Exception as e:
        print(f"Lỗi xử lý MQTT: {e}")


# === Khởi tạo MQTT client ===
client = mqtt.Client()
client.on_message = on_message
client.connect("localhost", 1883)
client.subscribe("health_monitor/patient/+/data")  # subscribe tất cả patient

print("MQTT Listener (với AI) đang chạy...")
client.loop_forever()