from naoqi import ALProxy
import math
from Obstacle import avoid_obstacles_after_step

IP = "192.168.1.35"  # IP address of your PC
PORT = 9559  # Port for communication between PC and NAO

motion = ALProxy("ALMotion", IP, PORT)
posture = ALProxy("ALRobotPosture", IP, PORT)
memory = ALProxy("ALMemory", IP, PORT)


import math

def move_robot_along_path(path):

    posture.goToPosture("StandInit", 1)

    print("Move forward 0.15m")
    motion.setWalkTargetVelocity(0.5, 0, 0, 0.3)
    motion.moveTo(0.15, 0, 0)
    motion.stopMove()

    turn_flag = 0

    for i in range(2, len(path)):
        x2, y2 = path[i]
        x1, y1 = path[i - 1]
        x0, y0 = path[i - 2]

        dx = x2 - x1
        dy = y2 - y1
        dx_prev = x1 - x0
        dy_prev = y1 - y0

        if (dy != 0 and dx_prev != 0) or (dx != 0 and dy_prev != 0):
            if turn_flag == 0:
                if dx != 0:
                    if dy_prev == 1 and dx == 1:
                        print("Turn right")
                        motion.moveTo(0, 0, -math.pi / 2)
                    elif dy_prev == 1 and dx == -1:
                        print("Turn left")
                        motion.moveTo(0, 0, math.pi / 2)
                    elif dy_prev == -1 and dx == 1:
                        print("Turn left")
                        motion.moveTo(0, 0, math.pi / 2)
                    elif dy_prev == -1 and dx == -1:
                        print("Turn right")
                        motion.moveTo(0, 0, -math.pi / 2)

                elif dy != 0:
                    if dx_prev == 1 and dy == 1:
                        print("Turn left")
                        motion.moveTo(0, 0, math.pi / 2)
                    elif dx_prev == 1 and dy == -1:
                        print("Turn right")
                        motion.moveTo(0, 0, -math.pi / 2)
                    elif dx_prev == -1 and dy == 1:
                        print("Turn right")
                        motion.moveTo(0, 0, -math.pi / 2)
                    elif dx_prev == -1 and dy == -1:
                        print("Turn left")
                        motion.moveTo(0, 0, math.pi / 2)

                turn_flag = 1

        print("Move forward 0.15m")
        motion.setWalkTargetVelocity(0.5, 0, 0, 0.3)
        motion.moveTo(0.15, 0, 0)
        motion.stopMove()

        turn_flag = 0


    print("Finished. 180")
    motion.moveTo(0, 0, math.pi)
