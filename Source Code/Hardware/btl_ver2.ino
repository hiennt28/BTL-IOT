

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_ADXL345_U.h>
#include "MAX30105.h"
#include "heartRate.h"
#include <ArduinoJson.h> 

// ======================== 1. CẤU HÌNH WIFI & MQTT ========================
const char* WIFI_SSID = "TP-LINK";       
const char* WIFI_PASSWORD = "11223344";  

const char* MQTT_SERVER = "8c9b9eafe2434729af707f153e31a91f.s1.eu.hivemq.cloud";
const int MQTT_PORT = 8883;
const char* MQTT_USER = "nhom5";
const char* MQTT_PASSWORD = "Abc123456";

const char* DEVICE_SERIAL = "ESP32-001";
const char* TOPIC_DATA = "health/data";
const char* TOPIC_CONTROL = "health/control";

// Chân đèn LED cảnh báo (Trên ESP32 thường là GPIO 2)
#define LED_PIN 2 

WiFiClientSecure espClient;
PubSubClient client(espClient);

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
void callback(char* topic, byte* payload, unsigned int length) {
  String messageTemp;
  Serial.print("\n[MSG] Nhan tu topic: ");
  Serial.print(topic);
  Serial.print(" | Noi dung: ");

  for (int i = 0; i < length; i++) {
    messageTemp += (char)payload[i];
  }
  Serial.println(messageTemp);

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
    if (strcmp(target_serial, DEVICE_SERIAL) == 0) {
      if (strcmp(command, "LED_ON") == 0) {
        digitalWrite(LED_PIN, HIGH); // BẬT ĐÈN
        Serial.println(">>> NGUY HIEM! DA BAT DEN CANH BAO <<<");
      } 
      else if (strcmp(command, "LED_OFF") == 0) {
        digitalWrite(LED_PIN, LOW);  // TẮT ĐÈN
        Serial.println(">>> BINH THUONG. DA TAT DEN <<<");
      }
    }
  }
}

// ======================== 4. CÁC HÀM KẾT NỐI ========================
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Ket noi WiFi: ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi Connected!");
 
  espClient.setInsecure(); 
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Ket noi MQTT...");
    String clientId = "ESP32-" + String(random(0xffff), HEX);
    
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

  // Khởi tạo cảm biến ADXL345
  if (!accel.begin()) {
    Serial.println(" Khong tim thay ADXL345!");
    while (1);
  }
  accel.setRange(ADXL345_RANGE_16_G);

  // Khởi tạo cảm biến MAX30102
  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("Khong tim thay MAX30102!");
    while (1);
  }
  particleSensor.setup();
  particleSensor.setPulseAmplitudeRed(0x1F);
  particleSensor.setPulseAmplitudeIR(0x1F);

  setup_wifi();
  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setCallback(callback);
  
  Serial.println(" HE THONG DA SAN SANG!");
}

// ======================== 6. MAIN LOOP ========================
void loop() {
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

    // Tạo JSON bằng thư viện ArduinoJson cho an toàn
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

    Serial.print(" Gửi dữ liệu: ");
    Serial.println(buffer);
    
    client.publish(TOPIC_DATA, buffer);
  }
  
  // Sample rate nhỏ để đọc cảm biến mượt mà
  delay(10); 
}