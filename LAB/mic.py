#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import time
import threading
import socket
import speech_recognition as sr
import cv2
import numpy as np
import pyaudio
import pickle
import struct

# Configuration
PC_IP = "192.168.1.156"
PC_PORT = 51599

# ---------------------------------------------------------------------------
# --- PC Memory simulating ALMemory events ---
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

class PCMemory:
    def __init__(self):
        self.subscribers = {}
    def subscriber(self, event_name):
        if event_name not in self.subscribers:
            self.subscribers[event_name] = Subscriber()
        return self.subscribers[event_name]
    def emit(self, event_name, value):
        if event_name in self.subscribers:
            self.subscribers[event_name].signal.emit(value)

# ---------------------------------------------------------------------------
# --- PC Speech Recognition ---
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
        self.vocabulary = vocab

    def subscribe(self, subscriber_name):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._listen_loop)
            self.thread.setDaemon(True)
            self.thread.start()

    def unsubscribe(self, subscriber_name):
        self.running = False

    def _listen_loop(self):
        english_map = {
            "headache": "You mentioned a headache. Maybe you should see internal medicine.",
            "pain": "You are in pain. Internal medicine might help.",
            "hurt": "You said hurt. Please describe the pain more.",
            "unwell": "Feeling unwell? Let's get you some help.",
            "sick": "You're sick. Please consider seeing a doctor.",
            "internal medicine": "Internal medicine department is recommended.",
            "stomach": "Stomach issues? Gastroenterology may help.",
            "abdomen": "Abdomen issues detected. Consider a medical checkup.",
            "belly": "Belly problems? Let's check gastroenterology.",
            "stomach ache": "You said stomach ache. We'll look into that.",
            "gastroenterology": "Directing to gastroenterology department.",
            "toilet": "You are looking for a restroom.",
            "bathroom": "Bathroom request received.",
            "restroom": "Restroom? It's just down the hall.",
            "washroom": "Washroom, noted.",
            "surgery": "Surgery department will handle this.",
            "trauma": "Trauma detected. Surgery is appropriate.",
            "fracture": "Fracture? We'll call surgery.",
            "broken": "Broken bone? Surgery will assist.",
            "injury": "Injury detected. Routing to proper care.",
            "ear": "Ear problem detected. Consider ENT.",
            "nose": "Nose-related issue. ENT can help.",
            "throat": "Throat pain noted. ENT recommended.",
            "earache": "Earache complaint heard.",
            "sore throat": "Sore throat. Let's consult ENT.",
            "ent": "ENT department selected.",
            "emergency": "Emergency detected! Preparing help.",
            "help": "Help is on the way.",
            "urgent": "Urgent case. Responding fast.",
            "laboratory": "Sending you to the laboratory.",
            "lab": "Lab work requested.",
            "test": "Test ordered. Going to lab.",
            "blood test": "Blood test? Sending to lab."
        }

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
                    if word.lower() in english_map:
                        print("\033[92m" + english_map[word.lower()] + "\033[0m")
                self.memory.emit("WordRecognized", value)
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                print("PCSpeechRecognition error:", e)
            time.sleep(0.1)

# ---------------------------------------------------------------------------
# --- PC Face Detection ---
class PCFaceDetection:
    def __init__(self, memory):
        self.memory = memory
        self.running = False
        self.thread = None
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    def subscribe(self, subscriber_name, param1=None, param2=None):
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
# --- PCCameraReceiver ---
class PCCameraReceiver:
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
        payload_size = struct.calcsize("!L")
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
                msg_size = struct.unpack("!L", packed_msg_size)[0]
                while len(data) < msg_size:
                    data += conn.recv(4096)
                frame_data = data[:msg_size]
                data = data[msg_size:]
                buffer = pickle.loads(frame_data)
                frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
                if frame is None:
                    continue
                self.memory.emit("CameraFrameReceived", frame)
                cv2.imshow("PCCameraReceiver - Received Frame", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except Exception as e:
                print("PCCameraReceiver error:", e)
                break
        conn.close()
        self.socket.close()
        cv2.destroyAllWindows()

# ---------------------------------------------------------------------------
# --- Debug entry point ---
if __name__ == "__main__":
    memory = PCMemory()
    asr = PCSpeechRecognition(memory)
    asr.setLanguage("en-US")
    asr.subscribe("TestSpeech")
    while True:
        time.sleep(1)
