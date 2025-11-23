// Arduino Code cho Tinkercad & Hardware thật
 #include <Arduino.h>

const int PIN_GAS = A0;
const int PIN_TEMP = A1;
const int PIN_BUZZER = 8;
const int PIN_LED_RED = 13;
const int PIN_LED_GREEN = 12;

void setup() {
  Serial.begin(9600); // Giao tiếp với Python
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_LED_GREEN, OUTPUT);
  
  // Warm up sensor (mô phỏng thì không cần đợi lâu)
  delay(1000);
}

void loop() {
  // 1. Đọc dữ liệu
  int gasValue = analogRead(PIN_GAS);
  int tempReading = analogRead(PIN_TEMP);
  
  // Chuyển đổi nhiệt độ cho TMP36 (Voltage -> Celsius)
  float voltage = tempReading * 5.0;
  voltage /= 1024.0;
  float tempC = (voltage - 0.5) * 100; 

  // 2. Gửi dữ liệu lên Python (Dạng JSON string cho dễ parse)
  // Format: {"gas": 120, "temp": 32.5}
  Serial.print("{\"gas\":");
  Serial.print(gasValue);
  Serial.print(",\"temp\":");
  Serial.print(tempC);
  Serial.println("}");

  // 3. Nhận lệnh từ Python (Nếu Python phát hiện lửa -> Kêu còi)
  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == 'A') { // A = Alarm ON
      digitalWrite(PIN_LED_RED, HIGH);
      digitalWrite(PIN_LED_GREEN, LOW);
      tone(PIN_BUZZER, 1000); 
    } else if (command == 'N') { // N = Normal
      digitalWrite(PIN_LED_RED, LOW);
      digitalWrite(PIN_LED_GREEN, HIGH);
      noTone(PIN_BUZZER);
    }
  }
  
  // (Tùy chọn) Logic dự phòng: Tự kêu nếu gas quá cao kể cả khi mất kết nối Python
  // (Tùy chọn) Logic dự phòng
  if (gasValue > 600) { 
      tone(PIN_BUZZER, 1000); 
  } else if (Serial.available() == 0) { 
      // Chỉ tắt còi khi không có lệnh từ Python VÀ Gas an toàn
      noTone(PIN_BUZZER); 
  }

  delay(500); // Update mỗi 0.5s
}