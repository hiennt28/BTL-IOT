# mqtt_listenner (Python Script)
import json
import pymysql
import math
import ssl
import time
import paho.mqtt.client as mqtt
from model_loader import predict_status

# =================================================================
# CẤU HÌNH MQTT (QUAN TRỌNG: BẠN PHẢI ĐIỀN THÔNG TIN CỦA BẠN)
# =================================================================

# 1. Lấy Cluster URL từ tab "Overview" trên HiveMQ Cloud
# Ví dụ: "8c9b9eafe2434729af707f153e31a91f.s1.eu.hivemq.cloud"
MQTT_BROKER = "8c9b9eafe2434729af707f153e31a91f.s1.eu.hivemq.cloud"

# 2. Tạo Username/Password trong tab "Access Management" trên HiveMQ Cloud
MQTT_USER = "nhom5"
MQTT_PASSWORD = "Abc123456"

# 3. Cổng mặc định của HiveMQ Cloud là 8883 (SSL)
MQTT_PORT = 8883
MQTT_TOPIC = "health/data"  # Khớp với hình ảnh bạn gửi

# =================================================================
# CẤU HÌNH DATABASE (MySQL/XAMPP Localhost)
# =================================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",     # Để trống nếu dùng XAMPP mặc định
    "db": "health_monitor",
    "cursorclass": pymysql.cursors.DictCursor
}

# =================================================================
# HÀM XỬ LÝ
# =================================================================

def on_connect(client, userdata, flags, rc, properties=None):
    """Hàm gọi khi kết nối thành công tới Broker"""
    if rc == 0:
        print("KET NOI THANH CONG toi HiveMQ Cloud!")
        client.subscribe(MQTT_TOPIC)
        print(f"Dang lang nghe topic: {MQTT_TOPIC}")
    else:
        print(f"Ket noi that bai! Ma loi (rc): {rc}")
        # rc=5: Sai username/password, rc=1: Sai protocol version

def on_message(client, userdata, msg):
    """Hàm gọi khi nhận được tin nhắn mới"""
    try:
        payload_str = msg.payload.decode('utf-8')
        data = json.loads(payload_str)
        # print(f"\n[NHAN DATA] {data}") # Tạm tắt log chi tiết để đỡ rối

        device_serial = data.get("device_serial")
        if not device_serial:
            print("Bo qua: Payload thieu 'device_serial'")
            return

        # --- KẾT NỐI DATABASE ---
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            # 1. KIỂM TRA TRẠNG THÁI 'is_measuring' CỦA THIẾT BỊ
            # Chỉ xử lý nếu thiết bị được phép đo
            cur.execute("SELECT device_id, is_measuring FROM Devices WHERE device_serial=%s", (device_serial,))
            device_row = cur.fetchone()

            if not device_row:
                print(f"⚠️ Thiet bi la: {device_serial}")
                conn.close()
                return

            # NẾU ĐANG DỪNG ĐO -> BỎ QUA
            if device_row['is_measuring'] == 0:
                print(f"⏸️ [DUNG DO] Thiet bi {device_serial} dang tat chuc nang do. Bo qua du lieu.")
                conn.close()
                return
            
            # Nếu đang đo, tiếp tục tìm patient_id
            cur.execute("SELECT patient_id FROM Patients WHERE device_id=%s", (device_row['device_id'],))
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
            
            # Tính a_total (Vector tổng gia tốc)
            a_total = math.sqrt(accel_x**2 + accel_y**2 + accel_z**2)

            # 3. GỌI AI DỰ ĐOÁN TRẠNG THÁI
            predicted_label = predict_status(bpm, a_total)
            print(f"🟢 [LUU DATA] Patient {patient_id}: {predicted_label} (BPM:{bpm})")

            # 4. Lưu vào bảng HealthData
            sql_insert = """
                INSERT INTO HealthData 
                (patient_id, bpm, ir_value, accel_x, accel_y, accel_z, a_total, predicted_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql_insert, (
                patient_id,
                bpm,
                data.get("ir_value", 0),
                accel_x,
                accel_y,
                accel_z,
                a_total,
                predicted_label
            ))
            
            # 5. Cập nhật trạng thái hiện tại cho Bệnh nhân
            cur.execute("""
                UPDATE Patients 
                SET current_health_status = %s
                WHERE patient_id = %s
            """, (predicted_label, patient_id))

            # 6. Logic tạo cảnh báo
            if "nguy hiểm" in predicted_label.lower() or "bất thường" in predicted_label.lower() or "ngã" in predicted_label.lower():
                 cur.execute("""
                    INSERT INTO Alerts (patient_id, alert_type, message, status)
                    VALUES (%s, %s, %s, 'new')
                 """, (patient_id, "Cảnh báo Sức khỏe (AI)", f"Phát hiện: {predicted_label}",))
                 print(f"🚨 Da tao canh bao cho benh nhan {patient_id}")

            conn.commit()
            # print("Da luu du lieu vao Database.")

        conn.close()

    except json.JSONDecodeError:
        print("Loi: Payload khong phai JSON hop le")
    except pymysql.MySQLError as e:
        print(f"Loi Database: {e}")
    except Exception as e:
        print(f"Loi khong xac dinh: {e}")

# =================================================================
# CHẠY CHƯƠNG TRÌNH
# =================================================================

# Khởi tạo Client với Version 2 (Sửa lỗi DeprecationWarning)
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# Cấu hình Callback
client.on_connect = on_connect
client.on_message = on_message

# Cấu hình bảo mật TLS (BẮT BUỘC CHO HIVEMQ CLOUD)
client.tls_set(tls_version=ssl.PROTOCOL_TLS)

# Cấu hình xác thực (Username/Password)
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

print("---------------------------------------------------")
print(f"Dang ket noi toi HiveMQ Cloud: {MQTT_BROKER}")
print("---------------------------------------------------")

try:
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_forever()
except Exception as e:
    print(f"\nKHONG THE KET NOI MQTT!")
    print(f"Chi tiet loi: {e}")