#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_ADXL345_U.h>
#include "MAX30105.h"
#include "heartRate.h"

// ======================== WiFi + MQTT ========================
const char* ssid = "TP-LINK";
const char* password = "11223344";

const char* mqtt_server = "8c9b9eafe2434729af707f153e31a91f.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char* mqtt_user = "nhom5";
const char* mqtt_pass = "Abc123456";

const char* device_serial = "ESP32-001";

WiFiClientSecure espClient;
PubSubClient client(espClient);

// ======================== Cảm biến ========================
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);
MAX30105 particleSensor;

// ======================== BPM smoothing ========================
const byte RATE_SIZE = 10;
byte rateSpot = 0;
float rates[RATE_SIZE];
long lastBeat = 0;
float bpm = 0;
float avgBpm = 0;

// ======================== Serial print interval ========================
unsigned long lastPrint = 0;
const unsigned long PRINT_INTERVAL = 1000; // in ms

// ======================== WiFi + MQTT ========================
void setup_wifi() {
  Serial.print("Kết nối WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi kết nối thành công");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Kết nối MQTT...");
    if (client.connect("ESP32_Client", mqtt_user, mqtt_pass)) {
      Serial.println("MQTT kết nối thành công!");
      client.subscribe("health/alert");
    } else {
      Serial.print("MQTT kết nối thất bại, mã lỗi: ");
      Serial.println(client.state());
      delay(5000);
    }
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Nhận được tin nhắn từ topic: ");
  Serial.println(topic);
  String message = "";
  for (int i = 0; i < length; i++) message += (char)payload[i];

  if (message == "ON") {
    Serial.println("Lệnh: Bật đèn LED!");
    digitalWrite(2, HIGH); 
  } else if (message == "OFF") {
    Serial.println("Lệnh: Tắt đèn LED!");
    digitalWrite(2, LOW);
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin(21,22);
  pinMode(2, OUTPUT); 

  setup_wifi();
  espClient.setInsecure();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  // ADXL345
  if (!accel.begin()) {
    Serial.println("Không tìm thấy ADXL345!");
    while (1);
  }
  accel.setRange(ADXL345_RANGE_16_G);

  // MAX30102
  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("Không tìm thấy MAX30102!");
    while (1);
  }
  particleSensor.setup();
  particleSensor.setPulseAmplitudeRed(0x1F);
  particleSensor.setPulseAmplitudeIR(0x1F);

  Serial.println("Thiết bị đã sẵn sàng!");
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  // --------- Đọc gia tốc -----------
  sensors_event_t event;
  accel.getEvent(&event);
  float ax = event.acceleration.x;
  float ay = event.acceleration.y;
  float az = event.acceleration.z;

  // --------- Đọc MAX30102 ----------
  long irValue = particleSensor.getIR();

  if (irValue > 50000) { // kiểm tra ngón tay
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
    bpm = avgBpm = 0;
  }

  // --------- Gửi dữ liệu lên MQTT 1 lần / giây ----------
  unsigned long nowPrint = millis();
  if (nowPrint - lastPrint >= 1000) {
    lastPrint = nowPrint;

    char buffer[256];
    snprintf(buffer, sizeof(buffer),
      "{\"device_serial\":\"%s\",\"bpm\":%.2f,\"avg_bpm\":%.2f,"
      "\"ir_value\":%ld,\"accel_x\":%.2f,\"accel_y\":%.2f,\"accel_z\":%.2f}",
      device_serial, bpm, avgBpm, irValue, ax, ay, az);

    client.publish("health/data", buffer);

    Serial.println("Sent data to MQTT:");
    Serial.println(buffer);
  }

  delay(10); // sample rate ~100Hz
}
