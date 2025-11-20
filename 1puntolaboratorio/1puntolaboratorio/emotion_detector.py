import threading
import cv2
import mediapipe as mp
import numpy as np
import time

# ------------------------------
# Semáforo para controlar el acceso al procesamiento
# ------------------------------
process_semaphore = threading.Semaphore(1)

# ------------------------------
# Mutex para proteger los datos compartidos
# ------------------------------
data_mutex = threading.Lock()

# Variable compartida
shared_emotion = "No detectada"

# Inicializar MediaPipe
mp_face = mp.solutions.face_mesh
mp_draw = mp.solutions.drawing_utils


def classify_emotion(landmarks):
    # Muy básico: usa la distancia entre puntos para aproximar emoción.
    # Se puede mejorar si quieres.

    mouth_up = landmarks[13].y
    mouth_down = landmarks[14].y
    eye_left_up = landmarks[159].y
    eye_left_down = landmarks[145].y

    mouth_open = abs(mouth_down - mouth_up)
    eye_open = abs(eye_left_down - eye_left_up)

    if mouth_open > 0.04:
        return "Sorprendido"
    elif eye_open < 0.01:
        return "Enojado"
    else:
        return "Neutral"


def emotion_processing(frame, results):
    global shared_emotion

    # Entrar al semáforo
    with process_semaphore:

        for face_landmarks in results.multi_face_landmarks:
            emotion = classify_emotion(face_landmarks.landmark)

            # Proteger con mutex
            with data_mutex:
                shared_emotion = emotion

        time.sleep(0.02)  # evitar sobrecarga


def emotion_thread(frame, results):
    t = threading.Thread(target=emotion_processing, args=(frame, results))
    t.start()
