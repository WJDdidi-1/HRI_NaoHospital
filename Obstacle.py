from naoqi import ALProxy
from GUI import get_updated_maze
from Navigation import run_navigation
import math
import time

# ---------------- Obstacle Avoidance Function ----------------

def avoid_obstacles_after_step(motionProxy, memoryProxy, threshold=0.5):
    """
    Simple obstacle avoidance function called after each step forward.
    It checks the sonar sensors and turns if an obstacle is detected.
    """
    try:
        left = memoryProxy.getData("Device/SubDeviceList/US/Left/Sensor/Value")
        right = memoryProxy.getData("Device/SubDeviceList/US/Right/Sensor/Value")
        print("[Sonar] Left: %.2f m, Right: %.2f m" % (left, right))

        if left < threshold or right < threshold:
            #print("[Obstacle] Detected! Initiating avoidance...")

            motionProxy.stopMove()
            time.sleep(3)


            #if left < right:
                #print("-> Turning right to avoid obstacle")
                #motionProxy.moveTo(0.0, 0.0, -0.5)
            #else:
                #print("<- Turning left to avoid obstacle")
                ##motionProxy.moveTo(0.0, 0.0, 0.5)

    except Exception as e:
        print("[Error] Obstacle detection failed:", str(e))
