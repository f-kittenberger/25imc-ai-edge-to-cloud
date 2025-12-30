# AI Edge-to-Cloud System

## Project Overview
Dieses Projekt implementiert ein AI Edge-to-Cloud System, bei dem Edge-Geräte Daten über eine Kafka-basierte Pipeline an einen Server in der Cloud oder im lokalen Kubernetes-Cluster senden. Die Anwendung ermöglicht Echtzeit-Verarbeitung von Sensordaten und KI-Inferenz direkt am Edge sowie Aggregation und Monitoring in der Cloud.

## Architecture
- **Edge Device**: Generiert Sensordaten und führt KI-Inferenz aus. Liefert Ergebnisse über Kafka.
- **Kafka**: Zentrale Event-Streaming-Plattform, die Edge-Geräte vom Server entkoppelt.
- **Server**: Konsumiert Kafka-Nachrichten, speichert die Daten und stellt REST-Endpunkte bereit.
- **Monitoring**: Optionales Modul für Visualisierung, Logging und Carbon-Aware Adaptation.

## Architecturally Significant Use Cases
1. **Person Detection at the Edge**  
   KI-basierte Analyse von Kameradaten direkt auf dem Edge-Device.
2. **Event Streaming via Kafka**  
   Zuverlässige, skalierbare Übertragung von Ereignissen an den Server.
3. **Cloud-side Data Aggregation**  
   Konsolidierung und Speicherung eingehender Daten auf dem Server.
4. **Visualization and Monitoring**  
   Darstellung von Live-Daten für Monitoring und Analyse.
5. **Carbon-Aware Adaptation (geplant)**  
   Anpassung des Systems unter Berücksichtigung von Energieverbrauch und CO₂-Emissionen.

## Diagrams
- **Component Diagram**: Zeigt die einzelnen Module (Edge, Kafka, Server) und deren Schnittstellen.
- **Deployment Diagram**: Stellt dar, wie Komponenten in Kubernetes oder auf VMs bereitgestellt werden.
- **Sequence Diagrams**: Zeigt Datenfluss und Interaktionen für jeden Use Case.

## Deployment

### Local (Docker)
Stelle sicher, dass Docker APP läuft.


eval $(minikube docker-env)
minikube start

docker build -f docker/Dockerfile.edge -t edge:latest .
docker build -f docker/Dockerfile.server -t server:latest .

### Kubernetes (Minikube)
### service entry added to kafka.yaml
kubectl apply -f k8s/kafka.yaml
kubectl apply -f k8s/server.yaml
kubectl apply -f k8s/edge.yaml
kubectl apply -f k8s/prometheus.yaml
kubectl apply -f k8s/grafana.yaml

kubectl get pods -A
kubectl get svc

kubectl logs -l app=edge -f
kubectl logs -l app=server -f
kubectl port-forward deployment/server 5000:5000
curl http://127.0.0.1:5000/data

k9s for overview
## Restart Pods e.g. server
kubectl delete pod -l app=server
minikube stop

## Manually push data for testing
curl -X POST http://localhost:5000/data -H "Content-Type: application/json" -d '{"persons_detected": 5, "device_id": "camera-01"}'

## Prometheus
kubectl port-forward svc/prometheus 9090:9090
visit http://127.0.0.1:9090/query

## Grafana
kubectl -n observability port-forward svc/grafana 3000:3000
http://127.0.0.1:3000/?orgId=1
User admin
PW admin (changed to edge-to-AI)

## Data Flow Overview

In the current setup, all data is transmitted via **Kafka**. The HTTP POST endpoint on the server is only used for optional testing or direct queries.
Edge Device
│
│ produces events
▼
Kafka Topic: edge-data
│
│ consumed by
▼
Server Application
│
│ stores and processes
▼
Data Store / Monitoring



- **Edge → Kafka**: The edge devices produce inference results (person detection etc.) and send them to the Kafka topic `edge-data`.
- **Server → Kafka**: The server consumes the `edge-data` topic using a Kafka consumer and appends the data to its internal store.
- **HTTP POST**: Only used optionally for debugging or testing, not part of the main production flow.

**Summary:** Kafka acts as the central event bus, decoupling edge and server components and ensuring a scalable, fault-tolerant communication channel.


Apache Kafka is used as a central event streaming platform to decouple edge devices from cloud services, enabling reliable, scalable, and fault-tolerant transmission of AI inference results.



✅ FINAL RUNBOOK – Edge → Kafka → Server (funktionierend)

Ziel:
Edge (K8s) sendet Daten → Kafka (Docker Compose) → Server (K8s) empfängt & verarbeitet

🔹 0. Voraussetzungen

Docker läuft

Minikube läuft

Projektverzeichnis: ~/ai-edge-to-cloud

🔹 1. Kafka + Zookeeper (Docker Compose, extern)
📁 Verzeichnis
cd ~/ai-edge-to-cloud/kafka-compose

▶️ Start
docker compose down -v
docker compose up -d

✅ Prüfen
docker ps


Erwartet:

kafka-compose-kafka-1

kafka-compose-zookeeper-1

🔹 2. Kafka-Konfiguration verifizieren (entscheidend!)
docker exec kafka-compose-kafka-1 bash -c 'env | grep ADVERTISED'


MUSS sein:

KAFKA_ADVERTISED_LISTENERS=INTERNAL://kafka:29092,EXTERNAL://192.168.49.2:9092

🔹 3. Kafka Topic anlegen
docker exec kafka-compose-kafka-1 kafka-topics \
  --bootstrap-server kafka:29092 \
  --create --if-not-exists \
  --topic edge-data \
  --partitions 1 \
  --replication-factor 1

Prüfen:
docker exec kafka-compose-kafka-1 kafka-topics \
  --bootstrap-server kafka:29092 --list


Erwartet:

edge-data

🔹 4. Minikube-IP ermitteln (für K8s)
minikube ip


📌 In deinem Fall:

192.168.49.2

🔹 5. Edge Deployment (Kubernetes)
k8s/edge.yaml
env:
  - name: BOOTSTRAP_SERVERS
    value: 192.168.49.2:9092

Anwenden + Neustart
cd ~/ai-edge-to-cloud
kubectl apply -f k8s/edge.yaml
kubectl delete pod -l app=edge

Logs prüfen
kubectl logs -l app=edge -f


Erwartet:

[EDGE] Sent: {...}

🔹 6. Server Deployment (Kubernetes)
k8s/server.yaml
env:
  - name: BOOTSTRAP_SERVERS
    value: 192.168.49.2:9092

Anwenden + Neustart
kubectl apply -f k8s/server.yaml
kubectl delete pod -l app=server

Prüfen: Env im Pod
kubectl exec -it $(kubectl get pod -l app=server -o jsonpath='{.items[0].metadata.name}') -- env | grep BOOTSTRAP


Erwartet:

BOOTSTRAP_SERVERS=192.168.49.2:9092

🔹 7. ✅ FINALER BEWEIS – Server empfängt Kafka-Daten
kubectl logs -l app=server -f


🎉 Erwartet (Beweis):

[SERVER] Received via Kafka: {...}


➡️ Edge → Kafka → Server läuft

🔹 8. (Optional) HTTP-Endpunkt prüfen
kubectl port-forward svc/server 5000:5000
curl http://localhost:5000/data


Erwartet:

[
  {
    "device_id": "edge-1",
    "timestamp": "...",
    "persons_detected": 24
  }
]

🧠 Architektur-Entscheidung (für Doku / ADR)

Kafka außerhalb von Kubernetes

Begründung:

stabileres lokales Setup

weniger Stateful-Komplexität

saubere Netzwerkgrenzen

realitätsnah für Edge/Cloud-Szenarien

Kubernetes nutzt Kafka als externen Event-Bus

Komponente	Läuft wo?
Kafka	❌ Minikube → ✅ Docker (VM)
Zookeeper	❌ Minikube → ✅ Docker (VM)
Edge	✅ Minikube
Server	✅ Minikube
CI/CD	✅ VM / GitHub
Verbindung	Minikube → VM IP

✅ Sauber alles runterfahren (ohne Datenverlust)
1️⃣ Kubernetes / Minikube (falls noch läuft)
minikube stop


(oder minikube delete, wenn du Speicher brauchst – Code bleibt)

2️⃣ Kafka & Zookeeper (Docker Compose)
cd ~/ai-edge-to-cloud/kafka-compose
docker compose down

3️⃣ Docker generell beruhigen
docker ps


➡️ sollte leer sein oder nur Systemcontainer zeigen

Optional:

docker system prune



VM instanz starten

source ai-edge-venv/bin/activate

minicube start

cd ~/ai-edge-to-cloud/kafka-compose

docker compose down -v

docker compose up -d

docker ps

Erwartet:

kafka-compose-kafka-1

kafka-compose-zookeeper-1

🔹 2. Kafka-Konfiguration verifizieren (entscheidend!)
docker exec kafka-compose-kafka-1 bash -c 'env | grep ADVERTISED'


MUSS sein:

KAFKA_ADVERTISED_LISTENERS=INTERNAL://kafka:29092,EXTERNAL://192.168.49.2:9092

🔹 3. Kafka Topic anlegen
docker exec kafka-compose-kafka-1 kafka-topics \
  --bootstrap-server kafka:29092 \
  --create --if-not-exists \
  --topic edge-data \
  --partitions 1 \
  --replication-factor 1

Prüfen:
docker exec kafka-compose-kafka-1 kafka-topics \
  --bootstrap-server kafka:29092 --list
























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