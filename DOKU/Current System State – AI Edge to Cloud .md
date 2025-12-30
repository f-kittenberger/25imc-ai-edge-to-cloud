Current System State – AI Edge to Cloud (Stable Development Setup)
Overview

The system implements a local edge inference pipeline that captures webcam frames in a browser, performs computer vision inference inside a Kubernetes-managed edge container, and forwards inference results to Kafka, where they are consumed on a remote VM.

This setup is intentionally optimized for development stability and reproducibility, not production exposure.

Architecture (End-to-End Flow)
Browser (Webcam, HTML/JS)
  → HTTP POST /frame (localhost:9001)
    → kubectl port-forward
      → Edge Pod (Minikube, Docker)
        → Frame saved to /tmp/frame.jpg
        → MediaPipe inference (face / pose)
        → Kafka Producer
          → Kafka Broker (VM)
            → Results visible on VM consumer

Key Components
1. Browser (Input Source)

HTML/JavaScript page using getUserMedia

Captures webcam frames at ~1 FPS

Sends frames as Base64 JPEG via:

POST http://localhost:9001/frame

2. Kubernetes (Local Cluster)

Minikube running with Docker driver

Single Deployment: edge

No Service, no NodePort, no Ingress

3. Edge Container

Python-based container

Runs:

Flask HTTP server on port 9001

MediaPipe-based inference (face + pose)

Kafka producer

Writes incoming frames to:

/tmp/frame.jpg

4. Inference Logic

Face detection via MediaPipe FaceDetection

Optional pose detection with visibility checks

Person detection logic:

A person is counted only when a valid face is detected

Outputs structured inference results:

{
  "persons_detected": 1,
  "faces": [...]
}

5. Kafka Integration

Edge container produces events to Kafka

Kafka broker runs on a separate VM

VM consumer confirms receipt of inference results

Kubernetes Configuration (Final, Minimal)
Deployment: k8s/edge.yaml

Single replica

Exposes container port 9001

No Service object

Designed to be accessed via kubectl port-forward

apiVersion: apps/v1
kind: Deployment
metadata:
  name: edge
spec:
  replicas: 1
  selector:
    matchLabels:
      app: edge
  template:
    metadata:
      labels:
        app: edge
    spec:
      containers:
        - name: edge
          image: edge-producer:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 9001
          env:
            - name: BOOTSTRAP_SERVERS
              value: "34.67.127.119:9092"
            - name: TOPIC
              value: "edge-data"

How the System Is Started (Correct Procedure)

Start Minikube (lightweight)

minikube start --driver=docker --cpus=2 --memory=2048


Deploy the edge workload

kubectl apply -f k8s/edge.yaml


Start port-forward (required)

kubectl port-forward deployment/edge 9001:9001


This terminal must remain open.

Open the HTML file in the browser

Camera access granted

Frames start streaming automatically

How to Verify It Is Working
Edge logs (primary indicator)
kubectl logs -f deployment/edge


Expected output:

[EDGE] wrote /tmp/frame.jpg
persons_detected: 1
[EDGE] Delivered to Kafka

Kafka VM

Kafka consumer shows incoming inference events

Confirms end-to-end success