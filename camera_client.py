import cv2
import socket
import struct
import pickle
import threading
import time

# 如果你用 Keras/TensorFlow
from tensorflow.keras.models import load_model
import numpy as np

# 配置
SERVER_IP = '127.0.0.1'
FRAME_PORT = 8000       # 原来的视频帧端口
EXPR_PORT = 8001        # 新增的表情标签端口

# 加载人脸检测 & 表情识别模型
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
expr_model = load_model('expression_model.h5')    # 请将模型文件放在同目录
expr_labels = ['angry','disgust','fear','happy','sad','surprise','neutral']

def recognize_expression(face_img):
    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (48, 48))
    normalized = resized.astype('float32') / 255.0
    input_data = normalized.reshape(1, 48, 48, 1)
    preds = expr_model.predict(input_data)
    return expr_labels[np.argmax(preds)]

def main():
    # 连接视频帧通道
    frame_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    frame_sock.connect((SERVER_IP, FRAME_PORT))
    # 新增：连接表情标签通道
    expr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    expr_sock.connect((SERVER_IP, EXPR_PORT))

    # 打开摄像头
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("[Client] Cannot open camera")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # —— 新增：表情识别（节流，每秒最多 2 次）
            start_ts = time.time()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 5)
            if len(faces) > 0:
                x, y, w, h = faces[0]
                face_roi = frame[y:y+h, x:x+w]
                expr_label = recognize_expression(face_roi)
                # 发送表情标签
                expr_sock.sendall(expr_label.encode('utf-8'))

            # —— 原有：发送视频帧
            ret2, buffer = cv2.imencode('.jpg', frame)
            if not ret2:
                continue
            data = pickle.dumps(buffer)
            message_size = struct.pack("!L", len(data))
            frame_sock.sendall(message_size + data)

            # 本地展示
            cv2.imshow("Client - Captured Frame", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # 控制识别频率
            elapsed = time.time() - start_ts
            if elapsed < 0.5:
                time.sleep(0.5 - elapsed)

    finally:
        cap.release()
        frame_sock.close()
        expr_sock.close()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()