# routes/patients.py
from flask import Blueprint, jsonify, request
from db import get_db_connection

patients_bp = Blueprint('patients', __name__)

# Lấy thông tin bệnh nhân theo patient_id
@patients_bp.route('/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # === BẮT ĐẦU CẬP NHẬT ===
    # SỬA: JOIN với bảng Doctors để lấy doctor_name
    cursor.execute("""
        SELECT p.*, d.full_name as doctor_name 
        FROM `Patients` p
        LEFT JOIN `Doctors` d ON p.doctor_id = d.doctor_id
        WHERE p.patient_id = %s
    """, (patient_id,))
    # === KẾT THÚC CẬP NHẬT ===
    
    patient = cursor.fetchone()

    cursor.close()
    conn.close()

    if not patient:
        return jsonify({"message": "Không tìm thấy bệnh nhân!"}), 404

    return jsonify(patient)

# Cập nhật thông tin bệnh nhân
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