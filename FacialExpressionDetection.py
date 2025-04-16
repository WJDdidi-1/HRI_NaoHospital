import qi
from naoqi import ALProxy
import time
import datetime
import csv
import os
import sys

class RobotAssistant(object):
    def __init__(self, session):
        self.session = session

        try:
            self.asr = session.service("ALSpeechRecognition")
            self.tts = session.service("ALTextToSpeech")
            self.face_detection = session.service("ALFaceDetection")
            self.motion = session.service("ALMotion")
            self.posture = session.service("ALRobotPosture")
            self.memory = session.service("ALMemory")
            self.sound_loc = session.service("ALSoundLocalization")
        except Exception as e:
            print("Error getting NAOqi services: {}".format(e))
            raise

        # Set the language for speech recognition and TTS to English
        try:
            self.asr.setLanguage("English")
        except Exception as e:
            print("Failed to set ASR language: {}".format(e))
        try:
            self.tts.setLanguage("English")
        except Exception as e:
            print("Failed to set TTS language: {}".format(e))

        # Define the vocabulary for speech recognition
        vocab = [
            "headache", "pain", "hurt", "hurts", "unwell", "sick", "internal medicine",
            "stomach", "abdomen", "belly", "stomach ache", "gastroenterology",
            "toilet", "bathroom", "restroom", "washroom",
            "surgery", "trauma", "fracture", "broken", "injury",
            "ear", "nose", "throat", "earache", "sore throat", "ENT",
            "emergency", "help", "urgent",
            "laboratory", "lab", "test", "blood test"
        ]
        try:
            self.asr.setVocabulary(vocab, True)
        except Exception as e:
            print("Failed to set ASR vocabulary: {}".format(e))

        self.last_sound_energy = 0.0
        self.last_sound_time = time.time()
        self.last_interaction_time = time.time()
        self.sleeping = False

        try:
            # Subscribe to speech recognition events
            self.asr.subscribe("VoiceRecog")
            word_subscriber = self.memory.subscriber("WordRecognized")
            word_subscriber.signal.connect(self.on_word_recognized)

            # Subscribe to face detection events
            self.face_detection.subscribe("FaceDetect", 500, 0.0)
            face_subscriber = self.memory.subscriber("FaceDetected")
            face_subscriber.signal.connect(self.on_face_detected)

            # Subscribe to sound localization events (for sound detection)
            self.sound_loc.setParameter("EnergyComputation", True)
            self.sound_loc.subscribe("SoundLoc")
            sound_subscriber = self.memory.subscriber("ALSoundLocalization/SoundLocated")
            sound_subscriber.signal.connect(self.on_sound_detected)
        except Exception as e:
            print("Failed to subscribe to one of the events: {}".format(e))
            raise

        try:
            self.tts.setParameter("speed", 90)
        except Exception:
            pass

        # Prepare the CSV log file
        self.log_file = "interaction_log.csv"
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Emotion", "Trigger", "Timestamp"])

    def classify_destination(self, recognized_words, full_text):
        dest_category = None
        dest_name = None
        # Destination mapping in English
        destinations = {
            "internal": "the internal medicine department",
            "gastro": "the gastroenterology department",
            "restroom": "the restroom",
            "surgery": "the surgery department",
            "ent": "the ENT department",
            "emergency": "the emergency department",
            "lab": "the laboratory"
        }
        # Mapping of keywords to destination categories
        english_map = {
            "headache": "internal", "pain": "internal", "hurt": "internal", "unwell": "internal", "sick": "internal", "internal medicine": "internal",
            "stomach": "gastro", "abdomen": "gastro", "belly": "gastro", "stomach ache": "gastro", "gastroenterology": "gastro",
            "toilet": "restroom", "bathroom": "restroom", "restroom": "restroom", "washroom": "restroom",
            "surgery": "surgery", "trauma": "surgery", "fracture": "surgery", "broken": "surgery", "injury": "surgery",
            "ear": "ent", "nose": "ent", "throat": "ent", "earache": "ent", "sore throat": "ent", "ent": "ent",
            "emergency": "emergency", "help": "emergency", "urgent": "emergency",
            "laboratory": "lab", "lab": "lab", "test": "lab", "blood test": "lab"
        }
        categories_found = []
        for rec_word in recognized_words:
            key = rec_word.lower()
            if key in english_map:
                categories_found.append(english_map[key])
        categories_found = list(set(categories_found))
        if len(categories_found) == 1:
            dest_category = categories_found[0]
        elif len(categories_found) > 1:
            if "restroom" in categories_found:
                dest_category = "restroom"
            elif "emergency" in categories_found:
                dest_category = "emergency"
            else:
                filtered = [cat for cat in categories_found if cat != "internal"]
                if len(filtered) == 1:
                    dest_category = filtered[0]
                elif len(filtered) > 1:
                    dest_category = filtered[0]
                else:
                    dest_category = "internal"
        else:
            dest_category = None
        if dest_category:
            dest_name = destinations[dest_category]
        return dest_name

    def classify_emotion(self, recognized_text, energy):
        """
        Determine the emotion category (happy, sad, angry, neutral) based on voice volume and keywords.
        
        First, check the recognized text for emotion keywords:
          - Happy keywords: ["thank", "thanks", "thank you", "great"]
          - Angry keywords: ["emergency", "help", "urgent", "angry"]
          - Sad keywords: ["headache", "pain", "unwell", "sick", "hurt"]
        
        If a keyword is found, return the corresponding emotion.
        If no emotion keywords are found, then use the voice energy (volume) to determine emotion:
          - If energy > 2000, return "angry"
          - If 800 < energy <= 2000, return "happy"
          - If energy <= 300, return "sad"
          - Otherwise, return "neutral"
        """
        text = recognized_text.lower() if recognized_text else ""
        happy_words = ["thank", "thanks", "thank you", "great"]
        angry_words = ["emergency", "help", "urgent", "angry"]
        sad_words = ["headache", "pain", "unwell", "sick", "hurt"]

        # Priority: keyword-based emotion detection
        if any(word in text for word in happy_words):
            return "happy"
        elif any(word in text for word in angry_words):
            return "angry"
        elif any(word in text for word in sad_words):
            return "sad"
        
        # Fallback: voice energy-based detection
        if energy is not None:
            if energy > 2000:
                return "angry"
            elif 800 < energy <= 2000:
                return "happy"
            elif energy <= 300:
                return "sad"
            else:
                return "neutral"
        return "neutral"

    def on_word_recognized(self, value):
        """
        Callback for when speech is recognized.
        Processes recognized words to determine destination and emotion, then responds and logs the interaction.
        """
        if not value:
            return
        recognized_words = []
        text_combined = ""
        try:
            for i in range(0, len(value), 2):
                if i < len(value):
                    word = value[i]
                    if not word:
                        continue
                    conf = value[i+1] if (i+1 < len(value) and isinstance(value[i+1], float)) else 1.0
                    if conf >= 0.4:
                        recognized_words.append(str(word))
            text_combined = " ".join(recognized_words)
        except Exception as e:
            print("Error parsing WordRecognized value: {}, raw value: {}".format(e, value))
            text_combined = str(value)
            recognized_words = [text_combined]
        if text_combined == "" and recognized_words:
            text_combined = " ".join(recognized_words)
        if not recognized_words:
            return

        self.last_interaction_time = time.time()
        if self.sleeping:
            self.wake_up()
            self.sleeping = False

        destination = self.classify_destination(recognized_words, text_combined)
        emotion = self.classify_emotion(text_combined, self.last_sound_energy)
        self.log_interaction(emotion, "voice")

        if destination:
            self.tts.say("Please follow me, I'll take you to {}.".format(destination))
            try:
                # Assume Navi(destination) is implemented elsewhere.
                Navi(destination)
            except Exception as e:
                print("Navigating to {} (simulated).".format(destination))
        else:
            self.tts.say("I'm sorry, I didn't catch that. Could you please repeat?")

    def on_face_detected(self, value):
        """
        Callback for when a face is detected.
        Wakes the robot from sleep and greets the user.
        """
        if not value:
            return
        face_detected = False
        try:
            if isinstance(value, list) and len(value) >= 2:
                faceInfoArray = value[1]
                if faceInfoArray and isinstance(faceInfoArray, list) and len(faceInfoArray) > 0:
                    face_detected = True
        except Exception as e:
            face_detected = True
        if face_detected:
            self.last_interaction_time = time.time()
            if self.sleeping:
                self.wake_up()
                self.sleeping = False
                self.tts.say("Hello, how can I help you?")
                self.log_interaction("neutral", "face")

    def on_sound_detected(self, value):
        energy = None
        try:
            if isinstance(value, list) and len(value) > 1:
                locData = value[1]
                if isinstance(locData, list) and len(locData) >= 4:
                    energy = float(locData[3])
        except Exception as e:
            print("Error parsing SoundLocated data: {}, raw: {}".format(e, value))
        if energy is not None:
            self.last_sound_energy = energy
            self.last_sound_time = time.time()
        SOUND_WAKE_THRESHOLD = 1500.0
        if self.sleeping and energy is not None and energy > SOUND_WAKE_THRESHOLD:
            self.wake_up()
            self.sleeping = False
            self.last_interaction_time = time.time()

    def wake_up(self):
        try:
            self.posture.goToPosture("StandInit", 0.5)
        except Exception as e:
            try:
                self.motion.setAngles("HeadPitch", 0.0, 0.1)
                self.motion.setAngles("HeadYaw", 0.0, 0.1)
                self.motion.setAngles("LShoulderPitch", 1.4, 0.1)
                self.motion.setAngles("RShoulderPitch", 1.4, 0.1)
                self.motion.setAngles("LShoulderRoll", 0.0, 0.1)
                self.motion.setAngles("RShoulderRoll", 0.0, 0.1)
            except Exception as e2:
                print("Failed to set wake-up posture: {}".format(e2))

    def go_to_sleep(self):
        try:
            self.posture.goToPosture("StandZero", 0.5)
            self.motion.setAngles("HeadPitch", 0.45, 0.1)
        except Exception as e:
            try:
                self.motion.setAngles("HeadPitch", 0.45, 0.1)
                self.motion.setAngles("HeadYaw", 0.0, 0.1)
                self.motion.setAngles("LShoulderPitch", 1.5, 0.1)
                self.motion.setAngles("RShoulderPitch", 1.5, 0.1)
            except Exception as e2:
                print("Failed to set sleep posture: {}".format(e2))

    def log_interaction(self, emotion, trigger):
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([emotion, trigger, timestamp])
        except Exception as e:
            print("Logging error: {}".format(e))

    def run(self):
        print("RobotAssistant is running. Listening for voice or face input...")
        try:
            while True:
                current_time = time.time()
                if not self.sleeping and (current_time - self.last_interaction_time > 10):
                    self.go_to_sleep()
                    self.sleeping = True
                    print("Entering sleep mode due to inactivity.")
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("Shutting down RobotAssistant.")
        finally:
            try:
                self.asr.unsubscribe("VoiceRecog")
            except Exception:
                pass
            try:
                self.face_detection.unsubscribe("FaceDetect")
            except Exception:
                pass
            try:
                self.sound_loc.unsubscribe("SoundLoc")
            except Exception:
                pass

def main(robot_ip="127.0.0.1", robot_port=9559):
    session = None
    try:
        session = qi.Session()
        session.connect("tcp://{}:{}".format(robot_ip, robot_port))
    except Exception as e:
        print("Cannot connect to Naoqi at {}:{}.\nError: {}".format(robot_ip, robot_port, e))
        sys.exit(1)
    assistant = RobotAssistant(session)
    assistant.run()

if __name__ == "__main__":
    ip = "127.0.0.1"
    port = 9559
    if len(sys.argv) >= 2:
        ip = sys.argv[1]
    if len(sys.argv) >= 3:
        port = int(sys.argv[2])
    main(ip, port)