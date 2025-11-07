from flask import Blueprint, jsonify, request
from db import get_db_connection

managers_bp = Blueprint('managers', __name__)

# === HELPER FUNCTION ===
def _find_best_doctor(manager_id, conn):
# ... (Hàm này không đổi) ...
    """
    Hàm nội bộ tìm bác sĩ có ít bệnh nhân nhất thuộc manager_id.
    """
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT d.doctor_id, (SELECT COUNT(*) FROM Patients p WHERE p.doctor_id = d.doctor_id) AS patient_count 
                FROM Doctors d 
                WHERE d.manager_id = %s 
                ORDER BY patient_count ASC 
                LIMIT 1
            """, (manager_id,))
            best_doctor = cur.fetchone()
            return best_doctor['doctor_id'] if best_doctor else None
    except Exception as e:
        # SỬA: Thêm str() để đảm bảo an toàn khi in lỗi
        print(f"Error finding best doctor: {str(e)}")
        return None
# ========================


# Lấy danh sách bác sĩ (theo manager_id)
@managers_bp.route('/<int:manager_id>/doctors', methods=['GET'])
def get_doctors(manager_id):
# ... (Phần kiểm tra conn không đổi) ...
    conn = get_db_connection()
    # SỬA: Thêm kiểm tra kết nối
    if not conn:
        return jsonify({"message": "Lỗi kết nối CSDL"}), 500
    try:
        with conn.cursor(dictionary=True) as cur:
# ... (Phần còn lại của hàm không đổi) ...
            cur.execute("SELECT * FROM Doctors WHERE manager_id = %s", (manager_id,))
            data = cur.fetchall()
        conn.close()
        return jsonify(data)
    except Exception as e:
        # SỬA: Thêm str() để đảm bảo an toàn khi in lỗi
        print(f"Error get_doctors: {str(e)}")
        if conn:
            conn.close()
        return jsonify({"message": "Lỗi khi lấy danh sách bác sĩ"}), 500


# Thêm bác sĩ (cho manager_id)
@managers_bp.route('/<int:manager_id>/doctors', methods=['POST'])
def add_doctor(manager_id):
# ... (Code data = request.json không đổi) ...
    data = request.json
    # Sử dụng mật khẩu plain text cho nhất quán với logic /login
    password_hash = data.get('password') 
    
    conn = get_db_connection()
    # SỬA: Thêm kiểm tra kết nối
    if not conn:
        return jsonify({'status':'error', 'message': 'Lỗi kết nối CSDL'}), 500
    try:
        with conn.cursor() as cur:
# ... (Phần còn lại của hàm không đổi) ...
            cur.execute(
                """
                INSERT INTO Doctors(manager_id, full_name, email, password_hash, phone_number, address, date_of_birth, title, specialty)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    manager_id,
                    data.get('full_name'),
                    data.get('email'),
                    password_hash,
                    data.get('phone_number'),
                    data.get('address'),
                    data.get('date_of_birth'),
                    data.get('title'),
                    data.get('specialty')
                )
            )
            conn.commit()
        conn.close()
        return jsonify({'status':'success', 'message': 'Thêm bác sĩ thành công!'})
    except Exception as e:
        # SỬA: Thêm str() để đảm bảo an toàn khi in lỗi
        print(f"Error add_doctor: {str(e)}")
        conn.rollback()
        conn.close()
        return jsonify({'status':'error', 'message': 'Email có thể đã tồn tại hoặc dữ liệu không hợp lệ'}), 400

# Cập nhật bác sĩ
@managers_bp.route('/doctors/<int:doctor_id>', methods=['PUT'])
def update_doctor(doctor_id):
# ... (Phần kiểm tra conn không đổi) ...
    data = request.json
    conn = get_db_connection()
    # SỬA: Thêm kiểm tra kết nối
    if not conn:
        return jsonify({'status':'error', 'message': 'Lỗi kết nối CSDL'}), 500
    try:
        with conn.cursor() as cur:
# ... (Phần còn lại của hàm không đổi) ...
            cur.execute(
                """
                UPDATE Doctors
                SET full_name = %s, email = %s, phone_number = %s, address = %s, date_of_birth = %s, title = %s, specialty = %s
                WHERE doctor_id = %s
                """,
                (
                    data.get('full_name'),
                    data.get('email'),
                    data.get('phone_number'),
                    data.get('address'),
                    data.get('date_of_birth'),
                    data.get('title'),
                    data.get('specialty'),
                    doctor_id
                )
            )
            conn.commit()
        conn.close()
        return jsonify({'status':'success', 'message': 'Cập nhật bác sĩ thành công!'})
    except Exception as e:
        # SỬA: Thêm str() để đảm bảo an toàn khi in lỗi
        print(f"Error update_doctor: {str(e)}")
        conn.rollback()
        conn.close()
        return jsonify({'status':'error', 'message': 'Lỗi khi cập nhật'}), 400

# Xóa bác sĩ
@managers_bp.route('/doctors/<int:doctor_id>', methods=['DELETE'])
def delete_doctor(doctor_id):
# ... (Phần kiểm tra conn không đổi) ...
    conn = get_db_connection()
    # SỬA: Thêm kiểm tra kết nối
    if not conn:
        return jsonify({'status':'error', 'message': 'Lỗi kết nối CSDL'}), 500
    try:
        with conn.cursor() as cur:
# ... (Phần còn lại của hàm không đổi) ...
            # Cần xử lý bệnh nhân của bác sĩ này trước khi xóa (ví dụ: gán null)
            cur.execute("UPDATE Patients SET doctor_id = NULL WHERE doctor_id = %s", (doctor_id,))
            cur.execute("DELETE FROM Doctors WHERE doctor_id = %s", (doctor_id,))
            conn.commit()
        conn.close()
        return jsonify({'status':'success', 'message': 'Xóa bác sĩ thành công!'})
    except Exception as e:
        # SỬA: Thêm str() để đảm bảo an toàn khi in lỗi
        print(f"Error delete_doctor: {str(e)}")
        conn.rollback()
        conn.close()
        return jsonify({'status':'error', 'message': 'Không thể xóa bác sĩ'}), 400

# Lấy danh sách bệnh nhân (theo manager_id)
@managers_bp.route('/<int:manager_id>/patients', methods=['GET'])
def get_patients(manager_id):
# ... (Phần kiểm tra conn không đổi) ...
    conn = get_db_connection()
    # SỬA: Thêm kiểm tra kết nối
    if not conn:
        return jsonify({"message": "Lỗi kết nối CSDL"}), 500
    try:
        with conn.cursor(dictionary=True) as cur:
# ... (Phần còn lại của hàm không đổi) ...
            # Join để lấy tên bác sĩ
            # SỬA LỖI: Thêm p.email vào SELECT
            cur.execute("""
                SELECT p.patient_id, p.full_name, p.email, p.manager_id, p.doctor_id, d.full_name as doctor_name 
                FROM Patients p
                LEFT JOIN Doctors d ON p.doctor_id = d.doctor_id
                WHERE p.manager_id = %s
            """, (manager_id,))
            data = cur.fetchall()
        conn.close()
        return jsonify(data)
    except Exception as e:
        # SỬA: Thêm str() để đảm bảo an toàn khi in lỗi
        print(f"Error get_patients: {str(e)}")
        if conn:
            conn.close()
        return jsonify({"message": "Lỗi khi lấy danh sách bệnh nhân"}), 500

# MỚI: API Thêm Bệnh Nhân (do Manager thực hiện)
@managers_bp.route('/<int:manager_id>/patients', methods=['POST'])
def add_patient(manager_id):
    data = request.json
    password_hash = data.get('password') # Lấy mật khẩu plain text

    conn = get_db_connection()
    # SỬA: Thêm kiểm tra kết nối (Đây là hàm gây ra lỗi trong ảnh)
    if not conn:
        return jsonify({'status':'error', 'message': 'Lỗi kết nối CSDL'}), 500
    try:
        # 1. Tự động tìm bác sĩ tốt nhất
        doctor_id = _find_best_doctor(manager_id, conn)

        # 2. Thêm bệnh nhân mới
        with conn.cursor() as cur:
# ... (Phần còn lại của hàm không đổi) ...
            # SỬA: Đã THÊM LẠI 'email' vào câu lệnh INSERT
            cur.execute(
                """
                INSERT INTO Patients(manager_id, doctor_id, full_name, email, password_hash, phone_number, address, date_of_birth)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    manager_id,
                    doctor_id,
                    data.get('full_name'),
                    data.get('email'), # <-- ĐÃ THÊM LẠI
                    password_hash,
                    data.get('phone_number'),
                    data.get('address'),
                    data.get('date_of_birth')
                )
            )
            conn.commit()
        conn.close()
        return jsonify({'status':'success', 'message': f'Thêm bệnh nhân thành công! (Tự động gán cho bác sĩ ID: {doctor_id})'})
    except Exception as e:
        # SỬA: Thêm str() để đảm bảo an toàn khi in lỗi
        print(f"Error add_patient: {str(e)}")
        conn.rollback()
        conn.close()
        # Trả về lỗi 400 (Bad Request) thay vì 500
        return jsonify({'status':'error', 'message': 'Dữ liệu không hợp lệ (ví dụ: email/sđt trùng lặp nếu bạn có ràng buộc UNIQUE)'}), 400


# ... (Đã xóa route /patients/assign) ...

# Giám sát thiết bị IoT (theo manager_id)
@managers_bp.route('/<int:manager_id>/devices', methods=['GET'])
def get_devices(manager_id):
# ... (Phần kiểm tra conn không đổi) ...
    conn = get_db_connection()
    # SỬA: Thêm kiểm tra kết nối
    if not conn:
        return jsonify({"message": "Lỗi kết nối CSDL"}), 500
    try:
        with conn.cursor(dictionary=True) as cur:
# ... (Phần còn lại của hàm không đổi) ...
            # Lấy các thiết bị của bệnh nhân thuộc quản lý này
            cur.execute("""
                SELECT d.* FROM Devices d
                JOIN Patients p ON d.device_id = p.device_id
                WHERE p.manager_id = %s
            """, (manager_id,))
            data = cur.fetchall()
        conn.close()
        return jsonify(data)
    except Exception as e:
        # SỬA: Thêm str() để đảm bảo an toàn khi in lỗi
        print(f"Error get_devices: {str(e)}")
        if conn:
            conn.close()
        return jsonify({"message": "Lỗi khi lấy danh sách thiết bị"}), 500

# Thống kê tổng hợp (theo manager_id)
@managers_bp.route('/<int:manager_id>/stats', methods=['GET'])
def stats(manager_id):
# ... (Phần kiểm tra conn không đổi) ...
    conn = get_db_connection()
    # SỬA: Thêm kiểm tra kết nối
    if not conn:
        return jsonify({"message": "Lỗi kết nối CSDL"}), 500
    try:
        with conn.cursor(dictionary=True) as cur:
# ... (Phần còn lại của hàm không đổi) ...
            cur.execute("SELECT COUNT(*) AS total FROM Patients WHERE manager_id = %s", (manager_id,))
            patients = cur.fetchone()['total']
            
            cur.execute("SELECT COUNT(*) AS total FROM Doctors WHERE manager_id = %s", (manager_id,))
            doctors = cur.fetchone()['total']
            
            # Thống kê cảnh báo theo loại, của các bệnh nhân thuộc quản lý
            cur.execute("""
                SELECT alert_type, COUNT(*) as count 
                FROM Alerts a
                JOIN Patients p ON a.patient_id = p.patient_id
                WHERE p.manager_id = %s
                GROUP BY alert_type
            """, (manager_id,))
            alerts_data = cur.fetchall()

        conn.close()
        
        alerts_labels = [a['alert_type'] for a in alerts_data]
        alerts_counts = [a['count'] for a in alerts_data]
        
        # Trả về cấu trúc mà frontend manager.html mong đợi
        stats_response = {
# ... (Phần code này không đổi) ...
            "patients_total": patients,
            "doctors_total": doctors,
            "alert_labels": alerts_labels,
            "alert_counts": alerts_counts
        }
        
        return jsonify(stats_response)
        
    except Exception as e:
        # SỬA: Thêm str() để đảm bảo an toàn khi in lỗi
        print(f"Error stats: {str(e)}")
        if conn:
            conn.close()
        return jsonify({"message": "Lỗi khi lấy thống kê"}), 500