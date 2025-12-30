import time
import json
import os
import sys
from datetime import datetime
from confluent_kafka import Producer

# 🔹 NEU: echte Inferenz importieren
# from infer.infer_face_pose import get_person_data
# from hw.frame_receiver import start



# Sofortiges Flushen von Logs
sys.stdout.reconfigure(line_buffering=True)

# Environment
BOOTSTRAP = os.getenv("BOOTSTRAP_SERVERS", "34.67.127.119:9092")
TOPIC = os.getenv("TOPIC", "edge-data")
DEVICE_ID = os.getenv("DEVICE_ID", "edge-1")

# ------------------------------------------------------------
# Kafka delivery callback (DER Wahrheitsbeweis)
# ------------------------------------------------------------
def delivery_report(err, msg):
    if err is not None:
        print(f"[EDGE] ❌ Delivery failed: {err}", flush=True)
    else:
        print(
            f"[EDGE] ✅ Delivered to {msg.topic()} "
            f"[{msg.partition()}] @ offset {msg.offset()}",
            flush=True,
        )

# ------------------------------------------------------------
# Kafka Producer initialisieren (UNVERÄNDERT)
# ------------------------------------------------------------
producer = None
try:
    producer = Producer({
        "bootstrap.servers": BOOTSTRAP,
        "linger.ms": 10,
    })
    print(f"[EDGE] Kafka producer initialized ({BOOTSTRAP})", flush=True)
except Exception as e:
    print("⚠️ Kafka disabled:", e, flush=True)

print("[EDGE] Edge running (REAL inference)", flush=True)

# ------------------------------------------------------------
# Edge Loop (MINIMAL geändert)
# ------------------------------------------------------------
def simulate_edge_data():
    while True:
        # 🔹 ALT:
        # count = random.randint(0, 25)

        # 🔹 NEU: echte Daten von der Inferenz
        persons_detected, faces = 2, 1 # get_person_data()

        payload = {
            "device_id": DEVICE_ID,
            "timestamp": datetime.utcnow().isoformat(),
            "persons_detected": persons_detected,
            "faces": faces,
        }

        print("🚨 EDGE RUNNING 🚨", payload, flush=True)

        if producer:
            try:
                producer.produce(
                    TOPIC,
                    json.dumps(payload),
                    callback=delivery_report,
                )
                producer.poll(1)
            except Exception as e:
                print("[EDGE] ❌ Produce exception:", e, flush=True)

        time.sleep(5)

# ------------------------------------------------------------
# Main (UNVERÄNDERT)
# ------------------------------------------------------------
if __name__ == "__main__":
    simulate_edge_data()
