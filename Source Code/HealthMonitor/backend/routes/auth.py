from flask import Blueprint, request, jsonify
from db import get_db_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Auth API connected"}), 200

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Lỗi kết nối cơ sở dữ liệu"}), 500
        
    cur = conn.cursor(dictionary=True)

    try:
        roles = {
            'Managers': 'manager',
            'Doctors': 'doctor',
            'Patients': 'patient'
        }

        for table, role in roles.items():
            cur.execute(f"SELECT * FROM {table} WHERE email=%s AND password_hash=%s", (email, password))
            user = cur.fetchone()

            if user:
                user_info = {
                    "full_name": user['full_name'],
                    "email": user['email'],
                    "role": role
                }
                if role == 'patient':
                    user_info["patient_id"] = user['patient_id']
                elif role == 'doctor':
                    user_info["doctor_id"] = user['doctor_id']
                elif role == 'manager':
                    user_info["manager_id"] = user['manager_id']

                cur.close()
                conn.close()
                return jsonify({"success": True, "user": user_info})

        cur.close()
        conn.close()
        return jsonify({"success": False, "message": "Sai thông tin đăng nhập"})
    except Exception as e:
        print("Login error:", str(e))
        if conn:
            conn.close()
        return jsonify({"success": False, "message": "Lỗi máy chủ"}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    phone_number = data.get('phone_number')
    address = data.get('address')
    date_of_birth = data.get('date_of_birth')
    role = data.get('role')

    table_map = {
        'manager': 'Managers',
        'doctor': 'Doctors',
        'patient': 'Patients'
    }

    if role not in table_map:
        return jsonify({"success": False, "message": "Vai trò không hợp lệ!"}), 400

    table = table_map[role]
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Không thể kết nối cơ sở dữ liệu"}), 500

    try:
        cur = conn.cursor(dictionary=True) 
        cur.execute(f"SELECT * FROM {table} WHERE email=%s", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": "Email đã tồn tại!"}), 400

        sql_insert = f"""
            INSERT INTO {table} (full_name, email, password_hash, phone_number, address, date_of_birth)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cur.execute(sql_insert, (full_name, email, password, phone_number, address, date_of_birth))
        
        if role == 'patient':
            patient_id = cur.lastrowid
            
            cur.execute("""
                SELECT m.manager_id, (SELECT COUNT(*) FROM Patients p WHERE p.manager_id = m.manager_id) AS patient_count 
                FROM Managers m 
                ORDER BY patient_count ASC 
                LIMIT 1
            """)
            best_manager = cur.fetchone()
            manager_id = best_manager['manager_id'] if best_manager else None

            if manager_id:
                cur.execute("""
                    SELECT d.doctor_id, (SELECT COUNT(*) FROM Patients p WHERE p.doctor_id = d.doctor_id) AS patient_count 
                    FROM Doctors d 
                    WHERE d.manager_id = %s 
                    ORDER BY patient_count ASC 
                    LIMIT 1
                """, (manager_id,))
                best_doctor = cur.fetchone()
                doctor_id = best_doctor['doctor_id'] if best_doctor else None
                
                cur.execute(
                    "UPDATE Patients SET manager_id = %s, doctor_id = %s WHERE patient_id = %s",
                    (manager_id, doctor_id, patient_id)
                )

        elif role == 'doctor':
            doctor_id = cur.lastrowid
            
            cur.execute("""
                SELECT m.manager_id, (SELECT COUNT(*) FROM Doctors d WHERE d.manager_id = m.manager_id) AS doctor_count 
                FROM Managers m 
                ORDER BY doctor_count ASC 
                LIMIT 1
            """)
            best_manager = cur.fetchone()
            manager_id = best_manager['manager_id'] if best_manager else None

            if manager_id:
                cur.execute(
                    "UPDATE Doctors SET manager_id = %s WHERE doctor_id = %s",
                    (manager_id, doctor_id)
                )

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Đăng ký thành công!"})
    except Exception as e:
        print("Register error:", str(e))
        conn.rollback()
        conn.close()
        return jsonify({"success": False, "message": "Lỗi máy chủ!"})

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    data = request.get_json()
    email = data.get('email')
    role = data.get('role')
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    table_map = {
        'manager': 'Managers',
        'doctor': 'Doctors',
        'patient': 'Patients'
    }
    if role not in table_map:
        return jsonify({"success": False, "message": "Vai trò không hợp lệ!"}), 400

    table = table_map[role]
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Lỗi kết nối cơ sở dữ liệu"}), 500

    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(f"SELECT * FROM {table} WHERE email=%s AND password_hash=%s", (email, old_password))
        user = cur.fetchone()

        if not user:
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": "Mật khẩu cũ không chính xác!"})

        cur.execute(f"UPDATE {table} SET password_hash=%s WHERE email=%s", (new_password, email))
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Đổi mật khẩu thành công!"})
    
    except Exception as e:
        print("Change password error:", str(e))
        conn.rollback()
        conn.close()
        return jsonify({"success": False, "message": "Lỗi máy chủ khi đổi mật khẩu!"})