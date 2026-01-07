import time
import json
import os
import sys
from datetime import datetime
from confluent_kafka import Producer
import threading
import cv2
from infer.infer_face_pose import get_person_data
from flask import Flask, request, jsonify, make_response
import base64
import numpy as np

# ------------------------
# Flask Setup
app = Flask(__name__)
CURRENT_FRAME_PATH = "/tmp/frame.jpg"
DEVICE_ID = os.getenv("DEVICE_ID", "edge-3")
TOPIC = os.getenv("TOPIC", "edge-data")
BOOTSTRAP = os.getenv("BOOTSTRAP_SERVERS", "34.67.127.119:9092")

# ------------------------
# Kafka Producer
producer = None
def delivery_report(err, msg):
    if err is not None:
        print(f"[EDGE] ❌ Delivery failed: {err}", flush=True)
    else:
        print(f"[EDGE] ✅ Delivered to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}", flush=True)

try:
    producer = Producer({"bootstrap.servers": BOOTSTRAP, "linger.ms": 10})
    print(f"[EDGE] Kafka producer initialized ({BOOTSTRAP})", flush=True)
except Exception as e:
    print("⚠️ Kafka disabled:", e, flush=True)

sys.stdout.reconfigure(line_buffering=True)
print("[EDGE] Edge running", flush=True)

# ------------------------
# Globaler Speicher für letzte Inferenz
last_result = {
    "device_id": DEVICE_ID,
    "timestamp": None,
    "persons_detected": 0,
    "faces": []
}

# ------------------------
# Flask /frame POST – nur Frame speichern
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

    cv2.imwrite(CURRENT_FRAME_PATH, image)
    print("[EDGE] wrote /tmp/frame.jpg", flush=True)
    return "ok"

# ------------------------
# Flask /frame_data GET – liefert letzte Bounding Boxes
@app.route("/frame_data", methods=["GET"])
def frame_data():
    global last_result
    response = make_response(jsonify({"faces": last_result["faces"]}))
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

# ------------------------
# Inferenz-Loop – aktualisiert globalen Speicher
def inference_loop():
    global last_result
    while True:
        image = cv2.imread(CURRENT_FRAME_PATH)
        if image is None:
            time.sleep(1)
            continue

        persons_detected, faces, _ = get_person_data(image)

        # Ergebnis in globalem Speicher aktualisieren
        last_result = {
            "device_id": DEVICE_ID,
            "timestamp": datetime.utcnow().isoformat(),
            "persons_detected": persons_detected,
            "faces": faces
        }

        print("🚨 EDGE RUNNING 🚨", last_result, flush=True)
        time.sleep(2)

# ------------------------
# Kafka-Loop – liest globalen Speicher
def kafka_loop():
    global last_result
    while True:
        if producer and last_result["timestamp"] is not None:
            try:
                producer.produce(TOPIC, json.dumps(last_result), callback=delivery_report)
                producer.poll(1)
            except Exception as e:
                print("[EDGE] Kafka produce failed:", e, flush=True)
        time.sleep(5)

# ------------------------
if __name__ == "__main__":
    # Start Inferenz-Loop
    t1 = threading.Thread(target=inference_loop, daemon=True)
    t1.start()

    # Start Kafka-Loop
    t2 = threading.Thread(target=kafka_loop, daemon=True)
    t2.start()

    # Start Flask-App
    app.run(host="0.0.0.0", port=9001)





















