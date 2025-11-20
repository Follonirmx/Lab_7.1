import cv2
import mediapipe as mp
from threading import Thread, Lock, Semaphore

# Inicializar MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh

class EmotionDetector:
    def __init__(self):
        self.face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.lock = Lock()          # Mutex
        self.semaphore = Semaphore(1)  # Semáforo
        self.emotion = "Desconocida"

    def detectar_emocion(self, landmarks):
        """
        Detecta Felicidad, Enojo o Tristeza
        usando labios, ojos y cejas
        """

        # --- Ojos ---
        ojo_izq = landmarks[159].y - landmarks[145].y
        ojo_der = landmarks[386].y - landmarks[374].y

        # --- Boca ---
        boca_sup = landmarks[13]
        boca_inf = landmarks[14]
        boca_dist = boca_inf.y - boca_sup.y

        # --- Cejas (inclinación de la ceja izquierda) ---
        ceja_izq_sup = landmarks[105]
        ceja_izq_inf = landmarks[66]
        ceja_inclinacion = ceja_izq_inf.y - ceja_izq_sup.y

        # --- Lógica simple ---
        # FELIZ: boca abierta o leve sonrisa (ceja normal)
        if boca_dist > 0.025 and ceja_inclinacion > 0:
            return "😊 Feliz"

        # ENOJADO: ojos cerrados y ceja fruncida
        if ojo_izq < 0.004 and ojo_der < 0.004 and ceja_inclinacion < -0.003:
            return "😡 Enojado"

        # TRISTE: boca cerrada y leve caída de cejas
        return "😢 Triste"

    def detect(self, frame):
        with self.lock:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb)
            if results.multi_face_landmarks:
                face = results.multi_face_landmarks[0]
                self.emotion = self.detectar_emocion(face.landmark)
            else:
                self.emotion = "No detectada"
        return self.emotion

def camera_thread(detector):
    detector.semaphore.acquire()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("No se pudo abrir la cámara")
        detector.semaphore.release()
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        emotion = detector.detect(frame)

        cv2.putText(frame, f"Emoción: {emotion}", (50,50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        cv2.imshow("Emotion Detector", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC para salir
            break

    cap.release()
    cv2.destroyAllWindows()
    detector.semaphore.release()

if __name__ == "__main__":
    detector = EmotionDetector()
    t1 = Thread(target=camera_thread, args=(detector,))
    t1.start()
    t1.join()
