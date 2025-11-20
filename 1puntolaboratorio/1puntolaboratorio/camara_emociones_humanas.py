import cv2
import mediapipe as mp

# Inicializar MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh

# Función simple para clasificar emociones (muy básica)
def detectar_emocion(landmarks):
    # Distancias verticales entre puntos clave
    ojo_izq = landmarks[159].y - landmarks[145].y
    ojo_der = landmarks[386].y - landmarks[374].y
    boca = landmarks[13].y - landmarks[14].y

    # Regla simple para clasificar
    if boca < -0.01:
        return "😊 Feliz"
    elif ojo_izq < 0.002 and ojo_der < 0.002:
        return "😡 Enojado"
    else:
        return "😢 Triste"

# Abrir cámara
cap = cv2.VideoCapture(0)

with mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as face_mesh:

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if results.multi_face_landmarks:
            face = results.multi_face_landmarks[0]
            h, w, _ = frame.shape

            emocion = detectar_emocion(face.landmark)

            cv2.putText(
                frame, f"Emocion: {emocion}",
                (30, 50), cv2.FONT_HERSHEY_SIMPLEX,
                1, (255, 255, 255), 2
            )

        cv2.imshow("Detector de emociones", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC para salir
            break

cap.release()
cv2.destroyAllWindows()
