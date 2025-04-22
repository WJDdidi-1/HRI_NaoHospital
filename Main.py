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

    # 2) Create HybridSession (ASR, face, sound loc)
    hybrid = HybridSession(session)

    # NOTE: Do NOT start PCCameraReceiver here, so the USB webcam stays free
    # cam = PCCameraReceiver(hybrid.pc_memory, port=8000)
    # cam.start()

    # 3) Prompt for input mode
    print("\nSelect input mode:")
    print("  1) Voice input")
    print("  2) Keyboard input")
    choice = raw_input("Enter 1 or 2: ").strip()

    assistant = RobotAssistant(hybrid)
    if choice == "2":
        # Keyboard mode
        assistant.keyboard_mode = True

        # Unsubscribe voice/face/sound loc services
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
        # Voice mode
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
