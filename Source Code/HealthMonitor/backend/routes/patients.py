# routes/patients.py
from flask import Blueprint, jsonify, request
from db import get_db_connection
import json 
from mqtt_listenner import client, MQTT_CONTROL_TOPIC
# Không cần datetime ở đây nữa vì đã tính trong SQL

patients_bp = Blueprint('patients', __name__)

# Lấy thông tin bệnh nhân KÈM THÔNG TIN THIẾT BỊ
@patients_bp.route('/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # SỬA ĐỔI QUAN TRỌNG:
    # Thêm hàm TIMESTAMPDIFF(SECOND, dev.last_seen, NOW()) để MySQL tự tính số giây trôi qua
    # Điều này giúp tránh lỗi lệch múi giờ giữa Python và MySQL
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

    # === LOGIC KIỂM TRA ONLINE/OFFLINE MỚI ===
    if patient.get('device_serial'):
        seconds = patient.get('seconds_since_seen')
        
        # Nếu không có last_seen hoặc đã quá 15 giây không thấy tin hiệu -> Offline
        # (Giảm xuống 15s để bạn test nhanh hơn)
        if seconds is None or seconds > 15: 
            patient['device_status'] = 'offline'
        else:
            patient['device_status'] = 'online'

    return jsonify(patient)

# Cập nhật thông tin cá nhân (Giữ nguyên)
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

# API Bật/Tắt chế độ đo (Giữ nguyên)
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


@patients_bp.route('/<int:patient_id>/device/wifi-config', methods=['POST'])
def config_wifi(patient_id):
    print(f"\n--- [DEBUG] Bắt đầu setup lại Wifi cho Patient ID: {patient_id} ---")

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
        payload = {
            "device_serial": device_serial,
            "command": "RESET_WIFI",
        }
        result = client.publish(MQTT_CONTROL_TOPIC, json.dumps(payload), qos=1)
        result.wait_for_publish()
        
        if result.rc == 0:
            print("Đã gửi lệnh reset wifi qua mqtt")
            return jsonify({
                "success": "True", 
                "message": "Đã reset wifi"
            })
        else:
            print(f"Lỗi rc={result.rc}")
            return jsonify({"success": False, "message": f"MQTT error: {result.rc}"}), 500

    except Exception as e:
        print(f"--- [ERROR] Exception: {str(e)} ---")
        return jsonify({"success": False, "message": f"Lỗi hệ thống: {str(e)}"}), 500