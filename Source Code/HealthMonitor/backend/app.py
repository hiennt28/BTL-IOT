# app.py
from flask import Flask, send_from_directory
from flask_cors import CORS
from threading import Thread
import mqtt_listenner
import os
# Import routes
from routes.auth import auth_bp
from routes.patients import patients_bp
from routes.healthdata import healthdata_bp
from routes.alerts import alerts_bp
from routes.doctors import doctors_bp
from routes.managers import managers_bp


app = Flask(__name__, static_folder='../frontend', static_url_path='/')
CORS(app) # Thêm CORS để cho phép API gọi từ frontend

# ==== Serve các trang frontend ====
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'login.html')

@app.route('/<path:filename>')
def serve_static_files(filename):
    return send_from_directory(app.static_folder, filename)

# Đường dẫn tuyệt đối đến folder firmware_uploads ngoài backend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Truy cập folder firmware_uploads ở cấp trên thư mục backend
FIRMWARE_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'firmware_uploads'))

@app.route('/api/managers/firmware/<filename>')
def download_firmware(filename):
    file_path = os.path.join(FIRMWARE_DIR, filename)
    if not os.path.isfile(file_path):
        return "File not found", 404
    return send_from_directory(FIRMWARE_DIR, filename)

# ==== API ====
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(patients_bp, url_prefix='/api/patients')
app.register_blueprint(healthdata_bp, url_prefix='/api/health')
app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
app.register_blueprint(doctors_bp, url_prefix='/api/doctors')
app.register_blueprint(managers_bp, url_prefix='/api/managers')

if __name__ == '__main__':
   
    # Chạy Flask app
    #app.run(debug=True, use_reloader=False) # use_reloader=False để tránh chạy thread MQTT 2 lần
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
