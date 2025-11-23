import cv2
import numpy as np
import time
import json
import serial
import threading
import smtplib
import random
from email.mime.text import MIMEText
from flask import Flask, render_template, Response, jsonify
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array

# --- CẤU HÌNH ---
USE_ARDUINO = False   # Đổi thành True nếu cắm mạch thật
SERIAL_PORT = 'COM3' # Kiểm tra trong Device Manager
BAUD_RATE = 9600
EMAIL_SENDER = "ph124work@gmail.com"
EMAIL_PASSWORD = "sozwbqqflkcetjoq" # Dùng App Password của Google
EMAIL_RECEIVER = "ph124work@gmail.com"

app = Flask(__name__)

# --- BIẾN TOÀN CỤC ---
system_status = {
    "temp": 0, "gas": 0, "fire_detected": False, "alarm": False, "log": []
}
last_email_time = 0

# --- 1. AI MODEL LOAD ---
try:
    model = load_model('fire_model.h5')
    print("AI Model Loaded!")
except:
    print("Chưa có model, dùng chế độ giả lập AI (Color detection)!")
    model = None

# --- 2. SERIAL & SENSOR HANDLER ---
class MockSerial:
    def readline(self):
        # Giả lập dữ liệu gửi từ Arduino
        t = random.uniform(25, 35) + (20 if system_status['fire_detected'] else 0)
        g = random.randint(100, 300) + (400 if system_status['fire_detected'] else 0)
        return f'{{"temp": {t:.1f}, "gas": {g}}}\n'.encode()
    
    def write(self, x): pass

if USE_ARDUINO:
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    except:
        print("Không tìm thấy Arduino, chuyển sang Mock Mode.")
        ser = MockSerial()
else:
    ser = MockSerial()

def sensor_loop():
    global system_status
    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            if line:
                data = json.loads(line)
                system_status['temp'] = data.get('temp', 0)
                system_status['gas'] = data.get('gas', 0)
                
                # Logic Alarm Tổng hợp
                check_alarm()
        except Exception as e:
            pass
        time.sleep(0.5)

def check_alarm():
    global system_status, last_email_time
    is_fire = system_status['fire_detected']
    is_high_temp = system_status['temp'] > 50
    is_gas_leak = system_status['gas'] > 500
    
    if is_fire or is_high_temp or is_gas_leak:
        system_status['alarm'] = True
        msg = "ALARM: "
        if is_fire: msg += "Phát hiện LỬA! "
        if is_high_temp: msg += "Nhiệt độ CAO! "
        if is_gas_leak: msg += "Rò rỉ KHÍ GAS! "
        
        if msg not in system_status['log'][-1:]: # Tránh spam log
            system_status['log'].append(f"{time.strftime('%H:%M:%S')} - {msg}")
        
        # Gửi lệnh xuống Arduino để kêu còi
        if USE_ARDUINO: ser.write(b'A')
        
        # Gửi Email (Cooldown 60s)
        if time.time() - last_email_time > 60:
            send_email(msg)
            last_email_time = time.time()
    else:
        system_status['alarm'] = False
        if USE_ARDUINO: ser.write(b'N')

def send_email(content):
    try:
        msg = MIMEText(content)
        msg['Subject'] = 'CẢNH BÁO CHÁY TỪ SMART FIRE GUARD'
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(EMAIL_SENDER, EMAIL_PASSWORD)
        s.send_message(msg)
        s.quit()
        print("Đã gửi email cảnh báo!")
    except Exception as e:
        print(f"Lỗi gửi mail: {e}")

threading.Thread(target=sensor_loop, daemon=True).start()

# --- 3. CAMERA & AI PROCESSING ---
def generate_frames():
    camera = cv2.VideoCapture(0) # 0 là webcam, đổi thành đường dẫn file video để test simulation
    while True:
        success, frame = camera.read()
        if not success: break
        
        # AI Prediction
        img = cv2.resize(frame, (224, 224))
        img = img.astype("float") / 255.0
        img = img_to_array(img)
        img = np.expand_dims(img, axis=0)
        
        label = "Normal"
        color = (0, 255, 0)
        
        if model:
            pred = model.predict(img, verbose=0)[0][0]
            if pred < 0.5: # < 0.5 nghĩa là nghiêng về fire (Class 0)
                label = "FIRE DETECTED"
                color = (0, 0, 255)
                system_status['fire_detected'] = True
            else:
                label = "Normal"
                color = (0, 255, 0)
                system_status['fire_detected'] = False
        else:
             # Fallback nếu chưa train model: Dùng color threshold đơn giản
             hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
             lower = np.array([0, 50, 50]) # Màu cam/đỏ
             upper = np.array([35, 255, 255])
             mask = cv2.inRange(hsv, lower, upper)
             if cv2.countNonZero(mask) > 5000: # Nếu nhiều pixel màu đỏ
                 system_status['fire_detected'] = True
                 label = "FIRE SIMULATION"
                 color = (0, 0, 255)
             else:
                 system_status['fire_detected'] = False

        cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# --- 4. FLASK ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/data')
def get_data():
    return jsonify(system_status)

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)