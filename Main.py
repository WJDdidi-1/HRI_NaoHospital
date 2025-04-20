from __future__ import print_function

import sys
import threading
from naoqi import ALProxy
import qi

from GUI import get_updated_maze
from Navigation import run_navigation
from Path_Calculation import dijkstra
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
    session = qi.Session()
    session.connect("tcp://{}:{}".format(robot_ip, robot_port))

    hybrid = HybridSession(session)

    cam = PCCameraReceiver(hybrid.pc_memory, port=8000)
    cam.start()
    print("\nSelect input mode:")
    print("  1) Voice input")
    print("  2) Keyboard input")
    choice = raw_input("Enter 1 or 2: ").strip()

    if choice == "2":
        assistant = RobotAssistant(hybrid)
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
        assistant = RobotAssistant(hybrid)
        assistant.run()

if __name__ == "__main__":
    ip_addr = "192.168.1.35"
    port_num = 9559
    if len(sys.argv) >= 2:
        ip_addr = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            port_num = int(sys.argv[2])
        except:
            pass
    main(ip_addr, port_num)
