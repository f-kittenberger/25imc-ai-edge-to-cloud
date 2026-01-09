
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
and forwards inference results to Kafka, where they are consumed on a remote VM. Prometheus scrapes data and provides it to Grafana for dashboards. On the VM a decision logic is implemented that queries carbon metrics from an external API and plans redeployment of the service to regions with a lower carbon index. The redeployment is simulated. 

This setup is intentionally optimized for development stability and reproducibility, not production exposure.

Kubernetes is deliberately used in a reduced and controlled manner to ensure deterministic behavior and simplified debugging during development.

---

## Architecture (End-to-End Flow)
**Edge Path:**

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

**Monitoring & Green Path:**

→ Server Container (VM) 
→ Exposes /metrics (Persons Detected)  
→ Carbon Bridge (VM) → Fetches CO2 Data (Electricity Maps API) → Exposes /metrics  
Prometheus (VM) → Scrapes Server & Carbon Bridge → Grafana (VM) → Visualizes Dashboard (Detections + Carbon Footprint)
Prometheus → Electricity Maps API → Redeployment decision logic


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

### 6. Prometheus & Grafana

Prometheus scrapes data from the Server and Carbon Bridge.
Grafana provides dashboards for: 
- Edge Detections: Live count of people per device.
- Carbon Footprint: Real-time graph of the current zone's carbon intensity

### 7. Carbon Bridge

Simulation of Redeployment Decision Logic
Checks if the current region's intensity exceeds a threshold. If so, it runs the choose_green_region.py script to find the greenest available region and logically "switches" the active zone.
Exposes carbon metrics on port 9091.


---

## Kubernetes Configuration (Final, Minimal)

Deployment: k8s/edge.yaml  

Single replica  

Exposes container port 9001  

No Service object  

Designed to be accessed via kubectl port-forward  

This configuration is intentionally frozen to serve as a stable development reference.  
Any future changes (scaling, exposure, persistence) should be introduced explicitly and in isolation.





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

```text
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
┌───────────────────────────────┐           ┌───────────────────────────┐
│ Server Container (VM)         │           │ Carbon Bridge (VM)        │
│ - Kafka Consumer              │           │ - Electricity Maps API    │
│ - Flask REST API              │           │ - Green Region Chooser    │
│ - Prometheus Metrics          │           │ - Prometheus Metrics      │
└───────────────┬───────────────┘           └─────────────┬─────────────┘
                │ /metrics                                │ /metrics
        ┌───────▼─────────────────────────────────────────▼──┐
        │ Prometheus (VM)                                    │
        │ Scrapes: Server:5000, CarbonBridge:9091            │
        └───────┬────────────────────────────────────────────┘
                │
        ┌───────▼────────┐
        │ Browser 2      │
        │ /data          │
        │ Grafana UI     │
        └────────────────┘
```

```text
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
│       └── ...
├── edge/
│   ├── __init__.py
│   ├── app_edge.py
│   ├── infer/
│   │   ├── __init__.py
│   │   └── infer_face_pose.py
│   └── hw/
│       ├── __init__.py
│       └── frame_receiver.py
├── VM/
|   ├── server/
│   |    ├── __init__.py
│   |    └── main.py
│   ├── monitoring/
│   │   ├── carbon_bridge.py
│   │   ├── choose_green_region.py
│   │   ├── prometheus.yml
│   │   └── region_map.json
│   ├── grafana/
│   │   └── provisioning/
│   ├── docker-compose.yaml
│   ├── Dockerfile.server
│   ├── grafana.yaml
│   ├── server.yaml
│   ├── server.txt
│   └── doku VM kafka.md
└── README.md
```

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

## Virtual Machine on Google Cloud Compute Engine
* For this showcase an instance was created in the region us-central1-a.
* The source image for the boot drive is ubuntu-2404-noble-amd64-v20251021.
* Computer type: e2-medium (2 vCPUs, 4 GB RAM)
* No GPU
* External fixed IP address: 34.67.127.119
* Storage 40 GB

### Setup
Separate doku for installation: /VM/doku VMkafka.md on google server.
Create folder structure as in folder VM in the repo. 
Install DOcker Compose:
``
sudo apt-get install docker-compose-plugin 
``
### Start services from /docker/docker-compose.yml

``docker-compose up -d``

+ After changes force recreate

``docker-compose up -d --force-recreate``

  #### For single services
* ``docker compose up -d --build server`` 
* ``docker compose up -d --build prometheus`` 
* ``docker compose up -d --build grafana`` 
* ``docker compose up -d --build node_exporter`` 
* ``docker compose up -d --build carbon-bridge`` 

Check for running containers and restart as necessary:

  + ``docker ps``
  + ``docker-compose restart carbon-bridge``

## Monitoring and visualization

### Messages via Kafka
When messages are received via Kafka, this can be checked in the log

``docker-compose logs -f --tail=10 server``

The output should contain lines like this:
````
edge_server  | [SERVER] Received via Kafka: {'device_id': 'edge-simulator-03', 'timestamp': '2026-01-08T20:20:53.112784', 'persons_detected': 0, 'faces': []}
````

### Prometheus data scraping
The server provides the data via Flask, so that Prometheus can scrape the data. 

``docker-compose logs -f docker-compose logs -f --tail=20  prometheus``

Since we are working with a fixed IP and the GC-VM firewall is configured to allow traffic on the respective ports, we can also look at the data here and generate simple tabular data or charts:

http://34.67.127.119:9090/query

To look at all provided metrics being scrabed we can call

http://34.67.127.119:9090/targets

and see the endpoints of the jobs
+ carbon_intensity: http://34.67.127.119:9091/metrics
+ edge_server: http://34.67.127.119:5000/data or http://34.67.127.119:9091/metrics for the last data received
+ node: http://34.67.127.119:9100/

Prometheus also serves as the data source for Grafana, where all scraped data is available to be used in charts and dashboards.

### Grafana

Grafana can be accessed at http://34.67.127.119:3000/ with 
+ user: admin
+ password: edge-to-cloud

Dashboards and datasources are stored in json and yaml/yml files. They are loaded automatically when the service starts or is freshly built.

For the node_exporter dashboard, that shows system information like cpu load or data storage, load for CPUs can be generated to show the effect in the dashboard by running this command in the SSH console:

``
docker run --rm -it polinux/stress stress --cpu 2 --timeout 120s
``

## Redeployment simulation

Threshold is set via a variable in the docker/.env file. Standard is 200 gCO2/kWh. If the current deployment zone exceeds this value, carbon-bridge calls choose_green_region.py to get the current value for the defined alternative zones. If there is a zone with a carbon intensity below 200 gCO2/kWh the automatic redeployment is launched.

To view the results of the simulation, take a look at the log of carbon-bridge

``docker-compose logs -f --tail=10 carbon-bridge``

For a showcase there is a html interface where values can be manually set to override the scraped real-time-data and to force the redeployment simulation to be triggered.

To view the results of the simulation, take a look at the log of carbon-bridge:

http://34.67.127.119:9091/


An override action appears like this in the log:
````
carbon_bridge  | 178.190.192.133 - - [08/Jan/2026 19:52:03] "POST /override HTTP/1.1" 302 -
````

If a redeployment is triggered it can be seen in the log:
````
carbon_bridge  | 178.190.192.133 - - [08/Jan/2026 19:54:06] "POST /override HTTP/1.1" 302 -
carbon_bridge  | [bridge] API restored for DK-DK1. Value 250.0 > 200.0. Triggering...
carbon_bridge  | [bridge] Threshold exceeded; invoking chooser: choose_green_region.py
carbon_bridge  | 178.190.192.133 - - [08/Jan/2026 19:54:06] "GET / HTTP/1.1" 200 -
carbon_bridge  | [prometheus] http://34.67.127.119 metric=carbon_intensity_gCo2perkWh duration=49ms
carbon_bridge  |  - AT           CI=  236.0 gCO2/kWh region=europe-west3
carbon_bridge  |  - FR           CI=   65.0 gCO2/kWh region=europe-west1
carbon_bridge  |  - NL           CI=  473.0 gCO2/kWh region=europe-west4
carbon_bridge  |  - DK-DK1       CI=  199.0 gCO2/kWh region=europe-north1
carbon_bridge  |  - US-CENT-SWPP CI=  240.0 gCO2/kWh region=us-central1
carbon_bridge  |  - US-NW-WACM   CI=  616.0 gCO2/kWh region=us-west1
carbon_bridge  |
carbon_bridge  | [chooser] Analysis complete. Best zone found: FR
carbon_bridge  |
carbon_bridge  | Recommended deployment:
carbon_bridge  | 🚩 Zone:    FR
carbon_bridge  | 🌍 Region:  europe-west1
carbon_bridge  | 🌳 C-Index: None
carbon_bridge  |
carbon_bridge  | [bridge] 🚨 MIGRATION! Switching Active Zone: DK-DK1 -> FR

````
#### This is the endpoint of the simulation, there is no physical redeployment happening as explained in ADR-009 and ADR-010

### Show logs:

Messages from edge devices
docker-compose logs -f kafka

find correct name of the container kafka e.g.: kafka_kafka_1
docker ps

go into the container:
docker exec -it kafka_kafka_1 \
kafka-topics --bootstrap-server kafka:29092 --list


Person detected on VM:
````
michael_aichinger_spitz_gmail_co@instance-20251109-123917:~$ docker exec -it docker-kafka-1 bash [appuser@6aa315cc8c10 ~]$ kafka-topics --bootstrap-server localhost:9092 --list __consumer_offsets edge-data [appuser@6aa315cc8c10 ~]$ [appuser@6aa315cc8c10 ~]$ kafka-console-consumer \ > --bootstrap-server localhost:9092 \ > --topic edge-data {"device_id": "edge-laptop-03", "timestamp": "2026-01-07T11:10:37.034142", "persons_detected": 1, "faces": [{"conf": 0.7749168276786804, "xmin": 0.7125, "ymin": 0.3875, "width": 0.2046875, "height": 0.27291666666666664}]} {"device_id": "edge-laptop-02", "timestamp": "2026-01-07T11:10:39.470175", "persons_detected": 1, "faces": [{"conf": 0.7055118680000305, "xmin": 0.7671875, "ymin": 0.36041666666666666, "width": 0.16875, "height": 0.22291666666666668}]}
````

edge:
````
🚨 EDGE RUNNING 🚨 {'device_id': 'edge-laptop-03', 'timestamp': '2026-01-07T14:37:10.422390', 'persons_detected': 1, 'faces': [{'conf': 0.6038628816604614, 'xmin': 0.6484375, 'ymin': 0.475, 'width': 0.1828125, 'height': 0.24166666666666667}]}
[EDGE] wrote /tmp/frame.jpg
127.0.0.1 - - [07/Jan/2026 14:37:11] "POST /frame HTTP/1.1" 200 -
127.0.0.1 - - [07/Jan/2026 14:37:11] "GET /frame_data HTTP/1.1" 200 -
````
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
