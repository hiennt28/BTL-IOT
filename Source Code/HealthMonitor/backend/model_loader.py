import tensorflow as tf
from tensorflow import keras
import joblib
import numpy as np
import os

# Đường dẫn tới các file mô hình (giả sử chúng nằm cùng thư mục backend)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "health_model.h5")
SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "label_encoder.pkl")

# Biến toàn cục để giữ mô hình, chỉ tải một lần
model = None
scaler = None
label_encoder = None

def load_model_assets():
    """
    Tải mô hình, scaler và label encoder vào bộ nhớ.
    """
    global model, scaler, label_encoder
    
    try:
        if not os.path.exists(MODEL_PATH):
            print(f"LỖI: Không tìm thấy file mô hình: {MODEL_PATH}")
            return
        if not os.path.exists(SCALER_PATH):
            print(f"LỖI: Không tìm thấy file scaler: {SCALER_PATH}")
            return
        if not os.path.exists(ENCODER_PATH):
            print(f"LỖI: Không tìm thấy file encoder: {ENCODER_PATH}")
            return

        model = keras.models.load_model(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        label_encoder = joblib.load(ENCODER_PATH)
        
        print("Tải mô hình AI, scaler và encoder thành công!")
        
        # Chạy một dự đoán thử để "warm up" mô hình
        predict_status(80, 1.5)
        print("Mô hình AI đã sẵn sàng.")

    except Exception as e:
        print(f"Lỗi nghiêm trọng khi tải mô hình AI: {e}")

def predict_status(bpm, a_total):
    """
    Dự đoán trạng thái sức khỏe từ bpm và a_total.
    
    Lưu ý: model.py của bạn dùng "AvgBPM". 
    Chúng ta giả định "bpm" từ MQTT là giá trị tương ứng.
    """
    if model is None or scaler is None or label_encoder is None:
        print("Mô hình AI chưa được tải. Không thể dự đoán.")
        return "Chưa rõ"

    try:
        # 1. Tạo input array
        # Mô hình được huấn luyện với 2 đặc trưng: [AvgBPM, A_total]
        input_data = np.array([[float(bpm), float(a_total)]])
        
        # 2. Scale dữ liệu
        scaled_data = scaler.transform(input_data)
        
        # 3. Dự đoán (predict trả về xác suất cho mỗi lớp)
        probabilities = model.predict(scaled_data)
        
        # 4. Lấy lớp có xác suất cao nhất
        predicted_class_index = np.argmax(probabilities, axis=1)[0]
        
        # 5. Giải mã (chuyển số thành nhãn)
        predicted_label = label_encoder.inverse_transform([predicted_class_index])[0]
        
        return predicted_label
        
    except Exception as e:
        print(f"Lỗi khi dự đoán: {e}")
        return "Lỗi dự đoán"

# Tải mô hình ngay khi file này được import
load_model_assets()