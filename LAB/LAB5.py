from naoqi import ALProxy
import time

ROBOT_IP = "192.168.1.35"
PORT = 9559

def main():
    try:
        mood_proxy = ALProxy("ALMood", ROBOT_IP, PORT)
        tts = ALProxy("ALTextToSpeech", ROBOT_IP, PORT)

        time.sleep(2)

        person_state = mood_proxy.currentPersonState()
        print("current:", person_state)

        tts.say("Hello! How are you feeling today?")
        time.sleep(1)
        emotional_reaction = mood_proxy.getEmotionalReaction()
        print("emotion:", emotional_reaction)

        if emotional_reaction == "positive":
            tts.say("You seem happy! That's great!")
        elif emotional_reaction == "negative":
            tts.say("You look a bit sad. I hope you feel better soon!")
        elif emotional_reaction == "neutral":
            tts.say("You seem neutral. Let me know if I can do anything for you!")
        else:
            tts.say("I'm here to help! Let me know how you're feeling!")

    except Exception as e:
        print("error:", e)

if __name__ == "__main__":
    main()
