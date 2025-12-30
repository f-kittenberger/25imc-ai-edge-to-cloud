import cv2
import mediapipe as mp

# MediaPipe Modules
mp_face = mp.solutions.face_detection
mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils

# Face Detector
face_detector = mp_face.FaceDetection(
    model_selection=0,
    min_detection_confidence=0.3
)

# Pose Detector
pose_detector = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.3,
    min_tracking_confidence=0.3
)

def infer(image_path="frame.jpg"):
    image = cv2.imread(image_path)
    if image is None:
        print("[MP] no image")
        return

    h, w = image.shape[:2]

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # ---------- FACE DETECTION ----------
    face_results = face_detector.process(rgb)
    if face_results.detections:
        for det in face_results.detections:
            score = det.score[0]
            box = det.location_data.relative_bounding_box

            x1 = int(box.xmin * w)
            y1 = int(box.ymin * h)
            x2 = int((box.xmin + box.width) * w)
            y2 = int((box.xmin + box.height) * h)

            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w - 1, x2)
            y2 = min(h - 1, y2)

            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                image,
                f"face {score:.2f}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

            print(f"[FACE] conf={score:.3f} box=({x1},{y1},{x2},{y2})")
    else:
        print("[FACE] none")

    # ---------- POSE DETECTION ----------
    pose_results = pose_detector.process(rgb)
    if pose_results.pose_landmarks:
        mp_draw.draw_landmarks(
            image,
            pose_results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            mp_draw.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=2),
            mp_draw.DrawingSpec(color=(255, 255, 0), thickness=2)
        )
        print("[POSE] person detected")
    else:
        print("[POSE] none")

    cv2.imwrite("frame_out.jpg", image)
