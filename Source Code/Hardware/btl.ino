#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_ADXL345_U.h>
#include "MAX30105.h"
#include "heartRate.h"


const char* ssid = "ten wifi";
const char* password = "matkhau";

const char* mqtt_server = "d2c7e1d6b7ff4636af82a88c157ff0a5.s1.eu.hivemq.cloud"; // link mqtt
const int mqtt_port = 8883;
const char* mqtt_user = "nhom5"; // user mqtt
const char* mqtt_pass = "Abc123456"; // matkhau mqtt

const char* device_serial = "ESP32-001";

WiFiClientSecure espClient;
PubSubClient client(espClient);
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);
MAX30105 particleSensor;

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
      Serial.println("MQTT kết nối Thành công!");
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

  Serial.print("Nội dung: ");
  String message = "";
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
    char c = (char)payload[i];
    message += c;
  }
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
  setup_wifi();
  pinMode(2, OUTPUT); 
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
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  sensors_event_t event;
  accel.getEvent(&event);
  float x = event.acceleration.x;
  float y = event.acceleration.y;
  float z = event.acceleration.z;

  byte rates[4] = { 0 };
  byte rateSpot = 0;
  long lastBeat = 0;
  float bpm = 0, avgBpm = 0;

  long irValue = particleSensor.getIR();
  if (irValue > 50000) {
    if (checkForBeat(irValue)) {
      long delta = millis() - lastBeat;
      lastBeat = millis();
      bpm = 60 / (delta / 1000.0);

      if (bpm > 20 && bpm < 255) {
        rates[rateSpot++] = (byte)bpm;
        rateSpot %= 4;
        avgBpm = 0;
        for (byte x = 0; x < 4; x++) avgBpm += rates[x];
        avgBpm /= 4;
      }
    }
  } else {
    bpm = avgBpm = 0;
  }

  char buffer[128];

  snprintf(buffer, sizeof(buffer),
           "{\"device_serial\":\"%s\",\"bpm\":%.2f,\"avg_bpm\":%.2f,"
           "\"ir_value\":%.2f,\"accel_x\":%.2f,\"accel_y\":%.2f,\"accel_z\":%.2f}",
           device_serial, bpm, avgBpm, irValue, x, y, z);

  client.publish("health/data", buffer);

  Serial.println("Sent data to MQTT:");
  Serial.println(buffer);
  delay(5000);
}
