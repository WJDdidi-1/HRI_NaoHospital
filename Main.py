# -*- coding: utf-8 -*-
from __future__ import print_function

import sys
import qi
import time
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

detect_flag = 0  # global emotion detection count

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
    # 1) 连接 NAOqi
    session = qi.Session()
    try:
        session.connect("tcp://%s:%d" % (robot_ip, robot_port))
    except Exception as e:
        print("Failed to connect to %s:%d.\n%s" % (robot_ip, robot_port, e))
        sys.exit(1)

    # 2) 创建 HybridSession，并启动摄像头 & 表情接收端口
    hybrid = HybridSession(session)
    cam = PCCameraReceiver(hybrid.pc_memory, port=8000)
    cam.start()
    print("PCCameraReceiver: Listening on port 8000")
    print("PCFaceDetection: Listening for expressions on port 8001")
    hybrid.pc_face.subscribe("ExprClient")

    # 3) 创建 RobotAssistant，用于后面 tts
    assistant = RobotAssistant(hybrid)

    # 4) 订阅 FaceExpression 事件，并在回调中让 NAO 说话
    expr_sub = hybrid.pc_memory.subscriber("FaceExpression")
    expr_result = {"label": None}

    def on_expr(val):
        global detect_flag
        if  detect_flag >= 2:
            return
        # 接收到的 val 是 [label] 列表
        label = val[0] if isinstance(val, list) else val
        expr_result["label"] = label

        if label == "happy":
            assistant.tts.say("You look happy. I'm glad to serve you. Where would you like to go?")
            detect_flag += 1
        elif label == "sad":
            assistant.tts.say("You look sad. I hope I can help you. Where would you like to go?")
            detect_flag += 1
        elif label == "angry":
            assistant.tts.say("You seem upset. I'm here to assist you. Where would you like to go?")
            detect_flag += 1
        else:
            return

    expr_sub.signal.connect(on_expr)

    # 5) 等待一次表情检测完成
    print("Please look at the camera for a moment...")
    while expr_result["label"] is None:
        # 保证回调线程能跑到
        time.sleep(0.1)

    # 6) 根据表情反馈完毕后，再提示输入模式
    print("\nSelect input mode:")
    print("  1) Voice input")
    print("  2) Keyboard input")
    choice = raw_input("Enter 1 or 2: ").strip()

    # 7) 根据选择进入键盘或语音模式
    if choice == "2":
        assistant.keyboard_mode = True
        # 取消 ASR/Face/Sound 的订阅
        try: assistant.asr.unsubscribe("VoiceRecog")
        except: pass
        try: assistant.face_detection.unsubscribe("FaceDetect")
        except: pass
        try: assistant.sound_loc.unsubscribe("SoundLoc")
        except: pass

        # 键盘模式导航
        keyboard_mode(assistant)
    else:
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
