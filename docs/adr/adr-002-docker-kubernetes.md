# ADR-002: Containerization and Kubernetes Usage

## Status
Accepted

## Context

The system consists of an edge application performing AI inference and a cloud-based server consuming inference results via Kafka.

To ensure reproducibility, isolation, and ease of deployment across development environments, containerization is required. During development, Kubernetes is used locally to manage the lifecycle of the edge application.

However, the system is not intended to run fully on Kubernetes in its current scope. In particular, Kafka and ZooKeeper are not deployed on Kubernetes.

## Decision

- All application components (edge and server) are packaged as Docker containers.
- Kubernetes (Minikube) is used **locally and only for development purposes** to:
  - Manage container lifecycle
  - Enable restart and isolation behavior
  - Simulate a lightweight orchestration environment
- Kafka and ZooKeeper are deployed **outside Kubernetes** using Docker Compose on a dedicated virtual machine.
- No Kubernetes-native services (Ingress, Service, ConfigMap, etc.) are required for the core data flow.
- Browser-to-edge communication is explicitly exposed using `kubectl port-forward`.

## Consequences

### Positive

- Clear separation between development orchestration and runtime architecture
- Reduced operational complexity
- Faster local iteration without full cluster management
- Avoids unnecessary Kubernetes abstraction for a single-node edge workload

### Negative

- Kubernetes knowledge is applied only partially
- The architecture is not immediately portable to a full Kubernetes production cluster
- Kafka scaling and orchestration are handled outside the Kubernetes ecosystem

## Rationale

The project prioritizes architectural clarity and demonstrability over production-grade orchestration.  
Using Kubernetes selectively avoids over-engineering while still demonstrating container orchestration concepts.
