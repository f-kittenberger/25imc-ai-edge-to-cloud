# ADR-004: Kafka Deployment with ZooKeeper (Non-KRaft)

## Status
Accepted

## Context

Apache Kafka is used as the central asynchronous messaging backbone between the edge and cloud components.

Kafka can be deployed either:
- in ZooKeeper mode (traditional architecture), or
- in KRaft mode (ZooKeeper-less, newer architecture).

At the time of implementation, system stability, tooling maturity, and simplicity were prioritized over adopting the latest Kafka operational model.

## Decision

- Kafka is deployed **with ZooKeeper**.
- Kafka and ZooKeeper run on a dedicated virtual machine using Docker Compose.
- KRaft mode is **not used** in the current architecture.

## Consequences

### Positive

- Well-understood and stable deployment model
- Broad tooling and documentation support
- Easier debugging and operational transparency
- Compatibility with standard Kafka client configurations

### Negative

- Additional operational component (ZooKeeper)
- Slightly higher maintenance overhead
- Does not showcase the latest Kafka architecture model

## Rationale

ZooKeeper-based Kafka was chosen to minimize operational risk and reduce architectural complexity within the project scope.

KRaft mode is acknowledged as a future-ready alternative but was intentionally excluded to keep the system aligned with stable, widely adopted deployment practices.
