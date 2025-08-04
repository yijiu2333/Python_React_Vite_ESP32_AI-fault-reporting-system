#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "my-wifi";
const char* password = "123456";

// HTTP请求的目标URL（主机端运行的Python脚本的地址）
const char* serverURL = "http://192.168.20.14:3001/receive"; //修改为后端backend地址

const int buttonPin = 0;  // ESP32 的按钮通常连接到 GPIO0
const int ledPin = 2;     // ESP32 的 LED 通常连接到 GPIO2

void setup() {
  Serial.begin(115200);

  pinMode(ledPin, OUTPUT);  // 设置 GPIO2 为输出引脚

  // 配置按钮引脚为输入模式，并启用内部上拉电阻
  pinMode(buttonPin, INPUT_PULLUP);

  // 连接到WiFi网络
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
}

void loop() {
  // 检测按钮是否被按下（低电平表示按下）
  if (digitalRead(buttonPin) == LOW) {
    Serial.println("Button pressed, sending HTTP request...");

    digitalWrite(ledPin, HIGH);  // 点亮 LED
    delay(1000);  // 延时 1 秒
    digitalWrite(ledPin, LOW); // 熄灭 LED

    // 创建HTTP客户端对象
    WiFiClient client;
    HTTPClient http;

    // 连接到服务器并发送HTTP POST请求
    http.begin(client, serverURL);
    String postData = "message=数控车床"; // 要发送的字符串内容
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    int httpResponseCode = http.POST(postData);

    // 检查HTTP响应
    if (httpResponseCode > 0) {
      Serial.print("HTTP Response code: ");
      Serial.println(httpResponseCode);
    } else {
      Serial.print("Error code: ");
      Serial.println(httpResponseCode);
    }

    // 断开HTTP连接
    http.end();

    // 等待一段时间避免重复发送
    delay(500);
  }
}