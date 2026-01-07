# ADR: Grafana for Data Visualization

## Status
Accepted

## Context
The system operator requires a dashboard to visualize the "AI Edge-to-Cloud" pipeline's performance (e.g., detections per device) and the environmental impact (Carbon Footprint). Raw data from Prometheus is difficult to interpret.

## Decision
We will use Grafana to visualize data stored in Prometheus. Dashboards are provisioned as code (JSON files) to ensure reproducibility.

## Consequences

- Flexible and powerful visualization (graphs, gauges, world maps).
- Seamless integration with Prometheus as a data source.
- Dashboard configurations can be stored in the repository.


