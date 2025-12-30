import time
import json
import os
import sys
from datetime import datetime
from confluent_kafka import Producer
from hw.frame_receiver import start as start_receiver
import threading
import cv2
from infer.infer_face_pose import get_person_data



sys.stdout.reconfigure(line_buffering=True)

BOOTSTRAP = os.getenv("BOOTSTRAP_SERVERS", "34.67.127.119:9092")
TOPIC = os.getenv("TOPIC", "edge-data")
DEVICE_ID = os.getenv("DEVICE_ID", "edge-1")

def delivery_report(err, msg):
    if err is not None:
        print(f"[EDGE] ❌ Delivery failed: {err}", flush=True)
    else:
        print(
            f"[EDGE] ✅ Delivered to {msg.topic()} "
            f"[{msg.partition()}] @ offset {msg.offset()}",
            flush=True,
        )

producer = None
try:
    producer = Producer({
        "bootstrap.servers": BOOTSTRAP,
        "linger.ms": 10,
    })
    print(f"[EDGE] Kafka producer initialized ({BOOTSTRAP})", flush=True)
except Exception as e:
    print("⚠️ Kafka disabled:", e, flush=True)

print("[EDGE] Edge running (DUMMY inference)", flush=True)

def simulate_edge_data():
    while True:
        #persons_detected, faces = 2, 1  # DUMMY – bewusst!
        image = cv2.imread("/tmp/frame.jpg")
        if image is None:
            print("[EDGE] no frame yet", flush=True)
            time.sleep(1)
            continue

        persons_detected, faces, out_img = get_person_data(image)

        payload = {
            "device_id": DEVICE_ID,
            "timestamp": datetime.utcnow().isoformat(),
            "persons_detected": persons_detected,
            "faces": faces,
        }

        print("🚨 EDGE RUNNING 🚨", payload, flush=True)

        if producer:
            producer.produce(
                TOPIC,
                json.dumps(payload),
                callback=delivery_report,
            )
            producer.poll(1)

        time.sleep(5)

if __name__ == "__main__":
    import threading

    t = threading.Thread(target=simulate_edge_data)
    t.start()

    start_receiver()





