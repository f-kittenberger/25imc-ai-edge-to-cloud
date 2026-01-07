# ADR: Simulation of Multi-Region Deployment

## Status
Accepted

## Context
The project aims to demonstrate the concept of moving workloads to regions with lower carbon intensity. However, physically moving a Google Cloud Compute Engine VM between regions dynamically is more complex than expected and could have been accomplished by a different setup of the project.

## Decision
We will simulate the redeployment process using a custom "Carbon Bridge" service (carbon_bridge.py). Instead of moving physical infrastructure, the service maintains a logical CURRENT_ZONE state. When a threshold is exceeded, a script (choose_green_region.py) selects a better zone, and the system logically "switches" to it.

## Consequences

### Positive
- Successfully demonstrates the logic and algorithm of carbon-aware computing without infrastructure overhead.
- Migration" is instant, allowing for easier demonstration during presentations.

### Negative
- The dashboard shows the "Active Zone" based on a variable, not the physical location of the server (which remains in the original VM).
