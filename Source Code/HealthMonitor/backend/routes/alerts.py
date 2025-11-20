from flask import Blueprint, jsonify
from db import get_db_connection

alerts_bp = Blueprint('alerts', __name__)

# Lấy cảnh báo của 1 bệnh nhân
@alerts_bp.route('/<int:patient_id>', methods=['GET'])
def get_alerts(patient_id):
    conn = get_db_connection()
    
    # Thêm dictionary=True để dữ liệu trả về có dạng { "alert_type": "...", "message": "..." }
    # Nếu không có, nó trả về dạng (1, "Cảnh báo",...) khiến JS không đọc được.
    if conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM Alerts WHERE patient_id=%s ORDER BY timestamp DESC", (patient_id,))
            data = cur.fetchall()
        conn.close()
        return jsonify(data)
    else:
        return jsonify([]), 500