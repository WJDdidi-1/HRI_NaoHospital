#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import qi
#from naoqi import ALProxy
import time
import datetime
import csv
import os
import sys
import threading
import socket  # Import the socket module

# PC side imports
import speech_recognition as sr
import cv2
import numpy as np
import pyaudio
import pickle
import struct
from Navigation import run_navigation
from Path_Calculation import dijkstra
from GUI import get_updated_maze
from Motion import move_robot_along_path

# Configuration
PC_IP = "192.168.1.156"  # IP address of your PC
PC_PORT = 51599         # Port for communication between PC and NAO

start = (7, 6)

departments = {
    1: ("internal", (0, 6)),
    2: ("gastro", (2, 1)),
    3: ("restroom", (2, 4)),
    4: ("surgery", (4, 4)),
    5: ("ent", (6, 4)),
    6: ("emergency", (7, 6)),
    7: ("lab", (5, 6))
}

def get_department_coord(dept_number):
    if dept_number in departments:
        return departments[dept_number][1]
    else:
        raise ValueError("Invalid department number. Please enter a number from 1 to 7.")

# ---------------------------------------------------------------------------
# --- PC Sound Localization  ---
# Use PyAudio to compute the energy of audio input from the PC microphone
class PCSoundLocalization:
    def __init__(self, memory, pc_ip, pc_port):
        self.memory = memory
        self.running = False
        self.thread = None
        self.energy_computation = False
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.audio_interface = pyaudio.PyAudio()
        self.pc_ip = pc_ip
        self.pc_port = pc_port
        self.socket = None

    def setParameter(self, param, value):
        if param == "EnergyComputation":
            self.energy_computation = value

    def subscribe(self, subscriber_name):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._sound_loop)
            self.thread.setDaemon(True)
            self.thread.start()
            self._connect_to_nao()

    def unsubscribe(self, subscriber_name):
        self.running = False
        if self.socket:
            self.socket.close()

    def _connect_to_nao(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.pc_ip, self.pc_port))
            print("Connected to NAO for sound data.")
        except Exception as e:
            print("Error connecting to NAO: {}".format(e))
            self.socket = None

    def _sound_loop(self):
        stream = self.audio_interface.open(format=self.format,
                                             channels=self.channels,
                                             rate=self.rate,
                                             input=True,
                                             frames_per_buffer=self.chunk,
                                             input_device_index=1)
        while self.running:
            try:
                data = stream.read(self.chunk, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                energy = np.linalg.norm(audio_data)  # Simple energy calculation
                # Send energy to NAO
                if self.socket:
                    try:
                        self.socket.send(str(energy).encode('utf-8'))  # Send as string
                    except Exception as e:
                        print("Error sending energy to NAO: {}".format(e))
                        self._connect_to_nao()  # Attempt to reconnect
                else:
                    self._connect_to_nao()

                # Construct a data structure similar to NAO's event:
                # value[1][3] is energy
                self.memory.emit("ALSoundLocalization/SoundLocated", [None, [None, None, None, energy]])
            except Exception as e:
                print("PCSoundLocalization error:", e)
            time.sleep(0.1)
        stream.stop_stream()
        stream.close()
        self.audio_interface.terminate()

# ---------------------------------------------------------------------------
# --- Hybrid Session ---
# A hybrid session that returns real NAO services and PC simulated services
class HybridSession:
    def __init__(self, real_session):
        self.real_session = real_session
        # Create a PC-side ALMemory
        self.pc_memory = PCMemory()
        # Create PC services and pass in the memory object
        self.pc_asr = PCSpeechRecognition(self.pc_memory)
        self.pc_face = PCFaceDetection(self.pc_memory)
        self.pc_sound = PCSoundLocalization(self.pc_memory, PC_IP, PC_PORT)  # Pass PC IP and Port
        self.nao_sound_proxy = NAOSoundProxy(PC_IP, PC_PORT)  # Create the proxy

    def service(self, service_name):
        if service_name == "ALSpeechRecognition":
            return self.pc_asr
        elif service_name == "ALFaceDetection":
            return self.pc_face
        elif service_name == "ALSoundLocalization":
            return self.nao_sound_proxy  # Return the proxy
        elif service_name == "ALMemory":
            return self.pc_memory
        else:
            # For other services, directly return from the real session
            return self.real_session.service(service_name)

# ---------------------------------------------------------------------------
# --- NAO Sound Proxy ---
# A proxy class to receive sound data from the PC
class NAOSoundProxy:
    def __init__(self, pc_ip, pc_port):
        self.pc_ip = pc_ip
        self.pc_port = pc_port
        self.socket = None
        self.thread = None
        self.running = False
        self.last_energy = 0.0
        print(pc_port, pc_ip)

    def subscribe(self, name):
        if not self.running:
            self.running = True
            self._start_listening()
            if self.socket:
                self.thread = threading.Thread(target=self._receive_energy)
                self.thread.setDaemon(True)
                self.thread.start()
            else:
                print("Socket initialization failed. Receive thread not started.")

    def unsubscribe(self, name):
        self.running = False
        if self.socket:
            self.socket.close()

    def _start_listening(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind(('', self.pc_port))  # Listen on all interfaces
            self.socket.listen(1)
            print("NAO listening for sound data on port {}".format(self.pc_port))
        except Exception as e:
            print("Error setting up socket on NAO: {}".format(e))
            self.socket = None

    def _receive_energy(self):
        if not self.socket:
            print("Socket not initialized. Cannot receive energy.")
            return

        try:
            conn, addr = self.socket.accept()
            print('Connected by', addr)
            while self.running:
                data = conn.recv(1024)
                if not data:
                    break
                try:
                    self.last_energy = float(data.decode('utf-8'))
                except ValueError:
                    print("Received invalid data: {}".format(data))
                time.sleep(0.01)  # Small delay
            conn.close()
        except Exception as e:
            print("Error receiving energy: {}".format(e))
        finally:
            if self.socket:
                self.socket.close()
            self.running = False

    def setParameter(self, param, value):
        # This method is required by the interface, but we don't use it
        pass

    def get_energy(self):
        return self.last_energy

# ---------------------------------------------------------------------------
# --- PCCameraReceiver ---
class PCCameraReceiver(object):
    def __init__(self, memory, port=8000):
        self.memory = memory
        self.port = port
        self.running = False
        self.thread = None
        self.socket = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._receive_loop)
            self.thread.setDaemon(True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()

    def _receive_loop(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('', self.port))
        self.socket.listen(1)
        print("PCCameraReceiver: Listening on port {}".format(self.port))
        conn, addr = self.socket.accept()
        print("PCCameraReceiver: Connected by", addr)
        data = ""
        payload_size = struct.calcsize("L")
        while self.running:
            try:
                while len(data) < payload_size:
                    packet = conn.recv(4096)
                    if not packet:
                        break
                    data += packet
                if not data:
                    break
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("L", packed_msg_size)[0]
                while len(data) < msg_size:
                    data += conn.recv(4096)
                frame_data = data[:msg_size]
                data = data[msg_size:]
                buffer = pickle.loads(frame_data)
                frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
                if frame is None:
                    continue
                # 通过 ALMemory 发送图像数据
                self.memory.emit("CameraFrameReceived", frame)
                # 显示画面
                print("<<<<，，，，，《《《>>>>")
                cv2.imshow("PCCameraReceiver - Received Frame", frame)
                # 调用 cv2.waitKey 定期刷新窗口
                cv2.waitKey(1)
                # 如检测到 'q' 键，则退出
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except Exception as e:
                print("PCCameraReceiver error:", e)
                break
        conn.close()
        self.socket.close()
        cv2.destroyAllWindows()
        print("Frame received with shape:", frame.shape)

# ---------------------------------------------------------------------------
# --- Implementation of event mechanism ---
class Signal:
    def __init__(self):
        self._callbacks = []
    def connect(self, callback):
        self._callbacks.append(callback)
    def emit(self, value):
        for cb in self._callbacks:
            try:
                cb(value)
            except Exception as e:
                print("Error in callback:", e)

class Subscriber:
    def __init__(self):
        self.signal = Signal()

# --- PC Memory simulating ALMemory events ---
class PCMemory:
    def __init__(self):
        self.subscribers = {}  # event_name -> Subscriber
    def subscriber(self, event_name):
        if event_name not in self.subscribers:
            self.subscribers[event_name] = Subscriber()
        return self.subscribers[event_name]
    def emit(self, event_name, value):
        if event_name in self.subscribers:
            self.subscribers[event_name].signal.emit(value)

# ---------------------------------------------------------------------------
# --- PC Speech Recognition  ---
# Use the speech_recognition library to listen from the PC microphone and recognize speech
class PCSpeechRecognition:
    def __init__(self, memory):
        self.memory = memory
        self.language = "English"
        self.vocabulary = []
        self.running = False
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.thread = None

    def setLanguage(self, language):
        self.language = language

    def setVocabulary(self, vocab, word_spotting):
        self.vocabulary = vocab  # Could be used to limit recognized content later

    def subscribe(self, subscriber_name):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._listen_loop)
            self.thread.setDaemon(True)
            self.thread.start()

    def unsubscribe(self, subscriber_name):
        self.running = False

    def _listen_loop(self):
        while self.running:
            try:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source)
                    print("Listening from PC microphone...")
                    audio = self.recognizer.listen(source, timeout=5)
                try:
                    recognized_text = self.recognizer.recognize_sphinx(audio, language=self.language)
                except Exception:
                    recognized_text = self.recognizer.recognize_google(audio, language=self.language)
                print("PC Speech recognized:", recognized_text)
                words = recognized_text.split()
                value = []
                for word in words:
                    value.append(word)
                    value.append(1.0)
                self.memory.emit("WordRecognized", value)
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                print("PCSpeechRecognition error:", e)
            time.sleep(0.1)

# ---------------------------------------------------------------------------
# --- PC Face Detection  ---
# Use OpenCV to capture video frames from the PC camera and detect faces
class PCFaceDetection:
    def __init__(self, memory):
        self.memory = memory
        self.running = False
        self.thread = None
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    def subscribe(self, subscriber_name, param1, param2):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._detection_loop)
            self.thread.setDaemon(True)
            self.thread.start()

    def unsubscribe(self, subscriber_name):
        self.running = False

    def _detection_loop(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Cannot open PC camera")
            return
        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            if len(faces) > 0:
                self.memory.emit("FaceDetected", [None, [faces[0].tolist()]])
                time.sleep(1)
            time.sleep(0.1)
        cap.release()

# ---------------------------------------------------------------------------
# --- Original RobotAssistant code ---
class RobotAssistant(object):
    destinations = {
        "internal": "the internal medicine department",
        "gastro": "the gastroenterology department",
        "restroom": "the restroom",
        "surgery": "the surgery department",
        "ent": "the ent department",
        "emergency": "the emergency department",
        "lab": "the laboratory"
    }
    destinations1 = {
        1: "the internal medicine department",
        2: "the gastroenterology department",
        3: "the restroom",
        4: "the surgery department",
        5: "the ent department",
        6: "the emergency department",
        7: "the laboratory"
    }

    category_map = {
        "the internal medicine department": 1,
        "the gastroenterology department": 2,
        "the restroom": 3,
        "the surgery department": 4,
        "the ent department": 5,
        "the emergency department": 6,
        "the laboratory": 7
    }
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

        try:
            self.asr.setLanguage("English")
        except Exception as e:
            print("Failed to set ASR language: {}".format(e))
        try:
            self.tts.setLanguage("English")
        except Exception as e:
            print("Failed to set TTS language: {}".format(e))

        self.path = []

        vocab = [
            "headache", "pain", "hurt", "unwell", "sick", "internal medicine",
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
            self.asr.subscribe("VoiceRecog")
            word_subscriber = self.memory.subscriber("WordRecognized")
            word_subscriber.signal.connect(self.on_word_recognized)

            self.face_detection.subscribe("FaceDetect", 500, 0.0)
            face_subscriber = self.memory.subscriber("FaceDetected")
            face_subscriber.signal.connect(self.on_face_detected)

            self.sound_loc.setParameter("EnergyComputation", True)
            self.sound_loc.subscribe("SoundLoc")
        except Exception as e:
            print("Failed to subscribe to one of the events: {}".format(e))
            raise

        try:
            self.tts.setParameter("speed", 90)
        except Exception:
            pass

        self.log_file = "interaction_log.csv"
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode='w') as f:
                writer = csv.writer(f)
                writer.writerow(["Emotion", "Trigger", "Timestamp"])

    def classify_destination(self, recognized_words, full_text):
        dest_category = None
        dest_name = None

        english_map = {
            "headache": "internal", "pain": "internal", "hurt": "internal", "hurts": "internal", "unwell": "internal", "sick": "internal", "internal medicine": "internal",
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
            dest_name = self.destinations[dest_category]
        return dest_name

    def classify_emotion(self, recognized_text, energy):
        text = recognized_text.lower() if recognized_text else ""
        happy_words = ["thank", "thanks", "thank you", "great"]
        angry_words = ["emergency", "help", "urgent", "angry"]
        sad_words = ["headache", "pain", "unwell", "sick", "hurt"]

        if any(word in text for word in happy_words):
            return "happy"
        elif any(word in text for word in angry_words):
            return "angry"
        elif any(word in text for word in sad_words):
            return "sad"

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
        energy = self.sound_loc.get_energy()
        emotion = self.classify_emotion(text_combined, energy)
        self.log_interaction(emotion, "voice")

        if destination:
            self.tts.say("Please follow me, I'll take you to {}.".format(destination))
            try:
                self.path = Navi(destination, maze)

            except Exception as e:
                print("Navigating to {} (simulated).".format(destination))
        else:
            self.tts.say("I'm sorry, I didn't catch that. Could you please repeat?")

    def on_face_detected(self, value):
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
        pass

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
            with open(self.log_file, mode='a') as f:
                writer = csv.writer(f)
                writer.writerow([emotion, trigger, timestamp])
        except Exception as e:
            print("Logging error: {}".format(e))

    def run(self):
        print("RobotAssistant is running. Listening for voice or face input...")
        try:
            while True:
                # 定期调用 cv2.waitKey 来刷新 OpenCV 窗口
                cv2.waitKey(10)
                current_time = time.time()
                if not self.sleeping and (current_time - self.last_interaction_time > 10):
                    #self.go_to_sleep()
                    #self.sleeping = True
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


def Navi(destination, maze):
    global start
    print("Navigating to {}...".format(destination))

    category_id = RobotAssistant.category_map.get(destination.lower())
    print("id", category_id)
    if category_id is None:
        print("Invalid destination keyword:", destination)
        return

    destination_name = RobotAssistant.destinations1[category_id]
    print("Target department is:", destination_name)
    print("the id is:", category_id)

    end = get_department_coord(category_id)

    print(type(start), type(end))

    import threading
    import time

    distance, path = dijkstra(maze, start, end)
    #path, distance = ([(7, 6), (6, 6)], 15)

    t1 = threading.Thread(target = run_navigation(maze, start, end))
    t1.start()

    print("Navigation complete. Distance:", distance, path)

    t2 = threading.Thread(target = move_robot_along_path(path))
    t2.start()

    t1.join()
    t2.join()

    start = end

    #return path


# ---------------------------------------------------------------------------
# --- Main function ---
maze = get_updated_maze()
def main(robot_ip="192.168.1.35", robot_port=9559):

    real_session = None
    try:
        real_session = qi.Session()
        real_session.connect("tcp://{}:{}".format(robot_ip, robot_port))
    except Exception as e:
        print("Cannot connect to Naoqi at {}:{}.\nError: {}".format(robot_ip, robot_port, e))
        sys.exit(1)
    # Create a hybrid session
    hybrid_session = HybridSession(real_session)

    # 启动摄像头接收服务（后台线程）
    camera_receiver = PCCameraReceiver(hybrid_session.pc_memory, port=8000)
    camera_receiver.start()

    assistant = RobotAssistant(hybrid_session)
    assistant.run()

if __name__ == "__main__":
    ip = "192.168.1.35"
    port = 9559
    if len(sys.argv) >= 2:
        ip = sys.argv[1]
    if len(sys.argv) >= 3:
        port = int(sys.argv[2])
    main(ip, port)