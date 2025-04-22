from naoqi import ALProxy
import time

NAO_IP = "192.168.1.35"
NAO_PORT = 9559

motion = ALProxy("ALMotion", NAO_IP, NAO_PORT)
tts = ALProxy("ALTextToSpeech", NAO_IP, NAO_PORT)

def raise_hand_and_speak():
    motion.wakeUp()
    motion.setStiffnesses("Body", 1.0)
    names = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw"]
    angles = [-0.5, -0.2, 1.0, 0.5, 0.3]
    times = [1.0, 1.0, 1.0, 1.0, 1.0] 
    motion.angleInterpolation(names, angles, times, True)
    tts.say("Welcome to paradise!")
    time.sleep(2)
    angles_down = [1.5, 0.0, 0.0, 0.0, 0.0]
    motion.angleInterpolation(names, angles_down, times, True)
    motion.rest()
if __name__ == "__main__":
    try:
        raise_hand_and_speak()
    except Exception as e:
        print("An error occurred")
