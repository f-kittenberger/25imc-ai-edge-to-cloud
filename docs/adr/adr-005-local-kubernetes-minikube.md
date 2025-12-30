# ADR-005: Local Kubernetes via Minikube

## Context
The system requires demonstration of orchestration, scaling, and failure recovery.
A local development environment is needed that resembles the production Kubernetes setup.

## Decision
Use Minikube to run a local single-node Kubernetes cluster for development and testing.

## Consequences
- Enables local testing of deployments, scaling, and consumer groups
- Adds setup complexity compared to plain Docker
- Production environment will use a multi-node Kubernetes cluster
