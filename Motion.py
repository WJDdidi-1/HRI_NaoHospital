# -*- coding: utf-8 -*-
from naoqi import ALProxy
import math
import time
from Path_Calculation import dijkstra


IP      = "192.168.1.35"
PORT    = 9559

# Proxies
motion   = ALProxy("ALMotion",       IP, PORT)
posture  = ALProxy("ALRobotPosture", IP, PORT)
memory   = ALProxy("ALMemory",       IP, PORT)
tts      = ALProxy("ALTextToSpeech", IP, PORT)

# Tuned parameters
DRIFT_COMPENSATION  = 0.02
OBSTACLE_THRESHOLD  = 0.45
TURN_ANGLE          = math.radians(90)
FORWARD_STEP        = 0.15
SETTLE_FORWARD      = 0.05

# Initialize body balance once
motion.wbEnable(True)


def is_obstacle_ahead():

    left  = memory.getData("Device/SubDeviceList/US/Left/Sensor/Value")
    right = memory.getData("Device/SubDeviceList/US/Right/Sensor/Value")
    return (left < OBSTACLE_THRESHOLD) or (right < OBSTACLE_THRESHOLD)


def move_robot_along_path(path, maze, end):

    posture.goToPosture("StandInit", 1.0)
    time.sleep(1.0)
    motion.moveInit()
    motion.setMotionConfig([
        ["ENABLE_FOOT_CONTACT_PROTECTION", True],
        ["ENABLE_TRUNK_CONTROL",           True]
    ])

    tts.say("I am moving forward")

    prev_dx = path[1][0] - path[0][0]
    prev_dy = path[1][1] - path[0][1]

    for idx in range(1, len(path)):
        prev = path[idx-1]
        curr = path[idx]
        dx   = curr[0] - prev[0]
        dy   = curr[1] - prev[1]

        if is_obstacle_ahead():
            tts.say("Obstacle ahead, pausing")
            motion.stopMove()
            while is_obstacle_ahead():
                time.sleep(0.5)
            tts.say("Resuming movement")

        if (dx, dy) != (prev_dx, prev_dy):
            cross = prev_dx * dy - prev_dy * dx
            angle = TURN_ANGLE if cross > 0 else -TURN_ANGLE
            tts.say("Turning")
            motion.moveTo(0, 0, angle)
            motion.killMove()
            time.sleep(0.5)
            prev_dx, prev_
            dy = dx, dy

        motion.moveTo(FORWARD_STEP, DRIFT_COMPENSATION, 0)

    tts.say("Arrived at destination")
    motion.killMove()
    time.sleep(0.5)
    #motion.moveTo(SETTLE_FORWARD, 0, 0)
    #motion.moveTo(-SETTLE_FORWARD, 0, 0)
    #time.sleep(0.2)
    motion.wbEnable(True)
    time.sleep(0.5)
    posture.goToPosture("StandInit", 1.0)