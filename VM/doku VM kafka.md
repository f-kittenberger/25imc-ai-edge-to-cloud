sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker


-->
canning linux images...                                                                                       

Running kernel seems to be up-to-date.

No services need to be restarted.

No containers need to be restarted.

No user sessions are running outdated binaries.

No VM guests are running outdated hypervisor (qemu) binaries on this host.


sudo usermod -aG docker $USER
logout
# neu einloggen


mkdir -p ~/kafka
cd ~/kafka

Schritt 4: docker-compose.yml erstellen
nano docker-compose.yml


Inhalt (IP ist deine feste IP):

version: "3.8"

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.3
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
    restart: unless-stopped

  kafka:
    image: confluentinc/cp-kafka:7.5.3
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181

      KAFKA_LISTENERS: INTERNAL://0.0.0.0:29092,EXTERNAL://0.0.0.0:9092
      KAFKA_ADVERTISED_LISTENERS: INTERNAL://kafka:29092,EXTERNAL://34.67.127.119:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: INTERNAL

      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    restart: unless-stopped


Speichern: Ctrl+O → Enter → Ctrl+X

Starten:
docker-compose up -d

logs ansehen:
docker-compose logs -f kafka


michael_aichinger_spitz@instance-20251109-123917:~/kafka$ grep KAFKA_ADVERTISED_LISTENERS docker-compose.yml
      KAFKA_ADVERTISED_LISTENERS: INTERNAL://kafka:29092,EXTERNAL://34.67.127.119:9092
michael_aichinger_spitz@instance-20251109-123917:~/kafka$ docker ps

CONTAINER ID   IMAGE                             COMMAND                  CREATED          STATUS          PORTS                                         NAMES
4ac878d47356   confluentinc/cp-kafka:7.5.3       "/etc/confluent/dock…"   12 minutes ago   Up 12 minutes   0.0.0.0:9092->9092/tcp, [::]:9092->9092/tcp   kafka_kafka_1
1f4b4c0f0505   confluentinc/cp-zookeeper:7.5.3   "/etc/confluent/dock…"   12 minutes ago   Up 12 minutes   2181/tcp, 2888/tcp, 3888/tcp                  kafka_zookeeper_1

die richtigen docker Bezeicghnungen einsetzen

5️⃣ Die korrekte Art zu testen (sehr wichtig)
✅ Test A: intern (Container → Container)

Im Container immer den internen Listener verwenden:

docker exec -it kafka_kafka_1 \
kafka-topics --bootstrap-server kafka:29092 --list


👉 NICHT localhost
👉 NICHT die externe IP



Firewall für VM Kafka zulassen:

✅ Lösung: Eine einzige Firewall-Regel erstellen

Wir machen das minimal, sauber, verständlich.

🧱 Ziel der Firewall-Regel

Erlaube:

TCP

Port 9092

von überall (0.0.0.0/0)
→ nur für Kafka

1️⃣ Neue Firewall-Regel erstellen

Google Cloud Console →

VPC network → Firewall rules → CREATE FIREWALL RULE

2️⃣ Felder GENAU SO ausfüllen
🔹 Name
allow-kafka-9092

🔹 Netzwerk
default

🔹 Traffic-Richtung
Eingehender Traffic

🔹 Aktion bei Übereinstimmung
Zulassen

🔹 Ziele
Alle Instanzen im Netzwerk


(oder alternativ später per Netzwerk-Tag – für jetzt nicht nötig)

🔹 Quellfilter
IPv4-Bereiche

🔹 Quell-IPv4-Bereiche
0.0.0.0/0


(ja, bewusst offen – Kafka ist kein Webserver, später kann man das einschränken)

🔹 Protokolle und Ports

❌ Alle zulassen → NEIN

✅ Angegebene Protokolle und Ports

Dann:

TCP
Ports:

9092

🔹 Logs
Aus


(reicht völlig)

👉 Erstellen / Speichern


docker run -it --rm confluentinc/cp-kafka:7.5.3 \
kafka-console-producer \
--bootstrap-server 34.67.127.119:9092 \
--topic test

Wenn du jetzt:

>


siehst OHNE Warnungen → 🎉 ERFOLG

Tippe:

hello


Enter → keine Fehlermeldung = perfekt.

Optional: Consumer-Test
docker run -it --rm confluentinc/cp-kafka:7.5.3 \
kafka-console-consumer \
--bootstrap-server 34.67.127.119:9092 \
--topic test \
--from-beginning

Ergebnis:
--> hello


Warum das alles logisch ist (wichtig fürs Verständnis)
Ebene	Status
Kafka	✅ läuft
Docker	✅ korrekt
advertised.listeners	✅ korrekt
Port-Mapping	✅ korrekt
Firewall	❌ blockiert
Ergebnis	❌ externe Clients kommen nicht rein

Firewall-Regeln sind die letzte „Tür“.
Alles dahinter kann perfekt sein – ohne Regel bleibt sie zu.

🔑 Merksatz (sehr wichtig)

In Google Cloud:
Port offen im Container ≠ Port offen im Netzwerk.
Firewall entscheidet immer zuletzt.

🚀 Definition of Done (nach diesem Schritt)


✔ Kafka läuft
✔ Statische IP
✔ EXTERNAL Listener
✔ Firewall offen
✔ Producer von außen verbindet

👉 Ab hier ist Kafka produktionsbereit.

Laptop / Raspberry Pi
   │
   │  (TCP 9092)
   ▼
Kafka (VM, Docker)
   │
   │  (internal)
   ▼
Server / Consumer 

/home/michael/ai-edge-to-cloud/
├── kafka/                # Kafka + Zookeeper (Docker Compose)
│   └── docker-compose.yml
│
├── docker/               # Dockerfiles
│   └── Dockerfile.server
│
├── requirements/
│   └── server.txt
│
├── server/
│   └── main.py
│
└── logs/




Der Server ist:

✅ Kafka Consumer

✅ liest vom Topic test (oder später people-detections)

✅ speichert / hält letzten Wert im Speicher

✅ stellt HTTP-Endpoint bereit (Flask)

✅ wird später:

von Browser

von Grafana

von Prometheus abgefragt

Noch kein Kubernetes.
Noch kein CI-Deploy.
Nur Funktionalität.

🔑 Architektur-Merksatz (wichtig!)

Kafka = Infrastruktur
Server = Anwendung
Nie in denselben Ordner


