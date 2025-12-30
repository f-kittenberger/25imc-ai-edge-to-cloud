# ADR-001: Use of Apache Kafka for Event-Based Communication

## Status
Accepted

## Context
The system consists of multiple edge devices producing AI inference results and a cloud-based server consuming and processing these results. The communication must be reliable, scalable, and decoupled in time and space.

## Decision
Apache Kafka is used as the central messaging backbone between edge devices and cloud services. Edge components act as Kafka producers, while the server acts as a Kafka consumer.

## Consequences
- Enables asynchronous and decoupled communication.
- Supports multiple producers and consumers with consumer groups.
- Improves scalability and fault tolerance.
- Introduces operational complexity compared to direct HTTP communication.


# ADR-001: Why Kafka for Edge-to-Cloud Communication

## Status
Accepted

## Context
The system requires reliable, scalable, and decoupled communication between multiple edge devices
(e.g., Raspberry Pi-based AI inference nodes) and a cloud-based server. The communication layer must
support asynchronous data transfer, fault tolerance, and future scalability, while remaining suitable
for local development and Kubernetes-based deployment.

## Decision
Apache Kafka is used as the primary messaging backbone between edge producers and cloud consumers.
Kafka topics are used to decouple edge inference workloads from server-side processing and storage.

## Consequences

### Positive
- Strong decoupling between producers and consumers
- Supports horizontal scalability (multiple edge devices, multiple consumers)
- Built-in durability and replayability of events
- Well-supported ecosystem (Kubernetes, Prometheus, Grafana)
- Enables future extensions such as stream processing and carbon-aware routing

### Negative
- Higher operational complexity compared to simple HTTP
- Additional resource consumption (broker, storage)
- Learning curve for configuration and monitoring

## Alternatives Considered
- Direct HTTP communication between edge and server
- Message queues such as RabbitMQ
- ZeroMQ-based point-to-point messaging

Kafka was selected due to its strong guarantees, ecosystem support, and alignment with cloud-native
and event-driven architectures.
