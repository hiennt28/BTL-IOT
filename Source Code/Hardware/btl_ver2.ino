#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <WiFiManager.h> // Cần cài thư viện "WiFiManager" by tzapu
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_ADXL345_U.h>
#include "MAX30105.h"
#include "heartRate.h"
#include <ArduinoJson.h> // Cần cài thư viện "ArduinoJson" by Benoit Blanchon

// ======================== 1. CẤU HÌNH MQTT ========================
// Lưu ý: SSID/Password Wifi không cần hardcode nữa vì dùng WiFiManager
const char* MQTT_SERVER = "8c9b9eafe2434729af707f153e31a91f.s1.eu.hivemq.cloud";
const int MQTT_PORT = 8883;
const char* MQTT_USER = "nhom5";
const char* MQTT_PASSWORD = "Abc123456";

// Serial thiết bị (Duy nhất cho mỗi ESP32)
#define DEVICE_SERIAL "ESP32-001" 

const char* TOPIC_DATA = "health/data";
const char* TOPIC_CONTROL = "health/control";

// Chân đèn LED cảnh báo (GPIO 2 thường là LED onboard của ESP32)
#define LED_PIN 2 

WiFiClientSecure espClient;
PubSubClient client(espClient);
WiFiManager wm; // Đối tượng WiFiManager

// ======================== 2. KHỞI TẠO CẢM BIẾN ========================
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);
MAX30105 particleSensor;

// Biến tính toán BPM
const byte RATE_SIZE = 10;
byte rateSpot = 0;
float rates[RATE_SIZE];
long lastBeat = 0;
float bpm = 0;
float avgBpm = 0;

unsigned long lastPrint = 0;
const unsigned long PRINT_INTERVAL = 1000; // Gửi 1 giây/lần

// ======================== 3. HÀM NHẬN LỆNH TỪ SERVER ========================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String messageTemp;
  // Serial.print("\n[MSG] Nhan tu topic: ");
  // Serial.print(topic);
  // Serial.print(" | Noi dung: ");

  for (int i = 0; i < length; i++) {
    messageTemp += (char)payload[i];
  }
  // Serial.println(messageTemp);

  // Chỉ xử lý tin nhắn từ topic điều khiển
  if (String(topic) == TOPIC_CONTROL) {
    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, messageTemp);

    if (error) {
      Serial.println("Loi JSON!");
      return;
    }

    const char* target_serial = doc["device_serial"];
    const char* command = doc["command"];

    // Kiểm tra đúng thiết bị không
    if (String(target_serial) == String(DEVICE_SERIAL)) {
      
      // --- LỆNH BẬT/TẮT ĐÈN ---
      if (String(command) == "LED_ON") {
        digitalWrite(LED_PIN, HIGH); // BẬT ĐÈN
        Serial.println(">>> NGUY HIEM! DA BAT DEN CANH BAO <<<");
      } 
      else if (String(command) == "LED_OFF") {
        digitalWrite(LED_PIN, LOW);  // TẮT ĐÈN
        Serial.println(">>> BINH THUONG. DA TAT DEN <<<");
      }
      
      // --- LỆNH CẬP NHẬT WIFI (TỪ WEB) ---
      else if (String(command) == "UPDATE_WIFI") {
         const char* new_ssid = doc["ssid"];
         const char* new_pass = doc["password"];
         
         Serial.println("\n[LENH] Yeu cau doi Wifi tu Web!");
         Serial.print("SSID moi: "); Serial.println(new_ssid);
         
         // Xóa cấu hình cũ của WiFiManager
         wm.resetSettings(); 
         
         // Ngắt kết nối hiện tại
         WiFi.disconnect();
         
         // Lưu Wifi mới vào bộ nhớ (NVS) và thử kết nối
         // WiFi.begin() tự động lưu thông tin này cho lần khởi động sau
         WiFi.begin(new_ssid, new_pass);
         
         Serial.println("Dang khoi dong lai de ket noi Wifi moi...");
         delay(2000);
         ESP.restart(); // Khởi động lại ESP32
      }
    }
  }
}

// ======================== 4. CÁC HÀM KẾT NỐI ========================
void setup_wifi() {
  // Cấu hình WiFiManager
  // Tự động kết nối wifi cũ. Nếu thất bại, phát Wifi AP tên "HealthMonitor_Setup"
  // Người dùng kết nối vào Wifi này để cấu hình (IP: 192.168.4.1)
  
  Serial.println("Dang ket noi Wifi...");
  
  // wm.resetSettings(); // Bỏ comment dòng này nạp 1 lần để xóa wifi cũ nếu cần test lại từ đầu
  
  // Tùy chỉnh timeout (ví dụ 180s cho portal)
  wm.setConfigPortalTimeout(180); 

  bool res;
  // Tên Wifi phát ra và mật khẩu (nếu muốn)
  res = wm.autoConnect("HealthMonitor_Setup", "12345678"); 

  if(!res) {
      Serial.println("Ket noi that bai hoac het thoi gian. Restarting...");
      ESP.restart();
  } 
  else {
      Serial.println("\nWiFi Connected!");
      Serial.print("IP Address: ");
      Serial.println(WiFi.localIP());
  }

  // Cấu hình SSL cho HiveMQ
  espClient.setInsecure(); 
}

void reconnect() {
  // Lặp cho đến khi kết nối được
  while (!client.connected()) {
    Serial.print("Dang ket noi MQTT...");
    
    // Tạo Client ID ngẫu nhiên
    String clientId = "ESP32-";
    clientId += String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str(), MQTT_USER, MQTT_PASSWORD)) {
      Serial.println("THANH CONG!");
      // Đăng ký nhận lệnh điều khiển
      client.subscribe(TOPIC_CONTROL);
      Serial.println("Da dang ky topic: health/control");
    } else {
      Serial.print("That bai, rc=");
      Serial.print(client.state());
      Serial.println(" (thu lai sau 5s)");
      delay(5000);
    }
  }
}

// ======================== 5. MAIN SETUP ========================
void setup() {
  Serial.begin(115200);
  
  // Cấu hình chân LED & I2C
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW); 
  Wire.begin(21, 22); // SDA, SCL

  Serial.println("Khoi dong cam bien...");

  // Khởi tạo cảm biến ADXL345
  if (!accel.begin()) {
    Serial.println("Loi: Khong tim thay ADXL345!");
    // while (1); // Có thể bỏ qua để test các phần khác nếu cảm biến lỗi
  }
  accel.setRange(ADXL345_RANGE_16_G);

  // Khởi tạo cảm biến MAX30102
  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("Loi: Khong tim thay MAX30102!");
    // while (1);
  } else {
    particleSensor.setup();
    particleSensor.setPulseAmplitudeRed(0x1F);
    particleSensor.setPulseAmplitudeIR(0x1F);
  }

  // Kết nối Wifi & MQTT
  setup_wifi();
  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setCallback(mqttCallback);
  
  Serial.println("HE THONG DA SAN SANG!");
}

// ======================== 6. MAIN LOOP ========================
void loop() {
  // Giữ kết nối MQTT
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // --------- 1. Đọc gia tốc (ADXL345) -----------
  sensors_event_t event;
  accel.getEvent(&event);
  float ax = event.acceleration.x;
  float ay = event.acceleration.y;
  float az = event.acceleration.z;

  // --------- 2. Đọc nhịp tim (MAX30102) ----------
  // Lưu ý: Đảm bảo cảm biến MAX30102 hoạt động ổn định để không chặn luồng
  long irValue = particleSensor.getIR();

  if (irValue > 50000) { // Phát hiện ngón tay
    if (checkForBeat(irValue)) {
      unsigned long now = millis();
      unsigned long delta = now - lastBeat;
      lastBeat = now;

      float instantBPM = 60.0 / (delta / 1000.0);

      if (instantBPM >= 40 && instantBPM <= 180) {
        rates[rateSpot++] = instantBPM;
        rateSpot %= RATE_SIZE;

        avgBpm = 0;
        for (byte i = 0; i < RATE_SIZE; i++) avgBpm += rates[i];
        avgBpm /= RATE_SIZE;

        bpm = instantBPM;
      }
    }
  } else {
    bpm = 0;
    avgBpm = 0;
  }

  // --------- 3. Gửi dữ liệu lên MQTT ----------
  unsigned long nowPrint = millis();
  if (nowPrint - lastPrint >= PRINT_INTERVAL) {
    lastPrint = nowPrint;

    // Tạo JSON bằng thư viện ArduinoJson
    DynamicJsonDocument doc(1024);
    doc["device_serial"] = DEVICE_SERIAL;
    doc["bpm"] = bpm;
    doc["avg_bpm"] = avgBpm;
    doc["ir_value"] = irValue;
    doc["accel_x"] = ax;
    doc["accel_y"] = ay;
    doc["accel_z"] = az;

    char buffer[512];
    serializeJson(doc, buffer);

    // Serial.print(" Gửi: ");
    // Serial.println(buffer);
    
    client.publish(TOPIC_DATA, buffer);
  }
  
  // Delay nhỏ để tránh quá tải I2C nhưng vẫn giữ loop mượt
  // Lưu ý: WiFiManager có thể chặn loop nếu mất mạng, nhưng autoConnect chỉ chạy ở setup()
  // nên trong loop() nó sẽ không chặn trừ khi bạn gọi wm.process() (cho non-blocking mode)
  delay(20); 
}