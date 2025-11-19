# routes/patients.py
from flask import Blueprint, jsonify, request
from db import get_db_connection

patients_bp = Blueprint('patients', __name__)

# Lấy thông tin bệnh nhân KÈM THÔNG TIN THIẾT BỊ
@patients_bp.route('/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # SỬA: JOIN với bảng Doctors và Devices để lấy đầy đủ thông tin
    # Thêm dev.is_measuring và dev.last_seen vào danh sách cột
    cursor.execute("""
        SELECT p.*, d.full_name as doctor_name, 
               dev.device_serial, dev.status as device_status, dev.is_measuring, dev.last_seen
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

# MỚI: API Bật/Tắt chế độ đo
@patients_bp.route('/<int:patient_id>/device/control', methods=['POST'])
def control_device(patient_id):
    data = request.get_json()
    action = data.get('action') # 'start' hoặc 'stop'
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Lấy device_id của bệnh nhân
    cursor.execute("SELECT device_id FROM Patients WHERE patient_id = %s", (patient_id,))
    result = cursor.fetchone()
    
    if not result or not result[0]:
        cursor.close(); conn.close()
        return jsonify({"success": False, "message": "Bệnh nhân chưa được gán thiết bị!"}), 400
        
    device_id = result[0]
    
    # 2. Cập nhật trạng thái is_measuring
    # 1: Bắt đầu đo, 0: Dừng đo
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