import os
import json
from flask import Flask, jsonify, request, Response
from confluent_kafka import Consumer, KafkaException
from prometheus_client import Gauge, generate_latest
from threading import Thread

BOOTSTRAP = os.getenv("BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC = "edge-data"
GROUP_ID = os.getenv("GROUP_ID", "server-group")

app = Flask(__name__)

PERSONS_DETECTED = Gauge(
    'persons_detected',
    'Number of people detected',
    ['device_id']
)

data_store = []

def create_consumer():
    return Consumer({
        "bootstrap.servers": BOOTSTRAP,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    })

def kafka_loop():
    consumer = create_consumer()
    consumer.subscribe([TOPIC])
    print(f"[SERVER] Kafka consumer started, bootstrap={BOOTSTRAP}, group={GROUP_ID}", flush=True)

    while True:
        try:
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                print("[SERVER] Kafka error:", msg.error(), flush=True)
                continue

            payload = json.loads(msg.value().decode("utf-8"))
            data_store.append(payload)

            count = int(payload.get("persons_detected", 0))
            device = payload.get("device_id", "unknown")
            PERSONS_DETECTED.labels(device_id=device).set(count)

            print("[SERVER] Received via Kafka:", payload, flush=True)

        except Exception as e:
            print("[SERVER] Kafka exception:", e, flush=True)

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype="text/plain")

@app.route("/data", methods=["GET"])
def data_endpoint():
    return jsonify(data_store)

if __name__ == "__main__":
    Thread(target=kafka_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, use_reloader=False)
