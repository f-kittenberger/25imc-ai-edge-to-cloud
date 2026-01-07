# ADR-001: Use of Apache Kafka for Event-Based Communication

## Status
Accepted

## Context
The system consists of multiple edge devices producing AI inference results and a cloud-based server consuming and processing these results. 
The communication must be reliable, scalable, and decoupled in time and space.

## Decision
Apache Kafka is used as the central messaging backbone between edge devices and cloud services. 
Edge components act as Kafka producers, while the server acts as a Kafka consumer.

## Consequences
- Enables asynchronous and decoupled communication.
- Supports multiple producers and consumers with consumer groups.
- Improves scalability and fault tolerance.
- Introduces operational complexity compared to direct HTTP communication.


