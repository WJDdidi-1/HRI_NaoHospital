#!/usr/bin/env python3
import cv2
import socket
import struct
import pickle

def main():
    SERVER_IP = '127.0.0.1'
    SERVER_PORT = 8000

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        print("[Client] Trying to connect to server...")
        client_socket.connect((SERVER_IP, SERVER_PORT))
        print("[Client] Connected to server at {}:{}".format(SERVER_IP, SERVER_PORT))
    except Exception as e:
        print("[Client] Failed to connect to server:", e)
        return

    # ✅ 强制使用 DirectShow 后端打开摄像头，解决 MSMF 报错问题
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("[Client] Cannot open camera")
        return
    else:
        print("[Client] Camera opened successfully.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[Client] Failed to read frame from camera")
                break

            ret2, buffer = cv2.imencode('.jpg', frame)
            if not ret2:
                print("[Client] Failed to encode frame")
                continue

            data = pickle.dumps(buffer)
            message_size = struct.pack("!L", len(data))
            try:
                client_socket.sendall(message_size + data)
                print("[Client] Sent a frame of size:", len(data))
            except Exception as e:
                print("[Client] Error sending data:", e)
                break

            cv2.imshow("Client - Captured Frame", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[Client] Quit signal received. Exiting.")
                break
    finally:
        print("[Client] Releasing camera and closing socket.")
        cap.release()
        client_socket.close()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()