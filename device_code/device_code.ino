// =========================
// INCLUDES
// =========================
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_BMP280.h>
#include "time.h"

// =========================
// GLOBAL TIMERS
// =========================
unsigned long lastMinuteStart = 0;
const unsigned long ONE_MINUTE = 60000UL;

// =========================
// MQ7 VARIABLES
// =========================
const int MQ7_PIN = 34;           // MQ7 analog pin (ADC)
int mq7_buffer[60];               // one reading per second (60s window)
int mq7_index = 0;
int lastValidCO = 0;
bool mq7Valid = false;            // valid only during the stable phase
unsigned long mq7CycleStart = 0;  // to detect heating/valid windows

// =========================
// DSM501A VARIABLES (dual channel)
// =========================
const int DSM_PM10_PIN = 26;      // P1 output
const int DSM_PM25_PIN = 27;      // P2 output

const unsigned long DSM_WINDOW_MS = 30000UL;  // 30s window

// Interrupt tracking
volatile unsigned long pm10LowStart = 0;
volatile unsigned long pm10LowAccum = 0;

volatile unsigned long pm25LowStart = 0;
volatile unsigned long pm25LowAccum = 0;

// Window timing
unsigned long dsmWindowStart = 0;

// Two 30s windows -> average to 1-minute value
bool dsmFirstWindow = true;
float pm25_win1 = 0, pm10_win1 = 0;
float pm25_win2 = 0, pm10_win2 = 0;

// =========================
// BMP280 VARIABLES
// =========================
Adafruit_BMP280 bmp;  // I2C
float currentTemp = 0.0;
float currentPressure = 0.0;

// =========================
// MQTT CONFIG
// =========================
const char* ssid        = "";
const char* password    = "";

const char* mqtt_server = "broker.hivemq.com";
const int   mqtt_port   = 1883;
const char* mqtt_topic  = "";
const char* mqtt_control_topic = "";

WiFiClient espClient;
PubSubClient client(espClient);

// =========================
// FAN CONTROL (L298N)
// =========================
const int FAN_PWM = 15;   // ENA
const int FAN_IN1 = 18;
const int FAN_IN2 = 19;

const int FAN_PWM_CH   = 5;
const int FAN_PWM_FREQ = 25000;
const int FAN_PWM_RES  = 8;

// =========================
// TIME (NTP)
// =========================
void setupTime() {
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");

  Serial.print("Waiting for time sync");
  time_t now = time(nullptr);
  while (now < 100000) {   // wait until time is not 1970
    delay(500);
    Serial.print(".");
    now = time(nullptr);
  }
  Serial.println("\nTime synchronized!");
}

// =========================
// WIFI
// =========================
void setupWiFi() {
  Serial.print("Connecting to WiFi ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected.");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

// =========================
// BMP280
// =========================
void readBMP280() {
  currentTemp = bmp.readTemperature();
  currentPressure = bmp.readPressure() / 100.0;  // Pa → hPa
}

// =========================
// MQ7 LOGIC
// =========================

// Update heating/stable cycle
void updateMQ7Validity() {
  unsigned long elapsed = (millis() - mq7CycleStart) / 1000; // seconds

  if (elapsed < 60) {
    mq7Valid = false;  // heating phase
  } 
  else if (elapsed < 150) {
    mq7Valid = true;   // stable phase
  } 
  else {
    // restart cycle
    mq7CycleStart = millis();
    mq7Valid = false;
  }
}

// 1-second sampling into buffer
void sampleMQ7() {
  int raw = analogRead(MQ7_PIN);

  if (!mq7Valid) {
    raw = lastValidCO;     // keep last stable value during invalid phases
  } else {
    lastValidCO = raw;     // update stable value
  }

  mq7_buffer[mq7_index] = raw;
  mq7_index = (mq7_index + 1) % 60;
}

// Compute CO mean + max over last 60 samples
void computeMQ7Stats(float &mean, int &maxv) {
  long sum = 0;
  maxv = mq7_buffer[0];

  for (int i = 0; i < 60; i++) {
    sum += mq7_buffer[i];
    if (mq7_buffer[i] > maxv) maxv = mq7_buffer[i];
  }
  mean = sum / 60.0;
}

// =========================
// DSM501A INTERRUPTS
// =========================
void IRAM_ATTR pm10_isr() {
  int level = digitalRead(DSM_PM10_PIN);
  unsigned long now = micros();

  if (level == LOW) {
    pm10LowStart = now;
  } else {
    if (pm10LowStart != 0) {
      pm10LowAccum += (now - pm10LowStart);
      pm10LowStart = 0;
    }
  }
}

void IRAM_ATTR pm25_isr() {
  int level = digitalRead(DSM_PM25_PIN);
  unsigned long now = micros();

  if (level == LOW) {
    pm25LowStart = now;
  } else {
    if (pm25LowStart != 0) {
      pm25LowAccum += (now - pm25LowStart);
      pm25LowStart = 0;
    }
  }
}

// DSM501A conversion formula
void computePM(float ratio, float &pm25, float &pm10) {
  float conc = 0.172 * ratio * ratio + 0.002204 * ratio + 0.000002;
  pm25 = 1.1 * conc + 3.3;
  pm10 = 1.3 * conc + 5.2;
}

// End of 30-second window
void processDSMWindow() {
  noInterrupts();
  unsigned long pm10_low = pm10LowAccum;
  unsigned long pm25_low = pm25LowAccum;
  pm10LowAccum = 0;
  pm25LowAccum = 0;
  interrupts();

  float windowSec = DSM_WINDOW_MS / 1000.0;

  float pm10_ratio = (pm10_low / 1e6) / windowSec;
  float pm25_ratio = (pm25_low / 1e6) / windowSec;

  float pm25, pm10;
  computePM(pm25_ratio, pm25, pm10);

  float dummy25, pm10_from_ratio;
  computePM(pm10_ratio, dummy25, pm10_from_ratio);

  float final_pm25 = pm25;
  float final_pm10 = pm10_from_ratio;

  if (dsmFirstWindow) {
    pm25_win1 = final_pm25;
    pm10_win1 = final_pm10;
    dsmFirstWindow = false;
  } else {
    pm25_win2 = final_pm25;
    pm10_win2 = final_pm10;
    dsmFirstWindow = true;
  }
}

// Final PM for the minute (average of two 30-second windows)
void computeMinutePM(float &pm25, float &pm10) {
  pm25 = (pm25_win1 + pm25_win2) / 2.0;
  pm10 = (pm10_win1 + pm10_win2) / 2.0;
}

// =========================
// FAN HELPERS
// =========================
int percentToPWM(int percent) {
  if (percent < 0) percent = 0;
  if (percent > 100) percent = 100;
  return (percent * 255) / 100;
}

void setFanSpeed(int percent) {
  int pwmValue = percentToPWM(percent);
  ledcWrite(FAN_PWM_CH, pwmValue);

  Serial.print("⚙ FAN speed set to ");
  Serial.print(percent);
  Serial.print("% → PWM ");
  Serial.println(pwmValue);
}

// =========================
// MQTT CALLBACK
// =========================
void mqttCallback(char* topic, byte* message, unsigned int length) {

  Serial.print("\n📥 MQTT Message received on: ");
  Serial.println(topic);

  if (strcmp(topic, mqtt_control_topic) != 0) {
    Serial.println("Ignoring message from other topic.");
    return;
  }

  // Convert payload to string
  String payload;
  for (unsigned int i = 0; i < length; i++) {
    payload += (char)message[i];
  }

  Serial.println("Payload: " + payload);

  // Extract fan speed: expects JSON containing "fan_supply_speed": <number>
  int keyIndex = payload.indexOf("\"fan_exhaust_speed\":");
  if (keyIndex != -1) {
    int start = payload.indexOf(":", keyIndex) + 1;
    int end = payload.indexOf(",", start);
    if (end == -1) end = payload.indexOf("}", start);

    int speed = payload.substring(start, end).toInt();
    setFanSpeed(speed);   // <-- FAN CONTROL HERE
  } else {
    Serial.println("fan_supply_speed not found in payload.");
  }
}

// =========================
// MQTT RECONNECT
// =========================
void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT ... ");

    if (client.connect("ESP32_AirMonitor")) {
      Serial.println("connected.");

      // SUBSCRIBE HERE — ONLY ON SUCCESSFUL CONNECT
      client.subscribe(mqtt_control_topic);
      Serial.print("Subscribed to: ");
      Serial.println(mqtt_control_topic);

    } else {
      Serial.print("failed (");
      Serial.print(client.state());
      Serial.println("). Retry in 2 seconds...");
      delay(2000);
    }
  }
}

// =========================
// FINAL MINUTE PROCESSOR
// =========================
void processMinuteCycle() {
  // BMP280
  readBMP280();

  // MQ7
  float co_mean;
  int co_max;
  computeMQ7Stats(co_mean, co_max);

  // DSM501A
  float pm25, pm10;
  computeMinutePM(pm25, pm10);

  // Timestamp
  time_t now = time(nullptr);
  char timestamp[30];
  strftime(timestamp, sizeof(timestamp), "%Y-%m-%dT%H:%M:%SZ", gmtime(&now));

  // Serial debug
  Serial.println("---- MINUTE SUMMARY ----");
  Serial.print("Temp: "); Serial.println(currentTemp);
  Serial.print("Pressure: "); Serial.println(currentPressure);
  Serial.print("CO mean: "); Serial.println(co_mean);
  Serial.print("CO max : "); Serial.println(co_max);
  Serial.print("PM2.5  : "); Serial.println(pm25);
  Serial.print("PM10   : "); Serial.println(pm10);

  // Build JSON payload
  String payload = "{";
  payload += "\"timestamp\":\"" + String(timestamp) + "\",";
  payload += "\"temp\":" + String(currentTemp, 2) + ",";
  payload += "\"pressure\":" + String(currentPressure, 2) + ",";
  payload += "\"co_mean\":" + String(co_mean, 2) + ",";
  payload += "\"co_max\":" + String(co_max) + ",";
  payload += "\"co_valid\":" + String(mq7Valid ? "true" : "false") + ",";
  payload += "\"pm2_5\":" + String(pm25, 2) + ",";
  payload += "\"pm10\":" + String(pm10, 2);
  payload += "}";

  Serial.println("=== MQTT Payload ===");
  Serial.println(payload);

  // Publish to MQTT
  client.publish(mqtt_topic, payload.c_str());
}

// =========================
// SETUP
// =========================
void setup() {
  Serial.begin(115200);
  delay(200);

  setupWiFi();
  setupTime();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqttCallback);

  // MQ7 cycle start
  mq7CycleStart = millis();

  // FAN pins
  pinMode(FAN_IN1, OUTPUT);
  pinMode(FAN_IN2, OUTPUT);

  // Fixed direction (supply fan)
  digitalWrite(FAN_IN1, HIGH);
  digitalWrite(FAN_IN2, LOW);

  // PWM setup
  ledcSetup(FAN_PWM_CH, FAN_PWM_FREQ, FAN_PWM_RES);
  ledcAttachPin(FAN_PWM, FAN_PWM_CH);
  ledcWrite(FAN_PWM_CH, 0);  // Fan OFF initially

  // DSM501A setup (dual channel)
  pinMode(DSM_PM10_PIN, INPUT);
  pinMode(DSM_PM25_PIN, INPUT);

  attachInterrupt(digitalPinToInterrupt(DSM_PM10_PIN), pm10_isr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(DSM_PM25_PIN), pm25_isr, CHANGE);

  dsmWindowStart = millis();

  // BMP280
  if (!bmp.begin(0x76)) {
    Serial.println("BMP ERROR! Check wiring / address.");
    while (1) {
      delay(1000);
    }
  }

  // Start minute cycle
  lastMinuteStart = millis();

  // Initialize MQ7 buffer to 0 to avoid random junk in first minute
  for (int i = 0; i < 60; i++) {
    mq7_buffer[i] = 0;
  }
}

// =========================
// LOOP
// =========================
void loop() {

  // --- MQTT connection ---
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();

  // --- Update MQ7 cycle (heating/valid) ---
  updateMQ7Validity();

  // ============ MQ7 sampling every 1 sec ============
  static unsigned long lastMQ7Sample = 0;
  if (millis() - lastMQ7Sample >= 1000) {
    lastMQ7Sample = millis();
    sampleMQ7();
  }

  // ============ DSM501A window every 30 sec ============
  if (millis() - dsmWindowStart >= DSM_WINDOW_MS) {
    dsmWindowStart = millis();
    processDSMWindow();
  }

  // ============ Full minute summary ============
  if (millis() - lastMinuteStart >= ONE_MINUTE) {
    lastMinuteStart = millis();
    processMinuteCycle();
  }
}
