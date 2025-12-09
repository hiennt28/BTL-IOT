from flask import Blueprint, jsonify, request
from db import get_db_connection
import time 
import paho.mqtt.client as mqtt
import json
from mqtt_listenner import send_ota_command
from mqtt_listenner import ota_status_store
from mqtt_listenner import client, MQTT_OTA_TOPIC
import base64
import os
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
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Lỗi kết nối CSDL"}), 500
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT p.patient_id, p.full_name, p.email, p.manager_id, p.device_id,
                       p.doctor_id, d.full_name as doctor_name 
                FROM Patients p 
                LEFT JOIN Doctors d ON p.doctor_id = d.doctor_id 
                WHERE p.manager_id = %s
            """, (manager_id,))
            data = cur.fetchall()
        conn.close()
        return jsonify(data)
    except Exception as e:
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


@managers_bp.route('/<int:manager_id>/devices', methods=['GET'])
def get_devices(manager_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Lỗi kết nối CSDL"}), 500

    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM devices ORDER BY device_id ASC")
            devices = cur.fetchall()

        conn.close()
        return jsonify(devices)
    except Exception as e:
        print(f"Error get_devices: {str(e)}")
        if conn:
            conn.close()
        return jsonify({"message": "Lỗi khi lấy danh sách thiết bị"}), 500

@managers_bp.route('/<int:manager_id>/devices/<int:device_id>', methods=['PUT'])
def update_device_serial(manager_id, device_id):
    """Cập nhật device_serial của thiết bị"""
    data = request.json
    device_serial = data.get("device_serial")
    
    if not device_serial or not device_serial.strip():
        return jsonify({"status": "error", "message": "Device serial không được để trống"}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Lỗi kết nối CSDL"}), 500
    
    try:
        with conn.cursor(dictionary=True) as cursor:
            # Kiểm tra thiết bị có tồn tại không
            cursor.execute("SELECT * FROM devices WHERE device_id = %s", (device_id,))
            device = cursor.fetchone()
            
            if not device:
                return jsonify({"status": "error", "message": "Thiết bị không tồn tại"}), 404
            
            # Kiểm tra device_serial mới có bị trùng không
            cursor.execute("SELECT device_id FROM devices WHERE device_serial = %s AND device_id != %s", 
                         (device_serial.strip(), device_id))
            duplicate = cursor.fetchone()
            
            if duplicate:
                return jsonify({"status": "error", "message": "Device serial này đã tồn tại"}), 400
            
            # Cập nhật device_serial
            cursor.execute(
                "UPDATE devices SET device_serial = %s WHERE device_id = %s",
                (device_serial.strip(), device_id)
            )
            conn.commit()
        
        conn.close()
        return jsonify({
            "status": "success", 
            "message": "Cập nhật device serial thành công!",
            "device_id": device_id,
            "device_serial": device_serial.strip()
        })
        
    except Exception as e:
        conn.rollback()
        print(f"Error update_device_serial: {str(e)}")
        return jsonify({"status": "error", "message": f"Cập nhật thất bại: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

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

@managers_bp.route('/<int:manager_id>/devices', methods=['POST'])
def add_device(manager_id):
    data = request.json
    device_serial = data.get("device_serial")
    status = "offline"

    if not device_serial:
        return jsonify({"status":"error", "message":"device_serial là bắt buộc"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Lấy device_id mới
        cursor.execute("SELECT IFNULL(MAX(device_id),0) AS max_id FROM devices")
        max_id = cursor.fetchone()[0]
        new_id = max_id + 1

        # Thêm thiết bị
        cursor.execute(
            "INSERT INTO devices (device_id, device_serial, status) VALUES (%s, %s, %s)",
            (new_id, device_serial, status)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status":"success", "message":"Thêm thiết bị thành công", "device_id": new_id})
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        print(f"Error add_device: {str(e)}")
        return jsonify({"status":"error", "message": f"Thêm thiết bị thất bại: {str(e)}"}), 400

#Gán thiết bị cho bệnh nhân
@managers_bp.route('/<int:manager_id>/patients/<int:patient_id>/assign-device', methods=['POST'])
def assign_device_to_patient(manager_id, patient_id):
    data = request.json
    device_id = data.get("device_id")
    if not device_id:
        return jsonify({"status": "error", "message": "device_id là bắt buộc"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Lỗi kết nối CSDL"}), 500

    try:
        with conn.cursor(dictionary=True) as cursor:
            # Kiểm tra bệnh nhân thuộc manager này
            cursor.execute("SELECT * FROM patients WHERE patient_id=%s AND manager_id=%s", (patient_id, manager_id))
            patient = cursor.fetchone()
            if not patient:
                return jsonify({"status": "error", "message": "Bệnh nhân không tồn tại hoặc không thuộc quản lý"}), 400

            # Kiểm tra thiết bị đã gán chưa
            cursor.execute("SELECT * FROM patients WHERE device_id=%s", (device_id,))
            assigned = cursor.fetchone()
            if assigned and assigned['patient_id'] != patient_id:
                return jsonify({"status": "error", "message": "Thiết bị đã được gán cho bệnh nhân khác"}), 400

            # Cập nhật device_id cho bệnh nhân
            cursor.execute("UPDATE patients SET device_id=%s WHERE patient_id=%s", (device_id, patient_id))
            conn.commit()

        return jsonify({"status": "success", "message": "Gán thiết bị thành công"})
    except Exception as e:
        conn.rollback()
        print(f"Error assign_device_to_patient: {str(e)}")
        return jsonify({"status": "error", "message": f"Gán thiết bị thất bại: {str(e)}"}), 500
    finally:
        conn.close()



#Hủy gán thiết bị cho bệnh nhân
@managers_bp.route('/<int:manager_id>/patients/<int:patient_id>/unassign-device', methods=['POST'])
def unassign_device(manager_id, patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Kiểm tra bệnh nhân có thuộc manager này không
        cursor.execute("SELECT manager_id FROM patients WHERE patient_id=%s", (patient_id,))
        row = cursor.fetchone()
        if not row or row[0] != manager_id:
            return jsonify({"status": "error", "message": "Bệnh nhân không tồn tại hoặc không thuộc quản lý"}), 400

        # Hủy gán device
        cursor.execute("UPDATE patients SET device_id=NULL WHERE patient_id=%s", (patient_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "Hủy gán thiết bị thành công"})
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        print(f"Error unassign_device: {str(e)}")
        return jsonify({"status": "error", "message": f"Hủy gán thất bại: {str(e)}"}), 500




# ============================================
# FILE: managers.py - HTTP OTA với IP Local
# ============================================

import os
import socket
import time
from flask import send_from_directory

FIRMWARE_FOLDER = "firmware_uploads"

# Tạo folder lưu firmware
os.makedirs(FIRMWARE_FOLDER, exist_ok=True)

# Hàm lấy IP local
def get_local_ip():
    """Lấy IP local của máy (192.168.x.x)"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"[IP] Không lấy được IP: {e}")
        return "127.0.0.1"


@managers_bp.route("/<int:manager_id>/update_firmware/<device_serial>", methods=["POST"])
def update_firmware(manager_id, device_serial):
    """Upload firmware và gửi URL qua MQTT"""
    
    print(f"\n{'='*60}")
    print(f"[HTTP OTA] Nhận request cập nhật firmware")
    print(f"[HTTP OTA] Device: {device_serial}")
    print(f"{'='*60}\n")
    
    file = request.files.get("firmware")
    if not file or not file.filename.endswith('.bin'):
        return jsonify({"status": "error", "message": "File không hợp lệ"}), 400

    file_size = len(file.read())
    file.seek(0)  # Reset pointer
    
    print(f"[HTTP OTA] File: {file.filename}")
    print(f"[HTTP OTA] Size: {file_size} bytes ({file_size/1024:.2f} KB)")
    
    if file_size > 2 * 1024 * 1024:  # Max 2MB
        return jsonify({"status": "error", "message": "File quá lớn (max 2MB)"}), 400

    # ✅ Lưu file vào server
    filename = f"{device_serial}_{int(time.time())}.bin"
    filepath = os.path.join(FIRMWARE_FOLDER, filename)
    file.save(filepath)

    print(f"[HTTP OTA] File saved at: {filepath}")
    print(f"[HTTP OTA] List files in firmware_uploads: {os.listdir(FIRMWARE_FOLDER)}")


    time.sleep(1)   # Cho file ghi xong trước khi ESP32 tải

    print(f"[HTTP OTA] Đã lưu: {filepath}")
    
    # Lấy IP local
    local_ip = get_local_ip()
    firmware_url = f"http://{local_ip}:5000/api/managers/firmware/{filename}"
    
    print(f"[HTTP OTA] URL: {firmware_url}")
    
    # Reset trạng thái OTA
    ota_status_store[device_serial] = {
        "progress": 0,
        "status": "idle",
        "reason": ""
    }
    
    # ✅ Gửi URL qua MQTT
    payload = {
        "device_serial": device_serial,
        "command": "START_OTA",
        "firmware_url": firmware_url
    }
    
    try:
        result = client.publish(MQTT_OTA_TOPIC, json.dumps(payload), qos=1)
        result.wait_for_publish()
        
        if result.rc == 0:
            print(f"[HTTP OTA] Đã gửi lệnh OTA qua MQTT")
            return jsonify({
                "status": "success", 
                "message": "Đã gửi lệnh OTA",
                "firmware_url": firmware_url
            })
        else:
            print(f"[HTTP OTA] MQTT publish failed: rc={result.rc}")
            return jsonify({"status": "error", "message": f"MQTT error: {result.rc}"}), 500
            
    except Exception as e:
        print(f"[HTTP OTA] Lỗi: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# Route serve file firmware
@managers_bp.route("/firmware/<filename>", methods=["GET"])
def serve_firmware(filename):
    """Serve file firmware cho ESP32 download"""
    print(f"[HTTP OTA] ESP32 đang download: {filename}")
    file_path = os.path.join(FIRMWARE_FOLDER, filename)
    if not os.path.isfile(file_path):
        return "File not found", 404
    return send_from_directory(FIRMWARE_FOLDER, filename)


@managers_bp.route("/<int:manager_id>/ota_status/<device_serial>", methods=["GET"])
def ota_status(manager_id, device_serial):
    """Lấy trạng thái OTA"""
    status = ota_status_store.get(device_serial, {
        "progress": 0, 
        "status": "idle", 
        "reason": ""
    })
    return jsonify(status)


# ============================================
# THÊM VÀO ĐẦU FILE: import thêm
# ============================================
"""
from flask import send_from_directory
import socket
import os
"""