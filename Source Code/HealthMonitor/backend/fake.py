# import paho.mqtt.client as mqtt
# import json
# import random
# import time
# import ssl
# import threading

# MQTT_BROKER = "8c9b9eafe2434729af707f153e31a91f.s1.eu.hivemq.cloud"
# MQTT_PORT = 8883
# MQTT_USER = "nhom5"
# MQTT_PASS = "Abc123456"
# MQTT_DATA_TOPIC = "health/data"
# MQTT_OTA_TOPIC = "health/ota_status"  # topic để gửi trạng thái OTA

# DEVICES = [
#     {"serial": "ESP32-001", "updating": False},
#     {"serial": "ESP32-002", "updating": False},
#     {"serial": "ESP32-003", "updating": False}
# ]

# client = mqtt.Client()
# client.username_pw_set(MQTT_USER, MQTT_PASS)
# client.tls_set(tls_version=ssl.PROTOCOL_TLS)

# # ===================== MQTT CALLBACK =====================
# def on_connect(client, userdata, flags, rc):
#     if rc == 0:
#         print("🔥 Thiết bị giả đã kết nối MQTT!")
#         client.subscribe("health/ota")  # lắng nghe lệnh START_OTA
#         print("Đang lắng nghe topic OTA")
#     else:
#         print("❌ Lỗi kết nối MQTT:", rc)

# def on_message(client, userdata, msg):
#     try:
#         payload = json.loads(msg.payload.decode())
#         target_serial = payload.get("device_serial")
#         command = payload.get("command")

#         if not target_serial or not command:
#             return

#         # Tìm device trong DEVICES
#         for dev in DEVICES:
#             if dev["serial"] == target_serial:
#                 if command == "START_OTA":
#                     # Chạy thread mô phỏng OTA
#                     threading.Thread(target=simulate_ota, args=(dev,)).start()
#                 break
#     except Exception as e:
#         print("Lỗi xử lý MQTT OTA:", e)

# client.on_connect = on_connect
# client.on_message = on_message

# # ===================== GỬI DỮ LIỆU SỐNG =====================
# def send_fake_data():
#     while True:
#         for dev in DEVICES:
#             if dev["updating"]:
#                 continue
#             payload = {
#                 "device_serial": dev["serial"],
#                 "bpm": random.randint(60, 110),
#                 "accel_x": round(random.uniform(-1.0, 1.0), 2),
#                 "accel_y": round(random.uniform(-1.0, 1.0), 2),
#                 "accel_z": round(random.uniform(-1.0, 1.0), 2),
#                 "ir_value": random.randint(200, 2000)
#             }
#             client.publish(MQTT_DATA_TOPIC, json.dumps(payload))
#             time.sleep(1)
#         time.sleep(2)

# # ===================== MÔ PHỎNG OTA =====================
# def simulate_ota(dev):
#     dev["updating"] = True
#     print(f"[OTA] Bắt đầu cập nhật firmware cho {dev['serial']}")

#     for i in range(0, 101, 10):
#         ota_status = {
#             "device_serial": dev["serial"],
#             "progress": i,
#             "status": "updating" if i < 100 else "success"
#         }
#         client.publish(MQTT_OTA_TOPIC, json.dumps(ota_status))
#         print(f"[OTA] {dev['serial']} tiến trình: {i}%")
#         time.sleep(0.5)

#     print(f"[OTA] Cập nhật hoàn tất cho {dev['serial']}")
#     dev["updating"] = False

# # ===================== RUN =====================
# print("Đang kết nối đến MQTT...")
# client.connect(MQTT_BROKER, MQTT_PORT)
# client.loop_start()

# # Chạy gửi dữ liệu giả
# threading.Thread(target=send_fake_data, daemon=True).start()


# import paho.mqtt.client as mqtt
# import json
# import random
# import time
# import ssl
# import threading

# MQTT_BROKER = "8c9b9eafe2434729af707f153e31a91f.s1.eu.hivemq.cloud"
# MQTT_PORT = 8883
# MQTT_USER = "nhom5"
# MQTT_PASS = "Abc123456"
# MQTT_DATA_TOPIC = "health/data"
# MQTT_OTA_TOPIC = "health/ota"  # ✅ SỬA: Lắng nghe lệnh OTA
# MQTT_OTA_STATUS_TOPIC = "health/ota_status"  # ✅ SỬA: Gửi trạng thái OTA

# DEVICES = [
#     {"serial": "ESP32-001", "updating": False},
#     {"serial": "ESP32-002", "updating": False},
#     {"serial": "ESP32-003", "updating": False}
# ]

# client = mqtt.Client()
# client.username_pw_set(MQTT_USER, MQTT_PASS)
# client.tls_set(tls_version=ssl.PROTOCOL_TLS)

# # ===================== MQTT CALLBACK =====================
# def on_connect(client, userdata, flags, rc):
#     if rc == 0:
#         print("🔥 Thiết bị giả đã kết nối MQTT!")
#         client.subscribe(MQTT_OTA_TOPIC)  # ✅ Lắng nghe lệnh START_OTA
#         print(f"✓ Đang lắng nghe topic: {MQTT_OTA_TOPIC}")
#     else:
#         print("❌ Lỗi kết nối MQTT:", rc)

# def on_message(client, userdata, msg):
#     """Xử lý lệnh OTA từ server"""
#     try:
#         payload = json.loads(msg.payload.decode())
#         target_serial = payload.get("device_serial")
#         command = payload.get("command")
#         firmware_data = payload.get("firmware_data")  # ✅ Base64 data

#         if not target_serial or not command:
#             return

#         print(f"[MQTT] Nhận lệnh từ topic {msg.topic}: {command} cho {target_serial}")

#         # Tìm device trong DEVICES
#         for dev in DEVICES:
#             if dev["serial"] == target_serial:
#                 if command == "START_OTA":
#                     if dev["updating"]:
#                         print(f"[OTA] {target_serial} đang cập nhật, bỏ qua lệnh")
#                         return
                    
#                     # ✅ Kiểm tra có firmware data không
#                     if not firmware_data:
#                         send_ota_status(target_serial, 0, "error", "Không có dữ liệu firmware")
#                         return
                    
#                     print(f"[OTA] Nhận firmware size: {len(firmware_data)} bytes (base64)")
                    
#                     # Chạy thread mô phỏng OTA
#                     threading.Thread(target=simulate_ota, args=(dev, firmware_data), daemon=True).start()
#                 break
#     except Exception as e:
#         print(f"❌ Lỗi xử lý MQTT OTA: {e}")

# client.on_connect = on_connect
# client.on_message = on_message

# # ===================== GỬI TRẠNG THÁI OTA =====================
# def send_ota_status(device_serial, progress, status, reason=""):
#     """Gửi trạng thái OTA lên server"""
#     ota_status = {
#         "device_serial": device_serial,
#         "progress": progress,
#         "status": status,  # idle, downloading, updating, success, error
#         "reason": reason
#     }
#     client.publish(MQTT_OTA_STATUS_TOPIC, json.dumps(ota_status))
#     print(f"[OTA STATUS] {device_serial}: {progress}% - {status}")

# # ===================== GỬI DỮ LIỆU SỐNG =====================
# def send_fake_data():
#     """Gửi dữ liệu health giả định LIÊN TỤC"""
#     print("📡 Bắt đầu gửi dữ liệu health mỗi 3 giây...\n")
    
#     while True:
#         for dev in DEVICES:
#             # ✅ CHỈ THÔNG BÁO nhưng VẪN GỬI DATA
#             status_icon = "🔄" if dev["updating"] else "✅"
            
#             payload = {
#                 "device_serial": dev["serial"],
#                 "bpm": random.randint(60, 110),
#                 "accel_x": round(random.uniform(-1.0, 1.0), 2),
#                 "accel_y": round(random.uniform(-1.0, 1.0), 2),
#                 "accel_z": round(random.uniform(-1.0, 1.0), 2),
#                 "ir_value": random.randint(200, 2000)
#             }
            
#             client.publish(MQTT_DATA_TOPIC, json.dumps(payload))
            
#             # Chỉ log nếu KHÔNG đang update (để tránh spam log)
#             if not dev["updating"]:
#                 print(f"{status_icon} [{time.strftime('%H:%M:%S')}] {dev['serial']}: BPM={payload['bpm']}")
            
#             time.sleep(1)
        
#         time.sleep(2)

# # ===================== MÔ PHỎNG OTA =====================
# def simulate_ota(dev, firmware_data):
#     """Mô phỏng quá trình OTA - Device VẪN HOẠT ĐỘNG trong khi cập nhật"""
#     device_serial = dev["serial"]
    
#     # ✅ Đánh dấu đang update (chỉ để UI biết, vẫn gửi data)
#     dev["updating"] = True
    
#     try:
#         print(f"\n{'='*50}")
#         print(f"[OTA] 🚀 {device_serial} NHẬN LỆNH CẬP NHẬT FIRMWARE")
#         print(f"[OTA] 📦 Firmware size: {len(firmware_data)} bytes (base64)")
#         print(f"[OTA] ⚠️  Device VẪN GỬI dữ liệu health trong khi OTA")
#         print(f"{'='*50}\n")
        
#         # ✅ GIAI ĐOẠN 1: DOWNLOADING (0-30%)
#         print(f"[OTA] 📥 {device_serial} - Đang tải firmware...")
#         send_ota_status(device_serial, 0, "downloading", "Bắt đầu tải")
        
#         for progress in range(0, 31, 5):
#             send_ota_status(device_serial, progress, "downloading", f"Đang tải {progress}%")
#             time.sleep(0.3)
        
#         # ✅ GIAI ĐOẠN 2: VERIFYING (30-40%)
#         print(f"[OTA] 🔍 {device_serial} - Đang xác thực firmware...")
#         for progress in range(30, 41, 5):
#             send_ota_status(device_serial, progress, "downloading", "Xác thực firmware")
#             time.sleep(0.2)
        
#         # ✅ GIAI ĐOẠN 3: UPDATING (40-95%)
#         print(f"[OTA] ⚙️  {device_serial} - Đang ghi firmware vào flash...")
#         for progress in range(40, 96, 5):
#             send_ota_status(device_serial, progress, "updating", f"Đang ghi {progress}%")
#             time.sleep(0.4)
        
#         # ✅ GIAI ĐOẠN 4: REBOOTING (95-100%)
#         print(f"[OTA] 🔄 {device_serial} - Khởi động lại thiết bị...")
#         send_ota_status(device_serial, 95, "updating", "Khởi động lại")
#         time.sleep(1.5)
        
#         # ✅ HOÀN THÀNH
#         send_ota_status(device_serial, 100, "success", "Cập nhật thành công")
#         print(f"\n{'='*50}")
#         print(f"[OTA] ✅ {device_serial} - CẬP NHẬT HOÀN TẤT!")
#         print(f"[OTA] 🔄 {device_serial} - Tiếp tục gửi dữ liệu bình thường")
#         print(f"{'='*50}\n")
        
#     except Exception as e:
#         print(f"[OTA] ❌ {device_serial} - Lỗi: {e}")
#         send_ota_status(device_serial, 0, "error", str(e))
    
#     finally:
#         # ✅ Reset trạng thái để UI biết đã xong
#         time.sleep(2)
#         dev["updating"] = False
#         print(f"[OTA] ℹ️  {device_serial} đã sẵn sàng nhận lệnh OTA mới\n")

# # ===================== THÊM: Mô phỏng lỗi ngẫu nhiên (tùy chọn) =====================
# def simulate_ota_with_random_error(dev, firmware_data):
#     """Mô phỏng OTA với khả năng lỗi ngẫu nhiên (để test)"""
#     dev["updating"] = True
#     device_serial = dev["serial"]
    
#     try:
#         # 10% khả năng lỗi ngay từ đầu
#         if random.random() < 0.1:
#             send_ota_status(device_serial, 0, "error", "Không đủ bộ nhớ flash")
#             return
        
#         # Download phase
#         for progress in range(0, 31, 5):
#             send_ota_status(device_serial, progress, "downloading")
#             time.sleep(0.3)
            
#             # 5% khả năng lỗi khi download
#             if random.random() < 0.05:
#                 send_ota_status(device_serial, progress, "error", "Mất kết nối MQTT")
#                 return
        
#         # Update phase
#         for progress in range(40, 96, 5):
#             send_ota_status(device_serial, progress, "updating")
#             time.sleep(0.4)
        
#         # Success
#         send_ota_status(device_serial, 100, "success")
#         print(f"[OTA] ✅ {device_serial} cập nhật thành công")
        
#     except Exception as e:
#         send_ota_status(device_serial, 0, "error", str(e))
#     finally:
#         time.sleep(2)
#         dev["updating"] = False

# # ===================== RUN =====================
# if __name__ == "__main__":
#     print("\n" + "="*60)
#     print("🤖 FAKE ESP32 SIMULATOR - HEALTH MONITORING + OTA")
#     print("="*60)
#     print(f"📡 MQTT Broker: {MQTT_BROKER}")
#     print(f"📤 Data Topic: {MQTT_DATA_TOPIC}")
#     print(f"📥 OTA Command Topic: {MQTT_OTA_TOPIC}")
#     print(f"📊 OTA Status Topic: {MQTT_OTA_STATUS_TOPIC}")
#     print(f"🔧 Devices: {', '.join([d['serial'] for d in DEVICES])}")
#     print("="*60 + "\n")
    
#     print("Đang kết nối đến MQTT...")
#     client.connect(MQTT_BROKER, MQTT_PORT)
#     client.loop_start()
    
#     # Đợi kết nối
#     time.sleep(2)
    
#     # Chạy gửi dữ liệu giả
#     print("🚀 Bắt đầu gửi dữ liệu health...\n")
#     data_thread = threading.Thread(target=send_fake_data, daemon=True)
#     data_thread.start()
    
#     # Giữ chương trình chạy
#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("\n\n⛔ Dừng chương trình...")
#         client.loop_stop()
#         client.disconnect()
#         print("👋 Đã ngắt kết nối MQTT")


import paho.mqtt.client as mqtt
import json
import random
import time
import ssl
import threading
import requests

MQTT_BROKER = "8c9b9eafe2434729af707f153e31a91f.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "nhom5"
MQTT_PASS = "Abc123456"
MQTT_DATA_TOPIC = "health/data"
MQTT_OTA_TOPIC = "health/ota"
MQTT_OTA_STATUS_TOPIC = "health/ota_status"

DEVICES = [
    {"serial": "ESP32-001", "updating": False},
    {"serial": "ESP32-002", "updating": False},
    {"serial": "ESP32-003", "updating": False}
]

client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.tls_set(tls_version=ssl.PROTOCOL_TLS)

# ==========================================================
# MQTT CONNECT
# ==========================================================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("🔥 Fake ESP32 kết nối MQTT thành công!")
        client.subscribe(MQTT_OTA_TOPIC)
        print("✓ Đang subscribe:", MQTT_OTA_TOPIC)
    else:
        print("❌ Lỗi kết nối MQTT", rc)

# ==========================================================
# Gửi trạng thái OTA về server
# ==========================================================
def send_ota_status(device_serial, progress, status, msg=""):
    payload = {
        "device_serial": device_serial,
        "progress": progress,
        "status": status,
        "reason": msg
    }
    client.publish(MQTT_OTA_STATUS_TOPIC, json.dumps(payload))
    print(f"[OTA STATUS] {device_serial} | {progress}% | {status} | {msg}")

# ==========================================================
# MQTT MESSAGE - nhận lệnh OTA
# ==========================================================
def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        serial = data.get("device_serial")
        command = data.get("command")
        firmware_url = data.get("firmware_url")

        if command != "START_OTA":
            return

        # Tìm đúng device
        for dev in DEVICES:
            if dev["serial"] == serial:
                if dev["updating"]:
                    print("⚠ Device đang update, bỏ qua lệnh")
                    return

                if not firmware_url:
                    send_ota_status(serial, 0, "error", "Không có firmware_url")
                    return

                print(f"\n🔔 Nhận lệnh OTA cho {serial}")
                print("URL firmware =", firmware_url)

                threading.Thread(
                    target=simulate_http_ota,
                    args=(dev, firmware_url),
                    daemon=True
                ).start()
                break

    except Exception as e:
        print("❌ Lỗi on_message:", e)


client.on_connect = on_connect
client.on_message = on_message

# ==========================================================
# Fake OTA (tải file bằng HTTP)
# ==========================================================
def simulate_http_ota(dev, firmware_url):
    serial = dev["serial"]
    dev["updating"] = True

    try:
        send_ota_status(serial, 0, "downloading", "Bắt đầu tải qua HTTP")

        print(f"[OTA] 📥 {serial} tải firmware từ {firmware_url}")

        res = requests.get(firmware_url)
        if res.status_code != 200:
            send_ota_status(serial, 0, "error", "Không tải được firmware")
            return

        firmware_data = res.content
        print(f"[OTA] 📦 {serial} tải xong firmware, size = {len(firmware_data)} bytes")

        # Giả lập tiến trình
        for p in range(0, 31, 5):
            send_ota_status(serial, p, "downloading")
            time.sleep(0.2)

        for p in range(30, 41, 5):
            send_ota_status(serial, p, "verifying")
            time.sleep(0.2)

        for p in range(40, 96, 5):
            send_ota_status(serial, p, "updating")
            time.sleep(0.3)

        send_ota_status(serial, 100, "success", "Cập nhật xong!")
        print(f"[OTA] 🎉 {serial} update thành công!")

    except Exception as e:
        send_ota_status(serial, 0, "error", str(e))

    finally:
        time.sleep(1)
        dev["updating"] = False


# ==========================================================
# Gửi dữ liệu health liên tục
# ==========================================================
def send_fake_data():
    while True:
        for dev in DEVICES:
            payload = {
                "device_serial": dev["serial"],
                "bpm": random.randint(60, 110),
                "accel_x": round(random.uniform(-1, 1), 2),
                "accel_y": round(random.uniform(-1, 1), 2),
                "accel_z": round(random.uniform(-1, 1), 2),
                "ir_value": random.randint(200, 2000)
            }
            client.publish(MQTT_DATA_TOPIC, json.dumps(payload))

            if not dev["updating"]:
                print(f"✓ {dev['serial']} | BPM={payload['bpm']}")

            time.sleep(1)
        time.sleep(1)


# ==========================================================
# MAIN
# ==========================================================
print("🚀 FAKE ESP32 KHỞI ĐỘNG...")
client.connect(MQTT_BROKER, MQTT_PORT)
client.loop_start()

time.sleep(2)

threading.Thread(target=send_fake_data, daemon=True).start()

while True:
    time.sleep(1)
