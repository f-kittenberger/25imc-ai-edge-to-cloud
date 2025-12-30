# ADR-002: Containerization with Docker and Orchestration with Kubernetes

## Status
Accepted

## Context
The system must run consistently across heterogeneous environments, including developer laptops, Raspberry Pi devices, and cloud VMs.

## Decision
All system components are packaged as Docker containers. Kubernetes is used for orchestration, deployment, and lifecycle management.

## Consequences
- Ensures reproducible builds and deployments.
- Simplifies scaling and redeployment of services.
- Enables future carbon-aware scheduling and automation.
- Adds learning and operational overhead.
