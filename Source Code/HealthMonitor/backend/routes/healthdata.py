# routes/healthdata.py
from flask import Blueprint, jsonify, request
from db import get_db_connection

healthdata_bp = Blueprint('healthdata', __name__)

# Lấy dữ liệu sức khỏe mới nhất
@healthdata_bp.route('/latest/<int:patient_id>', methods=['GET'])
def get_latest(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM HealthData 
        WHERE patient_id = %s 
        ORDER BY timestamp DESC LIMIT 1
    """, (patient_id,))
    latest = cursor.fetchone()

    cursor.close()
    conn.close()

    if not latest:
        return jsonify({"message": "Chưa có dữ liệu sức khỏe!"}), 404

    return jsonify(latest)

# Lấy dữ liệu lịch sử (range = day/week/month)
@healthdata_bp.route('/history/<int:patient_id>', methods=['GET'])
def get_history(patient_id):
    range_type = request.args.get('range', 'day')  # day, week, month

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if range_type == 'day':
        cursor.execute("""
            SELECT * FROM HealthData 
            WHERE patient_id = %s AND timestamp >= NOW() - INTERVAL 1 DAY
            ORDER BY timestamp ASC
        """, (patient_id,))
    elif range_type == 'week':
        cursor.execute("""
            SELECT * FROM HealthData 
            WHERE patient_id = %s AND timestamp >= NOW() - INTERVAL 7 DAY
            ORDER BY timestamp ASC
        """, (patient_id,))
    else:  # month
        cursor.execute("""
            SELECT * FROM HealthData 
            WHERE patient_id = %s AND timestamp >= NOW() - INTERVAL 1 MONTH
            ORDER BY timestamp ASC
        """, (patient_id,))

    history = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(history)
