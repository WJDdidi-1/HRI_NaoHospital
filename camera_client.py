import os
import cv2
import socket
import struct
import pickle
import time
import numpy as np
from tensorflow.keras.models import load_model

os.environ["TF_USE_LEGACY_KERAS"] = "1"

SERVER_IP = '127.0.0.1'
FRAME_PORT = 8000
EXPR_PORT = 8001

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

model_path = 'expression_model.h5'
if not os.path.exists(model_path):
    print("The expression model file expression_model.h5 was not found. Please place it in the current directory")
    exit(1)

expr_model = load_model(model_path, compile=False)
expr_labels = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']

def recognize_expression(face_img):
    try:
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)

        resized = cv2.resize(gray, (64, 64))

        normalized = resized.astype('float32') / 255.0

        input_data = normalized.reshape(1, 64, 64, 1)

        preds = expr_model.predict(input_data, verbose=0)
        idx = np.argmax(preds)
        label = expr_labels[idx]
        print("preds:", preds, "=>", label)
        return label
    except Exception as e:
        print("recognize_expression error:", e)
        return "unknown"


def main():
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("can not open camera")
        return
    print("camera opened")

    try:
        frame_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        frame_sock.connect((SERVER_IP, FRAME_PORT))
        print(f"connect to {FRAME_PORT}")
    except Exception as e:
        print(f"can not connect to {FRAME_PORT}：{e}")
        cap.release()
        return

    try:
        expr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        expr_sock.connect((SERVER_IP, EXPR_PORT))
        print(f"connect to expression port {EXPR_PORT}")
    except Exception as e:
        print(f"can not connect to expression port {EXPR_PORT}：{e}")
        frame_sock.close()
        cap.release()
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None or frame.size == 0:
                print("can not read frame")
                time.sleep(0.1)
                continue

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
                try:
                    expr_sock.sendall(expr_label.encode('utf-8'))
                except Exception as e:
                    print(f"fail to send expression：{e}")

            ret2, jpg = cv2.imencode('.jpg', frame)
            if not ret2:
                continue
            data = jpg.tobytes()
            message_size = struct.pack("!L", len(data))
            try:
                frame_sock.sendall(message_size + data)
            except Exception as e:
                print(f"fail to send message size：{e}")
                break
            #cv2.imshow("Client - Captured Frame", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            time.sleep(0.5)

    finally:
        print("release...")
        cap.release()
        frame_sock.close()
        expr_sock.close()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
