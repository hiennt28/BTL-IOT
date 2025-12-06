# routes/patients.py
from flask import Blueprint, jsonify, request
from db import get_db_connection
import paho.mqtt.client as mqtt
import json
import ssl
import time

# CẤU HÌNH MQTT 
MQTT_BROKER = "8c9b9eafe2434729af707f153e31a91f.s1.eu.hivemq.cloud"
MQTT_USER = "nhom5"
MQTT_PASSWORD = "Abc123456"
MQTT_PORT = 8883
MQTT_CONTROL_TOPIC = "health/control"

patients_bp = Blueprint('patients', __name__)

# Lấy thông tin bệnh nhân KÈM THÔNG TIN THIẾT BỊ
@patients_bp.route('/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.*, d.full_name as doctor_name, 
               dev.device_serial, dev.status as device_status, dev.is_measuring, dev.last_seen,
               TIMESTAMPDIFF(SECOND, dev.last_seen, NOW()) as seconds_since_seen
        FROM `Patients` p
        LEFT JOIN `Doctors` d ON p.doctor_id = d.doctor_id
        LEFT JOIN `Devices` dev ON p.device_id = dev.device_id
        WHERE p.patient_id = %s
    """, (patient_id,))
    
    patient = cursor.fetchone()

    cursor.close()
    conn.close()

    if not patient:
        return jsonify({"message": "Không tìm thấy bệnh nhân!"}), 404

    # Logic kiểm tra Online/Offline
    if patient.get('device_serial'):
        seconds = patient.get('seconds_since_seen')
        if seconds is None or seconds > 15: 
            patient['device_status'] = 'offline'
        else:
            patient['device_status'] = 'online'

    return jsonify(patient)

# Cập nhật thông tin cá nhân
@patients_bp.route('/update/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
        UPDATE Patients
        SET full_name = %s, phone_number = %s, address = %s, date_of_birth = %s
        WHERE patient_id = %s
    """
    cursor.execute(sql, (
        data.get('full_name'),
        data.get('phone_number'),
        data.get('address'),
        data.get('date_of_birth'),
        patient_id
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Cập nhật thông tin thành công!"})

# API Bật/Tắt chế độ đo
@patients_bp.route('/<int:patient_id>/device/control', methods=['POST'])
def control_device(patient_id):
    data = request.get_json()
    action = data.get('action') 
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT device_id FROM Patients WHERE patient_id = %s", (patient_id,))
    result = cursor.fetchone()
    
    if not result or not result[0]:
        cursor.close(); conn.close()
        return jsonify({"success": False, "message": "Bệnh nhân chưa được gán thiết bị!"}), 400
        
    device_id = result[0]
    
    new_status = 1 if action == 'start' else 0
    
    try:
        cursor.execute("UPDATE Devices SET is_measuring = %s WHERE device_id = %s", (new_status, device_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": f"Đã {'BẮT ĐẦU' if new_status else 'DỪNG'} đo."})
    except Exception as e:
        print(e)
        return jsonify({"success": False, "message": "Lỗi server"}), 500

# === API MỚI: CẤU HÌNH WIFI ===
@patients_bp.route('/<int:patient_id>/device/wifi-config', methods=['POST'])
def config_wifi(patient_id):
    print(f"\n--- [DEBUG] Bắt đầu cấu hình Wifi cho Patient ID: {patient_id} ---")
    
    data = request.get_json()
    ssid = data.get('ssid')
    password = data.get('password', '')

    if not ssid:
        return jsonify({"success": False, "message": "Vui lòng nhập tên Wifi"}), 400

    conn = get_db_connection()
    if not conn:
        print("--- [ERROR] Lỗi kết nối DB ---")
        return jsonify({"success": False, "message": "Lỗi DB"}), 500
        
    cursor = conn.cursor()

    # Lấy serial thiết bị của bệnh nhân
    cursor.execute("""
        SELECT d.device_serial 
        FROM Patients p 
        JOIN Devices d ON p.device_id = d.device_id 
        WHERE p.patient_id = %s
    """, (patient_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result:
        print("--- [ERROR] Không tìm thấy thiết bị ---")
        return jsonify({"success": False, "message": "Bệnh nhân chưa có thiết bị!"}), 404
    
    device_serial = result[0]
    print(f"--- [DEBUG] Device Serial: {device_serial} ---")

    # Gửi lệnh qua MQTT
    try:
        payload = json.dumps({
            "device_serial": device_serial,
            "command": "UPDATE_WIFI",
            "ssid": ssid,
            "password": password
        })
        
        # --- CẤU HÌNH MQTT CLIENT  ---
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
      
        client.tls_set(cert_reqs=ssl.CERT_NONE, tls_version=ssl.PROTOCOL_TLS)
        
        # Biến cờ để kiểm tra kết nối
        connection_flag = False

        def on_connect(client, userdata, flags, rc, properties=None):
            nonlocal connection_flag
            if rc == 0:
                print("--- [MQTT] Kết nối thành công! ---")
                connection_flag = True
            else:
                print(f"--- [MQTT] Kết nối thất bại, mã lỗi: {rc} ---")

        client.on_connect = on_connect

        print(f"--- [DEBUG] Đang kết nối tới {MQTT_BROKER}... ---")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        client.loop_start() # Bắt đầu luồng nền
        
        # Đợi tối đa 5 giây để kết nối
        wait_time = 0
        while not connection_flag and wait_time < 50:
            time.sleep(0.1)
            wait_time += 1
            
        if not connection_flag:
            print("--- [ERROR] Timeout: Không thể kết nối MQTT Broker ---")
            client.loop_stop()
            return jsonify({"success": False, "message": "Không thể kết nối Server MQTT"}), 500

        # Publish tin nhắn
        print("--- [DEBUG] Đang gửi tin nhắn... ---")
        info = client.publish(MQTT_CONTROL_TOPIC, payload, qos=1)
        info.wait_for_publish(timeout=3) # Đợi xác nhận gửi đi

        if info.is_published():
            print(f"--- [SUCCESS] Đã gửi lệnh: {payload} ---")
            client.loop_stop()
            client.disconnect()
            return jsonify({"success": True, "message": "Đã gửi lệnh cập nhật Wifi xuống thiết bị!"})
        else:
            print("--- [ERROR] Gửi thất bại (Timeout) ---")
            client.loop_stop()
            client.disconnect()
            return jsonify({"success": False, "message": "Gửi lệnh thất bại (Timeout)"}), 500

    except Exception as e:
        print(f"--- [ERROR] Exception: {str(e)} ---")
        return jsonify({"success": False, "message": f"Lỗi hệ thống: {str(e)}"}), 500