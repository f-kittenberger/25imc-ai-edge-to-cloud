# ADR-004: Kafka KRaft Mode without ZooKeeper

## Status
Accepted

## Context
Traditional Kafka deployments depend on ZooKeeper, which increases system complexity and operational overhead.

## Decision
Kafka is deployed in KRaft mode, using its internal Raft-based metadata management, eliminating the need for ZooKeeper.

## Consequences
- Simplifies deployment and configuration.
- Reduces number of system components.
- Aligns with modern Kafka best practices.
- Limits compatibility with very old Kafka tooling.
