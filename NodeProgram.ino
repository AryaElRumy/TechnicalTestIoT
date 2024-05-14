#include <ModbusMaster.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WiFi & MQTT Configuration
const char* ssid = "your_wifi_ssid";
const char* password = "your_wifi_password";
const char* mqtt_server = "mosquito";
const int mqtt_port = 1883;
const char* clientID = "node1";
const char* topic = "DATA/LOCAL/SENSOR/PANEL_1";

WiFiClient wifiClient;
PubSubClient client(wifiClient);

// Modbus Configuration
ModbusMaster node;

// Register Addresses
#define VOLTAGE_REG 0x0123
#define CURRENT_REG 0x0234
#define POWER_REG   0x0345
#define TEMP_REG    0x03E8

// Variables
float voltage = 0.0;
float current = 0.0;
float power = 0.0;
float temperature = 0.0;
float prev_temperature = 27.0; // Assuming initial room temperature

void setup() {
  Serial.begin(9600);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  client.setServer(mqtt_server, mqtt_port);
  node.begin(1, Serial2); // Modbus slave ID 1, using Serial2 on ESP32
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  readSensors();
  sendMQTT();
  delay(1000); // 1 second interval
}

void readSensors() {
  uint8_t resultV = node.readHoldingRegisters(VOLTAGE_REG, 2);
  uint8_t resultC = node.readHoldingRegisters(CURRENT_REG, 2);
  uint8_t resultP = node.readHoldingRegisters(POWER_REG, 2);
  uint8_t resultT = node.readHoldingRegisters(TEMP_REG, 1);

  if (resultV == node.ku8MBSuccess) {
    voltage = node.getResponseBuffer(0) / 10.0;
  }
  
  if (resultC == node.ku8MBSuccess) {
    current = node.getResponseBuffer(0) / 10.0;
  }
  
  if (resultP == node.ku8MBSuccess) {
    power = node.getResponseBuffer(0) / 10.0;
  }
  
  if (resultT == node.ku8MBSuccess) {
    temperature = node.getResponseBuffer(0) / 10.0;
  }
}

void sendMQTT() {
  StaticJsonDocument<200> jsonDoc;
  jsonDoc["status"] = "OK";
  jsonDoc["deviceID"] = "yourname";
  JsonObject data = jsonDoc.createNestedObject("data");
  data["v"] = voltage;
  data["i"] = current;
  data["pa"] = power;
  data["temp"] = temperature;
  data["fan"] = (temperature > prev_temperature * 1.02) ? "ON" : "OFF";
  data["time"] = getTimeStamp();

  char buffer[200];
  serializeJson(jsonDoc, buffer);
  client.publish(topic, buffer);

  prev_temperature = temperature; // Update previous temperature
}

String getTimeStamp() {
  char timeBuffer[25];
  sprintf(timeBuffer, "%04d-%02d-%02d %02d:%02d:%02d", 
          year(), month(), day(), hour(), minute(), second());
  return String(timeBuffer);
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    if (client.connect(clientID)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}
