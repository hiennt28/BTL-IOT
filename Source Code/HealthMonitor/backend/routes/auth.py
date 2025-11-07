# routes/auth.py
from flask import Blueprint, request, jsonify
from db import get_db_connection

auth_bp = Blueprint('auth', __name__)

# Route gốc kiểm tra kết nối
@auth_bp.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Auth API connected"}), 200


# Route login (đăng nhập)
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
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
                # Nếu là bệnh nhân, trả patient_id
                if role == 'patient':
                    user_info = {
                        "patient_id": user['patient_id'],
                        "full_name": user['full_name'],
                        "email": user['email'],
                        "role": role
                    }
                elif role == 'doctor':
                    user_info = {
                        "doctor_id": user['doctor_id'],
                        "full_name": user['full_name'],
                        "email": user['email'],
                        "role": role
                    }
                else:  # manager
                    user_info = {
                        "manager_id": user['manager_id'],
                        "full_name": user['full_name'],
                        "email": user['email'],
                        "role": role
                    }

                cur.close()
                conn.close()
                return jsonify({"success": True, "user": user_info})

        cur.close()
        conn.close()
        return jsonify({"success": False, "message": "Sai thông tin đăng nhập"})
    except Exception as e:
        print("Login error:", e)
        conn.close()
        return jsonify({"success": False, "message": "Lỗi máy chủ"}), 500


# Route register (đăng ký)
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
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {table} WHERE email=%s", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": "Email đã tồn tại!"}), 400

        cur.execute(f"""
            INSERT INTO {table} (full_name, email, password_hash, phone_number, address, date_of_birth)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (full_name, email, password, phone_number, address, date_of_birth))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Đăng ký thành công!"})
    except Exception as e:
        print("Register error:", e)
        conn.rollback()
        return jsonify({"success": False, "message": "Lỗi máy chủ!"})
    finally:
        conn.close()
