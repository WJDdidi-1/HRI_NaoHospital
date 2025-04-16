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
        client_socket.connect((SERVER_IP, SERVER_PORT))
        print("Connected to server at {}:{}".format(SERVER_IP, SERVER_PORT))
    except Exception as e:
        print("Failed to connect to server:", e)
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame from camera")
                break

            ret2, buffer = cv2.imencode('.jpg', frame)
            if not ret2:
                continue

            data = pickle.dumps(buffer)
            message_size = struct.pack("!L", len(data))
            try:
                client_socket.sendall(message_size + data)
            except Exception as e:
                print("Error sending data:", e)
                break

            cv2.imshow("Client - Captured Frame", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        client_socket.close()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
