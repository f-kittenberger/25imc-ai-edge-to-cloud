# AI Edge-to-Cloud System

## Overview

This project implements an edge-to-cloud architecture for real-time computer vision inference. 
Camera frames are captured in a web browser, processed locally on an edge device, and only structured inference results are transmitted to the cloud via Apache Kafka.

The system is designed for architectural clarity, traceability of design decisions, and academic evaluation rather than full-scale production deployment.

---

## Architecture Overview

The architecture follows a strict edge-first approach:

**Browser (Camera)**
→ HTTP POST  
→ **Edge Application**
→ AI Inference  
→ **Kafka**
→ **Cloud Server**
→ Storage, Metrics, Visualization

All asynchronous communication between edge and cloud components is handled exclusively via Kafka.

---

## End-to-End Data Flow

1. A browser captures camera frames and sends them via HTTP POST to the edge application.
2. The edge application stores the most recent frame temporarily.
3. AI inference runs periodically on the edge device.
4. Inference results are serialized as JSON and published to Kafka.
5. A cloud-based server consumes Kafka messages.
6. The server exposes stored data and metrics via REST endpoints.
7. The browser retrieves bounding box data for visualization.

---

## Edge Application

### Responsibilities

- Receive camera frames via HTTP
- Store the most recent frame ephemerally
- Execute AI inference periodically
- Publish inference results to Kafka
- Provide bounding box data for browser visualization

### Technical Characteristics

- Implemented as a single Flask application
- Stateless design (no persistent storage)
- Background threads for inference and Kafka publishing
- No frontend assets served from the container

### HTTP Endpoints

| Endpoint      | Method | Description |
|---------------|--------|-------------|
| `/frame`      | POST   | Receives a Base64-encoded JPEG frame |
| `/frame_data` | GET    | Returns latest bounding boxes |

---

## AI Inference

- Primary signal: MediaPipe Face Detection
- Optional: Pose Detection for visualization
- A person is counted when at least one face is detected

### Output Schema Example

```json
{
  "device_id": "edge-laptop-01",
  "timestamp": "2026-01-02T10:48:43Z",
  "persons_detected": 1,
  "faces": [
    {
      "conf": 0.93,
      "xmin": 0.45,
      "ymin": 0.29,
      "width": 0.22,
      "height": 0.30
    }
  ]
}
```

---

## Messaging Layer (Kafka)

- Apache Kafka is used as the central asynchronous messaging backbone.
- Kafka runs with ZooKeeper using Docker Compose on a dedicated virtual machine.
- The edge application acts as a Kafka producer.
- The cloud server acts as a Kafka consumer.

Kafka is the only mechanism for edge-to-cloud data transfer.

---

## Cloud Server

### Responsibilities

- Consume Kafka events
- Store inference results
- Expose REST APIs for data access
- Export Prometheus-compatible metrics

### Endpoints

| Endpoint   | Description |
|------------|-------------|
| `/data`    | Returns stored inference events |
| `/metrics` | Prometheus metrics endpoint |

---

## Visualization and Observability

- Bounding boxes are rendered in the browser by polling the edge application.
- Prometheus scrapes metrics from the cloud server.
- Grafana dashboards visualize:
  - Detected persons
  - System performance metrics

---

## Containerization and Kubernetes Usage

All components are containerized using Docker.

Kubernetes (Minikube) is used locally **only for development purposes**:
- Container lifecycle management
- Restart behavior
- Isolation during development

Kafka and ZooKeeper are explicitly **not deployed on Kubernetes**.

Browser-to-edge communication is exposed using `kubectl port-forward`.

This decision is documented in **ADR-002**.

---

## Architecture Decision Records (ADRs)

Architectural decisions are documented as ADRs to ensure traceability and evaluability.

### ADR-002 – Containerization and Kubernetes Usage
- Docker as the primary packaging mechanism
- Kubernetes limited to local development usage
- Kafka excluded from Kubernetes deployment

→ See: `docs/adr/adr-002-containerization-and-kubernetes-usage.md`

### ADR-004 – Kafka Deployment with ZooKeeper (Non-KRaft)
- ZooKeeper-based Kafka deployment
- KRaft mode explicitly excluded from the current scope

→ See: `docs/adr/adr-004-kafka-deployment-with-zookeeper.md`

---

## UML and Architectural Modeling

- Component diagrams reflect actual code modules
- Deployment diagrams focus on nodes, containers, and infrastructure
- Sequence diagrams model meaningful runtime scenarios
- Trivial or redundant diagrams are intentionally excluded

All diagrams are accompanied by textual explanations to ensure clarity.

---

## CI/CD and Sustainability

- CI pipelines validate builds and container images
- Edge inference reduces cloud compute load
- Kafka avoids continuous HTTP streaming
- Reduced network traffic contributes to lower energy consumption

---

## Design Principles

- Edge-first processing
- Stateless components
- Explicit data flow
- Separation of concerns
- Architectural decisions documented and justified

























--------------------------Lauffähig Kafka + zookeeper -----------------------------------

source ai-edge-venv/bin/activate


✅ FINAL RUNBOOK (REPRODUZIERBAR & STABIL)

Edge (K8s) → Kafka (Docker Compose extern) → Server (K8s)

Ziel:
Egal wann, egal wie oft:
Du kannst alles löschen, alles neu starten und es läuft wieder.

🧠 Architektur (fest, nicht mehr ändern)
Komponente	Läuft wo
Kafka	Docker Compose (VM / Host)
Zookeeper	Docker Compose (VM / Host)
Edge	Kubernetes (Minikube)
Server	Kubernetes (Minikube)
Verbindung	K8s → host.docker.internal:9092

❗ Kafka läuft NICHT in Kubernetes
❗ K8s greift immer extern auf Kafka zu

🔒 GOLDENE REGELN (bitte merken)

Kafka-Änderung ≠ K8s-Änderung

ENV-Änderung + imagePullPolicy: Never ⇒ IMMER neu bauen

Pods löschen reicht NICHT – Deployments cachen

Beweis ist immer: env im Pod

🧹 0. KOMPLETT RESET (wenn irgendwas komisch ist)
Kubernetes zurücksetzen (optional, aber sauber)
minikube stop
minikube start

Docker sauber halten (optional)
docker system prune -f

🟢 1. Kafka + Zookeeper STARTEN (Docker Compose)
cd ~/ai-edge-to-cloud/kafka-compose
docker compose down -v
docker compose up -d

Prüfen
docker ps


✅ Erwartet:

kafka-compose-kafka-1
kafka-compose-zookeeper-1

🔎 2. Kafka ADVERTISED LISTENERS PRÜFEN (KRITISCH!)
docker exec kafka-compose-kafka-1 env | grep ADVERTISED


✅ MUSS GENAU SO SEIN:

KAFKA_ADVERTISED_LISTENERS=INTERNAL://kafka:29092,EXTERNAL://host.docker.internal:9092


❌ Wenn hier IP steht → Kafka falsch konfiguriert → STOP.

📦 3. Kafka Topic anlegen
docker exec kafka-compose-kafka-1 kafka-topics \
  --bootstrap-server kafka:29092 \
  --create --if-not-exists \
  --topic edge-data \
  --partitions 1 \
  --replication-factor 1


Prüfen:

docker exec kafka-compose-kafka-1 kafka-topics \
  --bootstrap-server kafka:29092 --list


✅ Erwartet:

edge-data

🐳 4. Docker-Umgebung für Minikube setzen (PFLICHT!)
eval $(minikube docker-env)


❗ Ab jetzt werden Images INS Minikube gebaut

🏗 5. IMAGES NEU BAUEN (IMMER!)
docker build -f docker/Dockerfile.edge -t edge:latest .
docker build -f docker/Dockerfile.server -t server:latest .


Prüfen:

docker images | grep -E "edge|server"

🚀 6. Kubernetes Deployments NEU AUFSETZEN
Server
kubectl delete deployment server --ignore-not-found
kubectl delete service server --ignore-not-found
kubectl apply -f k8s/server.yaml

Edge
kubectl delete deployment edge --ignore-not-found
kubectl apply -f k8s/edge.yaml

🔍 7. ABSOLUTER BEWEIS – ENV im Pod
Server
kubectl exec -it \
  $(kubectl get pod -l app=server -o jsonpath='{.items[0].metadata.name}') \
  -- env | grep BOOTSTRAP


✅ MUSS SEIN

BOOTSTRAP_SERVERS=host.docker.internal:9092


Wenn nicht → Image NICHT neu gebaut.

📡 8. LOGS = FINALER BEWEIS
kubectl logs -l app=server -f


✅ Erwartet (dein aktueller Beweis):

[SERVER] Kafka consumer started, bootstrap=host.docker.internal:9092
[SERVER] Received via Kafka: {...}


➡️ Pipeline läuft. Punkt.

🌐 9. (Optional) HTTP prüfen
kubectl port-forward svc/server 5000:5000
curl http://localhost:5000/data

⚠️ Zur Warnung in deinen Logs (harmlos!)
Broker reports different ClusterId ...


➡️ Kommt von altem Consumer-Offset / Neustart
➡️ KEIN Fehler, Kafka synchronisiert sich neu
➡️ Kann ignoriert werden

🧾 WAS DU JETZT HAST (für Abgabe)

✅ Funktionierende Edge→Kafka→Server Pipeline
✅ Externe Kafka-Architektur (realistisch, stabil)
✅ K8s + Docker sauber getrennt
✅ Reproduzierbares Runbook
✅ ADR-fähige Architekturentscheidung

🏁 ABSCHLUSS

Du hast nichts „falsch gemacht“.
Du bist genau an den Punkten hängen geblieben, an denen auch Profis hängen:

K8s Caching

Docker vs Minikube Docker

Kafka Advertised Listeners

Jetzt hast du das unter Kontrolle.