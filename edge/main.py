import time
import json
import random
import os
import sys
from datetime import datetime
from confluent_kafka import Producer

# Sofortiges Flushen von Logs
sys.stdout.reconfigure(line_buffering=True)

# Environment
BOOTSTRAP = os.getenv("BOOTSTRAP_SERVERS", "kafka:9092")
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
# Kafka Producer initialisieren (deine Struktur bleibt!)
# ------------------------------------------------------------
producer = None
try:
    producer = Producer({
        "bootstrap.servers": BOOTSTRAP,
        "linger.ms": 10,
    })
    print(f"[EDGE-MOCK] Kafka producer initialized ({BOOTSTRAP})", flush=True)
except Exception as e:
    print("⚠️ Kafka disabled:", e, flush=True)

print("[EDGE-MOCK] HTTP-like simulation, Kafka output", flush=True)

# ------------------------------------------------------------
# Edge-Simulation
# ------------------------------------------------------------
def simulate_edge_data():
    while True:
        count = random.randint(0, 25)

        payload = {
            "device_id": DEVICE_ID,
            "timestamp": datetime.utcnow().isoformat(),
            "persons_detected": count,
        }

        # Loggen was wir senden wollen
        print("🚨🚨🚨 EDGE MOCK V2 RUNNING 🚨🚨🚨", payload, flush=True)

        # Nur senden, wenn Kafka verfügbar ist
        if producer:
            try:
                producer.produce(
                    TOPIC,
                    json.dumps(payload),
                    callback=delivery_report,
                )
                # Wichtig für Delivery Reports
                producer.poll(1)
            except Exception as e:
                print("[EDGE] ❌ Produce exception:", e, flush=True)

        time.sleep(5)

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
if __name__ == "__main__":
    simulate_edge_data()
