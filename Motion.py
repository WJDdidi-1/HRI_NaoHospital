# -*- coding: utf-8 -*-
from naoqi import ALProxy
import math
import time
from Path_Calculation import dijkstra

# Connection parameters
IP      = "192.168.1.35"
PORT    = 9559

# Proxies
motion   = ALProxy("ALMotion",       IP, PORT)
posture  = ALProxy("ALRobotPosture", IP, PORT)
memory   = ALProxy("ALMemory",       IP, PORT)
tts      = ALProxy("ALTextToSpeech", IP, PORT)

# Tuned parameters
DRIFT_COMPENSATION  = 0.02           # m lateral offset to correct left drift
OBSTACLE_THRESHOLD  = 0.45           # m sonar stop distance
TURN_ANGLE          = math.radians(80)
FORWARD_STEP        = 0.15           # m per grid cell
SETTLE_FORWARD      = 0.05           # m for final settle wiggle

# Initialize whole-body balance once
motion.wbEnable(True)


def is_obstacle_ahead():
    """
    Return True if front sonar (left or right) reads below threshold.
    """
    left  = memory.getData("Device/SubDeviceList/US/Left/Sensor/Value")
    right = memory.getData("Device/SubDeviceList/US/Right/Sensor/Value")
    return (left < OBSTACLE_THRESHOLD) or (right < OBSTACLE_THRESHOLD)


def move_robot_along_path(path, maze, end):
    """
    Walk the robot along `path`:
      - pause during obstacles;
      - turn 80° at corners;
      - move FORWARD_STEP with drift compensation;
      - foot contact & trunk control enabled;
      - final settle wiggle and stand posture.
    """
    # 1) Ensure stable standing posture
    posture.goToPosture("StandInit", 1.0)
    time.sleep(1.0)
    motion.moveInit()
    motion.setMotionConfig([
        ["ENABLE_FOOT_CONTACT_PROTECTION", True],
        ["ENABLE_TRUNK_CONTROL",           True]
    ])

    # 2) Announce start
    tts.say("I am moving forward")

    # 3) Track previous direction
    prev_dx = path[1][0] - path[0][0]
    prev_dy = path[1][1] - path[0][1]

    # 4) Step through path
    for idx in range(1, len(path)):
        prev = path[idx-1]
        curr = path[idx]
        dx   = curr[0] - prev[0]
        dy   = curr[1] - prev[1]

        # 4a) Obstacle pause
        if is_obstacle_ahead():
            tts.say("Obstacle ahead, pausing")
            motion.stopMove()
            while is_obstacle_ahead():
                time.sleep(0.5)
            tts.say("Resuming movement")

        # 4b) Corner turn
        if (dx, dy) != (prev_dx, prev_dy):
            cross = prev_dx * dy - prev_dy * dx
            angle = TURN_ANGLE if cross > 0 else -TURN_ANGLE
            tts.say("Turning")
            motion.moveTo(0, 0, angle)
            # kill residual motion and let balance settle
            motion.killMove()
            time.sleep(0.5)
            prev_dx, prev_dy = dx, dy

        # 4c) Forward step
        motion.moveTo(FORWARD_STEP, DRIFT_COMPENSATION, 0)

    # 5) Arrival settle
    tts.say("Arrived at destination")
    motion.killMove()
    time.sleep(0.5)
    #motion.moveTo(SETTLE_FORWARD, 0, 0)
    #motion.moveTo(-SETTLE_FORWARD, 0, 0)
    #time.sleep(0.2)
    motion.wbEnable(True)
    time.sleep(0.5)
    # 6) Final stand
    posture.goToPosture("StandInit", 1.0)