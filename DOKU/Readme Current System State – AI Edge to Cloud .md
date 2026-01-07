
# Problem Definition & Scope

Modern AI systems increasingly rely on edge-based inference to reduce latency,
bandwidth usage, and unnecessary cloud compute. At the same time, cloud-side
processing is required for aggregation, monitoring, and sustainability-aware
decision making.

This project explores a minimal but realistic Edge-to-Cloud AI pipeline with:
- Local inference at the edge
- Event-based decoupling via Kafka
- Cloud-side consumption and monitoring
- A foundation for carbon-aware behavior

Scope:
- Development and architectural validation
- Not intended as a production-ready deployment
- Security, authentication, and autoscaling are explicitly out of scope


# Why Edge + Cloud?

Edge inference reduces:
- Latency for real-time perception
- Raw video data transfer
- Continuous cloud compute usage

Cloud components are retained for:
- Asynchronous event processing
- Persistence and aggregation
- Observability and sustainability metrics


# Architectural Overview

The system follows an event-driven edge-to-cloud architecture.
Compute-intensive perception is executed at the edge, while aggregation,
monitoring, and future sustainability-aware logic are placed in the cloud.

Communication between edge and cloud is strictly asynchronous and decoupled.
The architecture favors simplicity, debuggability, and reproducibility over
production-grade exposure or automation.



# Current System State – AI Edge to Cloud (Stable Development Setup)

## Overview

The system implements a local edge inference pipeline that captures webcam frames in a browser, performs computer vision inference inside a Kubernetes-managed edge container, 
and forwards inference results to Kafka, where they are consumed on a remote VM.

This setup is intentionally optimized for development stability and reproducibility, not production exposure.

Kubernetes is deliberately used in a reduced and controlled manner to ensure deterministic behavior and simplified debugging during development.

---

## Architecture (End-to-End Flow)

Browser (Webcam, HTML/JS)  
→ HTTP POST /frame (localhost:9001)  
→ kubectl port-forward  
→ Edge Pod (Minikube, Docker)  
→ Frame saved to /tmp/frame.jpg  
→ MediaPipe inference (face / pose) 
→ HTTP GET /Bounding Boxes 
→ Kafka Producer  
→ Kafka Broker (VM)  
→ Results visible on VM consumer  

No Kubernetes Service, Ingress, or cluster-level routing abstraction is involved in this request path.  
All network traffic is explicitly routed via `kubectl port-forward`.

---

## Key Components

### 1. Browser (Input Source)

HTML/JavaScript page using getUserMedia  

Captures webcam frames at ~1 FPS  

Sends frames as Base64 JPEG via:  

POST http://localhost:9001/frame  

The browser communicates exclusively with a local endpoint and has no direct awareness of Kubernetes networking or cluster internals.

---

### 2. Kubernetes (Local Cluster)

Minikube running with Docker driver  

Single Deployment: edge  

No Service, no NodePort, no Ingress  

The absence of Kubernetes Services and Ingress is intentional and reflects a development-only baseline.  
Kubernetes is used solely for container lifecycle management (start, restart, isolation), not as a platform networking layer.

---

### 3. Edge Container

Python-based container  

Runs:  

Flask HTTP server on port 9001  

MediaPipe-based inference (face + pose)  

Kafka producer  

Writes incoming frames to:  

/tmp/frame.jpg  

The file `/tmp/frame.jpg` exists only inside the container filesystem and is ephemeral.  
It is removed automatically on container or pod restart, which is expected and desired behavior for this setup.

---

### 4. Inference Logic

Face detection via MediaPipe FaceDetection  

Optional pose detection with visibility checks  

Person detection logic:  

A person is counted only when a valid face is detected  

Outputs structured inference results:

```json
{
  "persons_detected": 1,
  "faces": [...]
}
```

The edge component is intentionally stateless; frames are processed and discarded immediately after inference.

---

### 5. Kafka Integration

Edge container produces events to Kafka  

Kafka broker runs on a separate VM  

VM consumer confirms receipt of inference results  

Kafka acts as the sole persistence and decoupling layer between edge inference and cloud-side consumption.

---

## Kubernetes Configuration (Final, Minimal)

Deployment: k8s/edge.yaml  

Single replica  

Exposes container port 9001  

No Service object  

Designed to be accessed via kubectl port-forward  

This configuration is intentionally frozen to serve as a stable development reference.  
Any future changes (scaling, exposure, persistence) should be introduced explicitly and in isolation.





        ┌───────────────┐
        │ Browser 1     │
        │ (Laptop)      │
        │ camera.html   │
        └───────┬───────┘
                │ HTTP POST /frame
                ▼
┌───────────────────────────────┐
│ Edge Container (Minikube)     │
│ - Flask API                   │
│ - MediaPipe Inference         │
│ - Kafka Producer              │
└───────────────┬───────────────┘
                │ Kafka Event
                ▼
┌───────────────────────────────┐
│ Kafka Broker (VM, Docker)     │
│ Topic: edge-data              │
└───────────────┬───────────────┘
                │ Kafka Consume
                ▼
┌───────────────────────────────┐
│ Server Container (VM)         │
│ - Kafka Consumer              │
│ - Flask REST API              │
│ - Prometheus Metrics          │
└───────────────┬───────────────┘
                │
        ┌───────▼────────┐
        │ Browser 2      │
        │ /data          │
        │ Grafana UI     │
        └────────────────┘






ai-edge-to-cloud/
├── .git/
├── .github/
│   └── workflows/
│       └── deploy.yml
├── ai-edge-venv/
├── docker/
│   └── Dockerfile.edge
├── docs/
│   ├── adr/
│   │   ├── 001-kafka.md
│   │   ├── 002-kubernetes.md
│   │   └── ... 
│   └── uml/
│       ├── component-diagram.puml
│       ├── deployment-diagram.puml
│       ├── sequence-edge-kafka-server.puml
│       └── ....
├── DOKU/
├── edge/
│   ├── __init__.py
│   ├── app_edge.py
│   ├── infer/
│   │   ├── __init__.py
│   │   └── infer_face_pose.py
│   └── hw/
│       ├── __init__.py
│       └── frame_receiver.py
├── grafana/
├── html/
│   └── camera.html
├── k8s/
│   ├── edge.yaml
│   ├── server.yaml
│   ├── grafana.yaml
│   └── prometheus.yaml
├── kafka-compose/
│   └─── docker-compose.yaml
├── requirements/
│   └── edge.txt
├── server/
│   ├── __init__.py
│   └── main.py
├── .dummy
├── .gitignore
├── minikube_latest_amd64.deb
└── README.md




## CI/CD (Development-Oriented)

- CI/CD pipeline for development and architectural validation only
- Triggered on feature branch push or manually (`workflow_dispatch`)
- Uses a **self-hosted GitHub runner** installed on the development machine for local Minikube tests
- Runs in two stages:

  1. **Build & Test (GitHub Cloud)**  
     - Checkout code, Python syntax checks, optional unit tests  
     - Build deterministic Docker images for Edge and Server  
     - No deployment to cluster  

  2. **Smoke Test & Local Deployment (Self-Hosted Runner)**  
     - Runs on the self-hosted runner  
     - load Docker images into Minikube  
     - Deploy Edge pod, test `/frame` endpoint  
     - No automatic production rollout  
     - Local validation only  

- Sustainability-aware deployment planned but not yet implemented






## concrete run:

### enviroment:

Python 3.12.3 + venv + Mediapipe 0.10.14
source ai-edge-venv/bin/activate

### camaera start

file://wsl.localhost/Ubuntu/home/micha/ai-edge-to-cloud/html/camera.html

\\wsl.localhost\Ubuntu\home\micha\ai-edge-to-cloud\html


### Docker
run Docker on windows with enable WSL2


### EDGE DEVICE

0. clean up 
docker system prune -a -f --volumes
minikube delete
rm -rf ~/.cache/pip

source ai-edge-venv/bin/activate


1. Minikube 

with reduced memory:
minikube start \
  --driver=docker \
  --memory=2048 \
  --cpus=2 \
  --disk-size=10g

if enough memory:
minikube config set memory 12000
minikube config set cpus 8
minikube config set disk-size 20g
minikube config set driver docker

minikube start --driver=docker

optional:
kubectl get nodes
minikube status


set docker enviroment:

eval $(minikube docker-env)

2. build edge-image
docker build -f docker/Dockerfile.edge -t edge-producer:latest .
save overwrite:
docker build --no-cache -f docker/Dockerfile.edge -t edge-producer:latest .


3. start edge-deployment
kubectl delete deployment edge
kubectl apply -f k8s/edge.yaml
kubectl rollout restart deployment edge

4. edge is running?
kubectl get pods

second terminal:
kubectl port-forward deployment/edge 9001:9001

first terminal:
view logs:
cd edge
kubectl logs -f -l app=edge

it does not make sence to rune more replicas:

only if shared /tem and seperate id... 
kubectl scale deployment edge --replicas=2



### (Kafka-lokal and for VM Server – static IP  34.67.127.119)

0. clean up
docker system prune -a -f --volumes

1. Kafka & Zookeeper start
cd ~/ai-edge-to-cloud/kafka-compose
docker compose up -d

2. Kafka-Container enter / name could be different look with:  docker ps
docker exec -it kafka-compose-kafka-1 bash

3. Topic check in the container
kafka-topics --bootstrap-server localhost:9092 --list

reponse:
__consumer_offsets
edge-data
test

4. Edge-daten live 
kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic edge-data


## virtual machine VM
seperate doku for instalation: /VM/doku VMkafka.md on google server  

after installation:

start:
docker-compose up -d

show logs:
docker-compose logs -f kafka

find correct name of the container kafka e.g.: kafka_kafka_1
docker ps

go into the container:
docker exec -it kafka_kafka_1 \
kafka-topics --bootstrap-server kafka:29092 --list




Person detected on VM:
{"device_id": "edge-1", "timestamp": "2025-12-30T15:14:34.678870", "persons_detected": 1, "faces": [{"conf": 0.9335712194442749, "xmin": 0.503125, "ymin": 0.3125, "width": 0.2140625, "height": 0.28541666666666665}]}


edge:
127.0.0.1 - - [30/Dec/2025 15:18:38] "POST /frame HTTP/1.1" 200 -
🚨 EDGE RUNNING 🚨 {'device_id': 'edge-1', 'timestamp': '2025-12-30T15:18:39.503195', 'persons_detected': 1, 'faces': []}
[EDGE] ✅ Delivered to edge-data [0] @ offset 20226
[EDGE] wrote /tmp/frame.jpg
127.0.0.1 - - [30/Dec/2025 15:18:39] "POST /frame HTTP/1.1" 200 -



do not make sence only if shared /tem and seperate id... 
kubectl scale deployment edge --replicas=2


## Stop system

kubectl delete deployment edge

minikube stop

### deactivate ai-edge-venv
deactivate  



### ci cd Workflow for development and deployment:

for rework of deploy.yaml:
git branch
e.g.: edge-kafka-v3-am

git add .github/workflows/deploy.yml
git commit -m "Aktualisierte CI/CD Pipeline"
git push origin edge-kafka-v3-am

hint: „no changes added to commit“, then:

git add -A
git commit -m "Force add CI/CD workflow changes"

when changing code (in right branch) only type:

git push

will automaticaly update and run localy edge
