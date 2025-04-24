import os
import cv2
import socket
import struct
import pickle
import time
import numpy as np
from tensorflow.keras.models import load_model

# 设置兼容 Keras 3 的环境变量（用于加载旧模型）
os.environ["TF_USE_LEGACY_KERAS"] = "1"

# 配置
SERVER_IP = '127.0.0.1'  # 改成服务器IP，如 NAO 的 IP
FRAME_PORT = 8000
EXPR_PORT = 8001

# 加载人脸检测模型
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# 加载表情识别模型
model_path = 'expression_model.h5'
if not os.path.exists(model_path):
    print("❌ 表情模型文件 expression_model.h5 未找到，请放在当前目录")
    exit(1)

expr_model = load_model(model_path, compile=False)
expr_labels = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']

def recognize_expression(face_img):
    try:
        # 1) 灰度化
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        # 2) 调整为 64×64 而不是 48×48
        resized = cv2.resize(gray, (64, 64))
        # 3) 归一化
        normalized = resized.astype('float32') / 255.0
        # 4) reshape 为 (1,64,64,1)
        input_data = normalized.reshape(1, 64, 64, 1)

        preds = expr_model.predict(input_data, verbose=0)
        idx = np.argmax(preds)
        label = expr_labels[idx]
        print("⚙️ preds:", preds, "=>", label)
        return label
    except Exception as e:
        print("⚠️ recognize_expression error:", e)
        return "unknown"


def main():
    # ✅ 第一步：先尝试打开摄像头
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("❌ 无法打开摄像头")
        return
    print("✅ 摄像头已打开")

    # ✅ 第二步：摄像头正常后再连接两个 socket
    try:
        frame_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        frame_sock.connect((SERVER_IP, FRAME_PORT))
        print(f"✅ 已连接到视频帧端口 {FRAME_PORT}")
    except Exception as e:
        print(f"❌ 无法连接到视频帧端口 {FRAME_PORT}：{e}")
        cap.release()
        return

    try:
        expr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        expr_sock.connect((SERVER_IP, EXPR_PORT))
        print(f"✅ 已连接到表情端口 {EXPR_PORT}")
    except Exception as e:
        print(f"❌ 无法连接到表情端口 {EXPR_PORT}：{e}")
        frame_sock.close()
        cap.release()
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None or frame.size == 0:
                print("⚠️ 摄像头读取失败或帧为空")
                time.sleep(0.1)
                continue

            # 人脸检测
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 5)

            if len(faces) > 0:
                x, y, w, h = faces[0]
                face_roi = frame[y:y + h, x:x + w]
                expr_label = recognize_expression(face_roi)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(
                frame, expr_label,
                 (x, y - 10),
                 cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                 (0, 255, 0), 2)
                # 发送表情标签
                try:
                    expr_sock.sendall(expr_label.encode('utf-8'))
                except Exception as e:
                    print(f"⚠️ 表情标签发送失败：{e}")

            # 发送视频帧
            ret2, jpg = cv2.imencode('.jpg', frame)
            if not ret2:
                continue
            data = jpg.tobytes()  # <--- 原始 JPEG bytes
            message_size = struct.pack("!L", len(data))
            try:
                frame_sock.sendall(message_size + data)
            except Exception as e:
                print(f"⚠️ 视频帧发送失败：{e}")
                break
            # 显示画面
            #cv2.imshow("Client - Captured Frame", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # 控制频率（最多每秒 2 次）
            time.sleep(0.5)

    finally:
        print("🔚 正在释放资源...")
        cap.release()
        frame_sock.close()
        expr_sock.close()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
