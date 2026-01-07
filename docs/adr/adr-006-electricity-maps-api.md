# ADR: Use of Electricity Maps API for Carbon Data

## Status
Accepted

## Context
To fulfill the project requirement of "Carbon Aware Computing," the system must be aware of the real-time carbon intensity of different geographical regions. The system needs a reliable, external source of truth to determine the "greenest" region to run the workload..

## Decision
We will use the Electricity Maps API to fetch real-time carbon intensity data for specific zones (e.g., AT, TR, US-CENT-SWPP). This is implemented in the carbon_bridge.py service.

## Consequences

### Positive 
- Provides accurate, real-time, and historical data for global power grids.
- Easy integration via HTTP REST API.

### Negative
- Requires an API token and management of rate limits.
- Dependency on an external 3rd party service.
