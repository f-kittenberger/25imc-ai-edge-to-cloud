import random
import json
import time
from datetime import datetime
from confluent_kafka import Producer
import sys

sys.stdout.reconfigure(line_buffering=True)

BOOTSTRAP = "34.67.127.119:9092"
TOPIC = "edge-data"

# Optional: Callback to confirm the message was delivered
def delivery_report(err, msg):
    if err is not None:
        print(f"[ERROR] Message delivery failed: {err}")
    else:
        print(f"[SUCCESS] Message delivered to {msg.topic()} [{msg.partition()}]")

producer = Producer({"bootstrap.servers": BOOTSTRAP})
print(f"[EDGE] Kafka producer starting, bootstrap={BOOTSTRAP}")

def generate_simulated_faces(intensity):
    faces_list = []
    num_faces = random.randint(0, intensity)
    
    for _ in range(num_faces):
        width = random.uniform(0.05, 0.3)
        height = random.uniform(0.05, 0.4)
        xmin = random.uniform(0, 1.0 - width)
        ymin = random.uniform(0, 1.0 - height)
        
        face = {
            "conf": random.uniform(0.5, 0.99),
            "xmin": xmin,
            "ymin": ymin,
            "width": width,
            "height": height
        }
        faces_list.append(face)
    
    return faces_list # Return the list itself

def simulate_edge_data():
    while True:
        # Intensity for randomness
        intensity_val = random.randint(0, 10)
        device_id = random.randint(1, 3)
        
        faces_data = generate_simulated_faces(intensity_val)
        
        payload = {
            "device_id": f"edge-simulator-0{device_id}",
            "timestamp": datetime.now().isoformat(),
            "persons_detected": len(faces_data), # Actual count of generated faces
            "faces": faces_data
        }
        
        producer.produce(TOPIC, json.dumps(payload), callback=delivery_report)
        producer.flush() # Forces the message out immediately
        
        print(f"[EDGE] Sent data for simulator-0{device_id} (Detected: {len(faces_data)})")
        print("[EDGE] Sent:", payload)
        time.sleep(30)

if __name__ == "__main__":
    try:
        simulate_edge_data()
    except KeyboardInterrupt:
        print("[EDGE] Stopping simulator...")