from flask import Blueprint, jsonify, request
from db import get_db_connection
from datetime import datetime, timedelta

doctors_bp = Blueprint('doctors', __name__)

# API: Lấy thông tin chi tiết của bác sĩ (cho tab profile)
@doctors_bp.route('/<int:doctor_id>', methods=['GET'])
def get_doctor_details(doctor_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT doctor_id, full_name, email, phone_number, address, date_of_birth, title, specialty FROM Doctors WHERE doctor_id = %s", (doctor_id,))
        doctor = cursor.fetchone()
        cursor.close()
        conn.close()
        if not doctor:
            return jsonify({"message": "Không tìm thấy bác sĩ"}), 404
        return jsonify(doctor)
    except Exception as e:
        print("Error fetching doctor details:", str(e))
        return jsonify({"message": "Lỗi khi lấy thông tin bác sĩ"}), 500

# API: Bác sĩ cập nhật thông tin cá nhân
@doctors_bp.route('/update/<int:doctor_id>', methods=['PUT'])
def update_doctor(doctor_id):
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE Doctors
            SET full_name = %s, phone_number = %s, address = %s, date_of_birth = %s, title = %s, specialty = %s
            WHERE doctor_id = %s
        """
        cursor.execute(sql, (
            data.get('full_name'),
            data.get('phone_number'),
            data.get('address'),
            data.get('date_of_birth'),
            data.get('title'),
            data.get('specialty'),
            doctor_id
        ))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Cập nhật thông tin thành công!"})
    except Exception as e:
        print("Error updating doctor:", str(e))
        return jsonify({"message": "Lỗi khi cập nhật thông tin"}), 500


# API: Lấy danh sách bệnh nhân phụ trách
@doctors_bp.route('/<int:doctor_id>/patients', methods=['GET'])
def get_patients(doctor_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT patient_id, full_name, email, phone_number FROM Patients WHERE doctor_id = %s", (doctor_id,))
        patients = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(patients)
    except Exception as e:
        print("Error fetching patients:", str(e))
        return jsonify({"message": "Lỗi khi lấy danh sách bệnh nhân!"}), 500

# API: Lấy cảnh báo bệnh nhân
@doctors_bp.route('/<int:doctor_id>/alerts', methods=['GET'])
def get_alerts(doctor_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT a.alert_id, a.patient_id, p.full_name, a.alert_type, a.message, a.status, a.timestamp
            FROM Alerts a
            JOIN Patients p ON a.patient_id = p.patient_id
            WHERE p.doctor_id = %s
            ORDER BY a.timestamp DESC
        """
        cursor.execute(query, (doctor_id,))
        alerts = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(alerts)
    except Exception as e:
        print("Error fetching alerts:", str(e))
        return jsonify({"message": "Lỗi khi lấy cảnh báo!"}), 500

# API: Lấy dữ liệu sức khỏe mới nhất của bệnh nhân 
@doctors_bp.route('/health/latest/<int:patient_id>', methods=['GET'])
def latest_health(patient_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
      
        cursor.execute("""
            SELECT bpm, avg_bpm, ir_value, accel_x, accel_y, accel_z, a_total, timestamp
            FROM HealthData
            WHERE patient_id = %s
            ORDER BY timestamp DESC
            LIMIT 1
        """, (patient_id,))
        data = cursor.fetchone()
        cursor.close()
        conn.close()
        if not data:
            return jsonify({"message": "Không có dữ liệu!"}), 404
        return jsonify(data)
    except Exception as e:
        print("Error fetching latest health data:", str(e))
        return jsonify({"message": "Lỗi khi lấy dữ liệu sức khỏe!"}), 500

# API: Lấy lịch sử dữ liệu sức khỏe theo range
@doctors_bp.route('/health/history/<int:patient_id>', methods=['GET'])
def health_history(patient_id):
    range_type = request.args.get('range', 'day')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        now = datetime.now()
        if range_type == 'day':
            start_time = now - timedelta(days=1)
        elif range_type == 'week':
            start_time = now - timedelta(weeks=1)
        elif range_type == 'month':
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(days=1)

        cursor.execute("""
            SELECT bpm, avg_bpm, ir_value, accel_x, accel_y, accel_z, a_total, timestamp
            FROM HealthData
            WHERE patient_id = %s AND timestamp >= %s
            ORDER BY timestamp ASC
        """, (patient_id, start_time))
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(data)
    except Exception as e:
        print("Error fetching health history:", str(e))
        return jsonify({"message": "Lỗi khi lấy lịch sử sức khỏe!"}), 500

# API: Cập nhật trạng thái cảnh báo
@doctors_bp.route('/alerts/<int:alert_id>', methods=['PUT'])
def update_alert_status(alert_id):
    data = request.get_json()
    new_status = data.get('status', 'viewed')
    doctor_id = data.get('doctor_id')

    if new_status not in ['viewed', 'handled']:
        return jsonify({"message": "Trạng thái không hợp lệ"}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE Alerts
            SET status = %s, viewed_at = NOW(), viewed_by_doctor_id = %s
            WHERE alert_id = %s
            """, (new_status, doctor_id, alert_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": f"Đã cập nhật trạng thái thành {new_status}"})
    except Exception as e:
        print("Error updating alert status:", str(e))
        return jsonify({"message": "Lỗi khi cập nhật cảnh báo"}), 500