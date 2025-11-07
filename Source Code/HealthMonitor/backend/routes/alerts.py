from flask import Blueprint, jsonify
from db import get_db_connection

alerts_bp = Blueprint('alerts', __name__)

# Lấy cảnh báo của 1 bệnh nhân
@alerts_bp.route('/<int:patient_id>', methods=['GET'])
def get_alerts(patient_id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM Alerts WHERE patient_id=%s ORDER BY timestamp DESC", (patient_id,))
        data = cur.fetchall()
    conn.close()
    return jsonify(data)
