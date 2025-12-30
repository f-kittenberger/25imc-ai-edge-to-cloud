from flask import Flask, request
import base64
import cv2
import numpy as np

from infer.infer_face_pose import get_person_data

# OPTIONAL: Kafka nur, wenn vorhanden
try:
    from stream.kafka_producer import send_event
except ImportError:
    send_event = None
    print("[WARN] Kafka disabled (stream.kafka_producer not found)")

app = Flask(__name__)

@app.route("/frame", methods=["POST"])
def frame():
    data = request.data.decode()

    if "," not in data:
        return "invalid data", 400

    try:
        jpg = base64.b64decode(data.split(",", 1)[1])
    except Exception as e:
        print("[EDGE] base64 decode failed:", e, flush=True)
        return "bad image", 400

    npimg = np.frombuffer(jpg, dtype=np.uint8)
    image = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    if image is None:
        print("[EDGE] cv2.imdecode failed", flush=True)
        return "bad jpeg", 400

    cv2.imwrite("/tmp/frame.jpg", image)
    print("[EDGE] wrote /tmp/frame.jpg", flush=True)

    return "ok"


def start():
    app.run(port=9001, host="0.0.0.0")



