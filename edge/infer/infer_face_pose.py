import cv2
import mediapipe as mp

mp_face = mp.solutions.face_detection
mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils

face_detector = mp_face.FaceDetection(
    model_selection=0,
    min_detection_confidence=0.3
)

pose_detector = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.3,
    min_tracking_confidence=0.3
)

def get_person_data(image):
    if image is None:
        return 0, [], image

    h, w = image.shape[:2]
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    faces = []

    face_results = face_detector.process(rgb)
    if face_results.detections:
        for det in face_results.detections:
            score = det.score[0]
            box = det.location_data.relative_bounding_box

            x1 = int(box.xmin * w)
            y1 = int(box.ymin * h)
            x2 = int((box.xmin + box.width) * w)
            y2 = int((box.ymin + box.height) * h)

            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w - 1, x2), min(h - 1, y2)

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

            faces.append({
                "conf": float(score),
                "xmin": x1 / w,
                "ymin": y1 / h,
                "width": (x2 - x1) / w,
                "height": (y2 - y1) / h,
            })

    pose_results = pose_detector.process(rgb)
    # Statt:
    # persons_detected = 1 if pose_results.pose_landmarks else 0

    # ✅ Anzahl der Gesichter zählen
    persons_detected = len(faces)

    if pose_results.pose_landmarks:
        mp_draw.draw_landmarks(
            image,
            pose_results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )

    cv2.imwrite("frame_out.jpg", image)
    return persons_detected, faces, image


