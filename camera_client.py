#!/usr/bin/env python3
import cv2
import socket
import struct
import pickle

def main():
    # 设置接收端服务器的 IP 和端口（这里假设服务器在本机，根据实际情况修改）
    SERVER_IP = '127.0.0.1'
    SERVER_PORT = 8000

    # 建立 TCP 连接
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((SERVER_IP, SERVER_PORT))
        print("Connected to server at {}:{}".format(SERVER_IP, SERVER_PORT))
    except Exception as e:
        print("Failed to connect to server:", e)
        return

    # 打开摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return
    else:
        print("Camera opened successfully.")

    try:
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame from camera")
                break
            frame_count += 1
            print("Captured frame {}".format(frame_count))

            # 将采集到的帧进行 JPEG 压缩
            ret2, buffer = cv2.imencode('.jpg', frame)
            if not ret2:
                print("Failed to encode frame {}".format(frame_count))
                continue
            else:
                print("Frame {} encoded successfully.".format(frame_count))

            # 使用 pickle 序列化压缩后的数据
            data = pickle.dumps(buffer)
            data_length = len(data)
            print("Frame {} pickle data size: {} bytes".format(frame_count, data_length))

            # 先将数据长度打包为固定长度（使用 unsigned long 格式）
            message_size = struct.pack("L", data_length)
            # 发送长度信息和数据
            try:
                client_socket.sendall(message_size + data)
                print("Frame {} sent successfully.".format(frame_count))
            except Exception as send_error:
                print("Error sending frame {}: {}".format(frame_count, send_error))
                break

            # 可选：在客户端显示采集到的帧（调试用）
            cv2.imshow("Client - Captured Frame", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Quit signal received, exiting.")
                break
    except Exception as e:
        print("Error during transmission:", e)
    finally:
        cap.release()
        client_socket.close()
        cv2.destroyAllWindows()
        print("Camera and socket closed.")

if __name__ == '__main__':
    main()