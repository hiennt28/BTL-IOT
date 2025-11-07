from flask import Blueprint, jsonify, request
from db import get_db_connection

managers_bp = Blueprint('managers', __name__)

# Danh sách bác sĩ
@managers_bp.route('/doctors', methods=['GET'])
def get_doctors():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM Doctors")
        data = cur.fetchall()
    conn.close()
    return jsonify(data)

# Thêm/Sửa/Xóa bác sĩ
@managers_bp.route('/doctors/add', methods=['POST'])
def add_doctor():
    data = request.json
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO Doctors(manager_id, full_name, email, password_hash, specialty)
            VALUES (%s,%s,%s,SHA2(%s,256),%s)
        """,(data['manager_id'],data['full_name'],data['email'],data['password'],data['specialty']))
        conn.commit()
    conn.close()
    return jsonify({'status':'success'})

# Danh sách bệnh nhân
@managers_bp.route('/patients', methods=['GET'])
def get_patients():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM Patients")
        data = cur.fetchall()
    conn.close()
    return jsonify(data)

# Gán bệnh nhân cho bác sĩ
@managers_bp.route('/patients/assign', methods=['POST'])
def assign_patient():
    data = request.json
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("UPDATE Patients SET doctor_id=%s WHERE patient_id=%s",(data['doctor_id'],data['patient_id']))
        conn.commit()
    conn.close()
    return jsonify({'status':'success'})

# Giám sát thiết bị IoT
@managers_bp.route('/devices', methods=['GET'])
def get_devices():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM Devices")
        data = cur.fetchall()
    conn.close()
    return jsonify(data)

# Thống kê tổng hợp
@managers_bp.route('/stats', methods=['GET'])
def stats():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total_patients FROM Patients")
        patients = cur.fetchone()['total_patients']
        cur.execute("SELECT COUNT(*) AS total_doctors FROM Doctors")
        doctors = cur.fetchone()['total_doctors']
        cur.execute("SELECT COUNT(*) AS total_alerts FROM Alerts")
        alerts = cur.fetchone()['total_alerts']
    conn.close()
    return jsonify({'patients':patients,'doctors':doctors,'alerts':alerts})
