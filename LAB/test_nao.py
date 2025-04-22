from inspect import walktree

import naoqi
from naoqi import ALProxy
import time
import os

DESTINY = "192.168.1.35"
ROBOT_IP = DESTINY
PORT = 9559

tts = ALProxy("ALAnimatedSpeech",ROBOT_IP, PORT)
motion = ALProxy("ALMotion", ROBOT_IP, PORT)
audio_player = ALProxy("ALAudioPlayer", ROBOT_IP, PORT)

motion.wakeUp()

#audio_play
#local_path = os.path.join(os.getcwd(), "lightsaber.MP3")
#scp_command = "scp " + local_path + " nao@" + ROBOT_IP + ":/home/nao/"
#os.system(scp_command)
#audio_player.playFile("/home/nao/lightsaber.MP3")

#speech
message= "Hello there!"
message_str = "\\style=didactic\\ \\vol=90\\ \\wait=5\\" + message
tts.say(message_str)

#walk
motion.moveInit()
motion.move(0.2, 0, 0)
time.sleep(4)
motion.stopMove()

motion.rest()