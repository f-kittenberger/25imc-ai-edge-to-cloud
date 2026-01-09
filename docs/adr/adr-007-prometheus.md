# ADR-007: Prometheus for Metrics Collection

## Status
Accepted

## Context
The system generates numerical data that changes over time, specifically the number of persons detected by edge devices and the current carbon intensity of the deployment zone. We need a time-series database to collect, store, and allow querying of this data.

## Decision
We will use Prometheus as the monitoring and time-series database. It will scrape metrics from the Server application, the Carbon Bridge and Node Exporter.

## Consequences

### Positive
- Standard industry solution for container/Kubernetes monitoring.
- The "pull" model works well with our Docker Compose architecture where services expose HTTP endpoints.

### Negative
- Fiddeling with configuring scrape targets in prometheus.yml.
