# -*- coding: utf-8 -*-
from GUI import get_updated_maze
from Navigation import run_navigation
import math
from naoqi import ALProxy
import qi
from Path_Calculation import dijkstra
from HRI_Speech_EmoRec_Interaction import (
    HybridSession,
    PCCameraReceiver,
    RobotAssistant,
)
import sys


# Configuration
PC_IP = "192.168.1.156"  # IP address of your PC
PC_PORT = 51599  # Port for communication between PC and NAO


# Connect to NAO robot
IP = "192.168.1.35"

#IP = "127.0.0.1"
PORT = 9559
motion = ALProxy("ALMotion", IP, PORT)
posture = ALProxy("ALRobotPosture", IP, PORT)

# Get map, start, end from GUI
#maze = get_updated_maze()



#=========================================Interaction==========================================================
def main(robot_ip="192.168.1.35", robot_port=9559):
    real_session = None
    try:
        real_session = qi.Session()
        real_session.connect("tcp://{}:{}".format(robot_ip, robot_port))
    except Exception as e:
        print("Cannot connect to Naoqi at {}:{}.\nError: {}".format(robot_ip, robot_port, e))
        sys.exit(1)

    hybrid_session = HybridSession(real_session)

    camera_receiver = PCCameraReceiver(hybrid_session.pc_memory, port=8000)
    camera_receiver.start()

    assistant = RobotAssistant(hybrid_session)
    assistant.run()

    # Execute robot motion
    #move_robot_along_path(assistant.path)


#==================================================================================================================


if __name__ == "__main__":
    ip = "192.168.1.35"
    port = 9559
    if len(sys.argv) >= 2:
        ip = sys.argv[1]
    if len(sys.argv) >= 3:
        port = int(sys.argv[2])
    main(ip, port)


