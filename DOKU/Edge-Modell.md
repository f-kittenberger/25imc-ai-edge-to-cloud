Befehlskette ohne interference:
EDGE DEVICE (Laptop, Minikube mit wenig Speicher)
0. Aufräumen (zwingend)
docker system prune -a -f --volumes
minikube delete
rm -rf ~/.cache/pip

1. Minikube mit reduziertem Speicher starten
minikube start \
  --driver=docker \
  --memory=2048 \
  --cpus=2 \
  --disk-size=10g


Docker-Umgebung setzen:

eval $(minikube docker-env)

2. Edge-Image bauen
docker build -f docker/Docker_file.edge -t edge-producer:latest .

3. Edge-Deployment starten
kubectl apply -f k8s/edge.yaml
kubectl rollout restart deployment edge

4. Edge prüfen
kubectl get pods
kubectl logs -f -l app=edge

VM (Kafka-Server – 34.67.127.119)
0. Aufräumen
docker system prune -a -f --volumes

1. Kafka & Zookeeper starten
docker compose up -d

2. Kafka-Container betreten
docker exec -it kafka-compose_kafka_1 bash

3. Topic prüfen
kafka-topics --bootstrap-server localhost:9092 --list

4. Edge-Daten live sehen
kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic edge-data






Browser / Kamera
        ↓
Flask (Frame Receiver)
        ↓
MediaPipe (Face + Pose)
        ↓
Docker-Container (Edge)
        ↓
Kafka Topic (Events / Metadata)
        ↓
Cloud / Analytics / Dashboard




ai-edge-to-cloud/
edge/
├── __init__.py
├── app_edge.py
├── infer/
│   ├── __init__.py
│   └── infer_face_pose.py
└── hw/
    ├── __init__.py
    └── frame_receiver.py

│
├── k8s/
│   └── edge.yaml
│
├── docker/
│   └── Dockerfile.edge
│
├── requirements/
│   └── edge.txt



Quelle (Browser/Kamera/Skript – egal)
        ↓
frame.jpg   (lokal auf dem Edge-Rechner)
        ↓
Docker-Container
   ├─ liest frame.jpg
   ├─ Inferenz (MediaPipe)
   ├─ schreibt frame_out.jpg
   └─ sendet Kafka

