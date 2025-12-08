#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_ADXL345_U.h>
#include "MAX30105.h"
#include "heartRate.h"
#include <ArduinoJson.h>
#include <HTTPUpdate.h>
#include <HTTPClient.h>

// ======================== CẤU HÌNH ========================
const char* WIFI_SSID = "ten wifi";       
const char* WIFI_PASSWORD = "matkhau";  

const char* MQTT_SERVER = "d2c7e1d6b7ff4636af82a88c157ff0a5.s1.eu.hivemq.cloud";
const int MQTT_PORT = 8883;
const char* MQTT_USER = "nhom5";
const char* MQTT_PASSWORD = "Abc123456";

const char* DEVICE_SERIAL = "ESP32-001";
const char* TOPIC_DATA = "health/data";
const char* TOPIC_CONTROL = "health/control";
const char* TOPIC_OTA = "health/ota";
const char* TOPIC_OTA_STATUS = "health/ota_status";

#define LED_PIN 2 

WiFiClientSecure espClient;
PubSubClient client(espClient);

// ======================== CẢM BIẾN ========================
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);
MAX30105 particleSensor;

const byte RATE_SIZE = 10;
byte rateSpot = 0;
float rates[RATE_SIZE];
long lastBeat = 0;
float bpm = 0;
float avgBpm = 0;

unsigned long lastPrint = 0;
const unsigned long PRINT_INTERVAL = 5000;

bool otaInProgress = false;

// ======================== GỬI TRẠNG THÁI OTA ========================
void sendOTAStatus(int progress, const char* status, const char* reason = "") {
  StaticJsonDocument<256> doc;
  doc["device_serial"] = DEVICE_SERIAL;
  doc["progress"] = progress;
  doc["status"] = status;
  doc["reason"] = reason;
  
  char buffer[256];
  serializeJson(doc, buffer);
  
  client.publish(TOPIC_OTA_STATUS, buffer);
  Serial.print("[OTA STATUS] ");
  Serial.println(buffer);
}

// ======================== HTTP OTA UPDATE ========================
void performHTTPOTA(const char* firmwareURL) {
  Serial.println("\n========================================");
  Serial.println("[HTTP OTA] BAT DAU CAP NHAT FIRMWARE");
  Serial.print("[HTTP OTA] URL: ");
  Serial.println(firmwareURL);
  Serial.println("========================================");
  
  otaInProgress = true;
  
  sendOTAStatus(5, "downloading", "Ket noi server");
  
  WiFiClient updateClient;
  
  // Callback theo dõi tiến trình
  httpUpdate.onProgress([](int current, int total) {
    int progress = (current * 100) / total;
    
    // Gửi status mỗi 10%
    static int lastReported = -1;
    if (progress / 10 != lastReported / 10) {
      lastReported = progress;
      
      if (progress <= 50) {
        sendOTAStatus(progress, "downloading", "Dang tai firmware");
        Serial.print("[HTTP OTA] Download: ");
      } else {
        sendOTAStatus(progress, "updating", "Dang ghi firmware");
        Serial.print("[HTTP OTA] Writing: ");
      }
      Serial.print(progress);
      Serial.println("%");
      if(progress==100){
        Serial.println("\n[HTTP OTA] THANH CONG!");
        sendOTAStatus(100, "success", "Cap nhat thanh cong");
    }
  });
  
  // Thực hiện HTTP update
  Serial.println("[HTTP OTA] Bat dau download...");
  t_httpUpdate_return ret = httpUpdate.update(updateClient, firmwareURL);
  
  switch (ret) {
    case HTTP_UPDATE_FAILED:
      Serial.println("\n[HTTP OTA] THAT BAI!");
      Serial.printf("Error (%d): %s\n", 
                    httpUpdate.getLastError(), 
                    httpUpdate.getLastErrorString().c_str());
      sendOTAStatus(0, "error", httpUpdate.getLastErrorString().c_str());
      break;
      
    case HTTP_UPDATE_NO_UPDATES:
      Serial.println("[HTTP OTA] Khong co update");
      sendOTAStatus(0, "error", "Khong co update");
      break;
      
    case HTTP_UPDATE_OK:
      Serial.println("\n[HTTP OTA] THANH CONG!");
      sendOTAStatus(100, "success", "Cap nhat thanh cong");
      delay(1000);
      Serial.println("[HTTP OTA] Dang khoi dong lai...");
      ESP.restart();
      break;
  }
  
  otaInProgress = false;
}

// ======================== CALLBACK MQTT ========================
void callback(char* topic, byte* payload, unsigned int length) {
  
  // XỬ LÝ LỆNH OTA
  if (String(topic) == TOPIC_OTA) {
    Serial.println("\n[OTA] NHAN LENH CAP NHAT FIRMWARE!");
    
    String messageTemp = "";
    for (unsigned int i = 0; i < length; i++) {
      messageTemp += (char)payload[i];
    }
    
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, messageTemp);

    if (error) {
      Serial.print("[OTA] LOI JSON: ");
      Serial.println(error.c_str());
      sendOTAStatus(0, "error", "Loi JSON");
      return;
    }

    const char* target_serial = doc["device_serial"];
    const char* command = doc["command"];
    const char* firmware_url = doc["firmware_url"];

    if (strcmp(target_serial, DEVICE_SERIAL) == 0) {
      if (strcmp(command, "START_OTA") == 0) {
        if (firmware_url && strlen(firmware_url) > 0) {
          Serial.print("[OTA] Firmware URL: ");
          Serial.println(firmware_url);
          
          // Thực hiện HTTP OTA
          performHTTPOTA(firmware_url);
        } else {
          Serial.println("[OTA] KHONG CO URL!");
          sendOTAStatus(0, "error", "Khong co URL");
        }
      }
    }
    return;
  }
  
  // XỬ LÝ ĐIỀU KHIỂN
  if (String(topic) == TOPIC_CONTROL) {
    String messageTemp = "";
    for (unsigned int i = 0; i < length; i++) {
      messageTemp += (char)payload[i];
    }
    
    StaticJsonDocument<256> doc;
    deserializeJson(doc, messageTemp);

    const char* target_serial = doc["device_serial"];
    const char* command = doc["command"];

    if (strcmp(target_serial, DEVICE_SERIAL) == 0) {
      if (strcmp(command, "LED_ON") == 0) {
        digitalWrite(LED_PIN, HIGH);
        Serial.println(">>> BAT DEN <<<");
      } 
      else if (strcmp(command, "LED_OFF") == 0) {
        digitalWrite(LED_PIN, LOW);
        Serial.println(">>> TAT DEN <<<");
      }
      else if (strcmp(command, "RESET_WIFI") == 0) {
        Serial.println("Reset WiFi");
        WiFi.disconnect(true, true);
        delay(200);
        WiFiManager wm;
        wm.resetSettings();
        delay(1000);
        ESP.restart();
      }
    }
  }
}

// ======================== WIFI & MQTT ========================
void setup_wifi() {
  Serial.print("Ket noi WiFi: ");
  Serial.println(WIFI_SSID);
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi OK");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
  
  espClient.setInsecure(); 
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Ket noi MQTT...");
    String clientId = "ESP32-" + String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str(), MQTT_USER, MQTT_PASSWORD)) {
      Serial.println("OK");
      client.subscribe(TOPIC_CONTROL);
      client.subscribe(TOPIC_OTA);
      Serial.println("Subscribed to OTA topic");
    } else {
      Serial.print("rc=");
      Serial.println(client.state());
      delay(5000);
    }
  }
}

// ======================== SETUP ========================
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n========================================");
  Serial.print("DEVICE: ");
  Serial.println(DEVICE_SERIAL);
  Serial.print("Free Heap: ");
  Serial.print(ESP.getFreeHeap());
  Serial.println(" bytes");
  Serial.println("========================================");
  
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW); 
  Wire.begin(21, 22);

  if (!accel.begin()) {
    Serial.println("ADXL345");
    while (1);
  }
  accel.setRange(ADXL345_RANGE_16_G);
  Serial.println("ADXL345 OK");

  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("MAX30102");
    while (1);
  }
  particleSensor.setup();
  particleSensor.setPulseAmplitudeRed(0x1F);
  particleSensor.setPulseAmplitudeIR(0x1F);
  Serial.println("MAX30102 OK");

  setup_wifi();
  
  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setCallback(callback);
  
  Serial.println("READY!");
}

// ======================== LOOP ========================
void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  if (otaInProgress) {
    delay(100);
    return;
  }

  // Đọc cảm biến
  sensors_event_t event;
  accel.getEvent(&event);
  
  long irValue = particleSensor.getIR();
  
  if (irValue > 50000) {
    if(checkForBeat(irValue)){
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

  if (millis() - lastPrint >= PRINT_INTERVAL) {
    lastPrint = millis();

    StaticJsonDocument<512> doc;
    doc["device_serial"] = DEVICE_SERIAL;
    doc["bpm"] = bpm;
    doc["avg_bpm"] = avgBpm;
    doc["ir_value"] = irValue;
    doc["accel_x"] = event.acceleration.x;
    doc["accel_y"] = event.acceleration.y;
    doc["accel_z"] = event.acceleration.z;

    char buffer[512];
    serializeJson(doc, buffer);
    client.publish(TOPIC_DATA, buffer);
  }
  
  delay(10); 
}
