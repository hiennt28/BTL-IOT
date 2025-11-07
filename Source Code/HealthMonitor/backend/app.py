# app.py
from flask import Flask, send_from_directory
from flask_cors import CORS
from threading import Thread

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

# ==== API ====
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(patients_bp, url_prefix='/api/patients')
app.register_blueprint(healthdata_bp, url_prefix='/api/health')
app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
app.register_blueprint(doctors_bp, url_prefix='/api/doctors')
app.register_blueprint(managers_bp, url_prefix='/api/managers')

if __name__ == '__main__':
   
    # Chạy Flask app
    app.run(debug=True, use_reloader=False) # use_reloader=False để tránh chạy thread MQTT 2 lần