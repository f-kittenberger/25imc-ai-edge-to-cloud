import cv2
import mediapipe as mp

mp_face = mp.solutions.face_detection
mp_draw = mp.solutions.drawing_utils

detector = mp_face.FaceDetection(
    model_selection=0,        # 0 = short-range (Webcam)
    min_detection_confidence=0.3
)

def infer(image_path="frame.jpg"):
    image = cv2.imread(image_path)
    if image is None:
        print("No image")
        return

    h, w = image.shape[:2]

    # MediaPipe arbeitet intern in RGB
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = detector.process(rgb)

    if results.detections:
        for det in results.detections:
            score = det.score[0]
            box = det.location_data.relative_bounding_box

            x1 = int(box.xmin * w)
            y1 = int(box.ymin * h)
            x2 = int((box.xmin + box.width) * w)
            y2 = int((box.ymin + box.height) * h)

            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w - 1, x2)
            y2 = min(h - 1, y2)

            label = f"face {score:.2f}"

            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                image,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

            print(f"[MP] face conf={score:.3f} box=({x1},{y1},{x2},{y2})")
    else:
        print("[MP] no face")

    cv2.imwrite("frame_out.jpg", image)
