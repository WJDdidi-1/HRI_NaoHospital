# -*- coding: utf-8 -*-
from __future__ import print_function

import sys
import qi
from naoqi import ALProxy

from GUI import get_updated_maze
from Navigation import run_navigation
from Path_Calculation import dijkstra, get_department_coord
from HRI_Speech_EmoRec_Interaction import (
    HybridSession,
    PCCameraReceiver,
    RobotAssistant,
    Navi,
    maze,
)

def keyboard_mode(assistant):
    print(">>> Keyboard mode ready. Type a keyword to navigate.")
    while True:
        try:
            cmd = raw_input("Your destination keyword (e.g. headache, stomach, lab): ").strip()
            if not cmd:
                continue
            dest_name = assistant.classify_destination([cmd], cmd)
            if not dest_name:
                print("Invalid keyword:", cmd)
                continue
            print("Navigating to", dest_name)
            Navi(dest_name, maze)
        except Exception as e:
            print("Error in keyboard mode:", e)

def main(robot_ip="192.168.1.35", robot_port=9559):
    # 1) Connect to NAOqi
    session = qi.Session()
    try:
        session.connect("tcp://%s:%d" % (robot_ip, robot_port))
    except Exception as e:
        print("Failed to connect to %s:%d.\n%s" % (robot_ip, robot_port, e))
        sys.exit(1)

    # 2) 创建 HybridSession (PC 端 ASR/Face/SoundLoc 服务)
    hybrid = HybridSession(session)

    # 3) 启动 PC-端摄像头与表情接收服务（在 8000/8001 端口监听）
    cam = PCCameraReceiver(hybrid.pc_memory, port=8000)
    cam.start()
    print("PCCameraReceiver: Listening on port 8000")
    print("PCFaceDetection: Listening for expressions on port 8001")

    hybrid.pc_face.subscribe("PCFace")
    print("\nSelect input mode:")
    print("  1) Voice input")
    print("  2) Keyboard input")
    choice = raw_input("Enter 1 or 2: ").strip()

    # 5) 创建机器人助手
    assistant = RobotAssistant(hybrid)

    if choice == "2":
        # 键盘模式
        assistant.keyboard_mode = True

        # 取消语音/人脸/声源定位订阅
        try:
            assistant.asr.unsubscribe("VoiceRecog")
        except:
            pass
        try:
            assistant.face_detection.unsubscribe("FaceDetect")
        except:
            pass
        try:
            assistant.sound_loc.unsubscribe("SoundLoc")
        except:
            pass

        keyboard_mode(assistant)
    else:
        # 语音模式
        assistant.keyboard_mode = False
        assistant.run()

if __name__ == "__main__":
    ip   = "192.168.1.35"
    port = 9559
    if len(sys.argv) >= 2:
        ip = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            port = int(sys.argv[2])
        except:
            pass
    main(ip, port)
