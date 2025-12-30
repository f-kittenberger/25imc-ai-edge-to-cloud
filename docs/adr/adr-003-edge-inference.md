# ADR-003: Edge-Based AI Inference on Raspberry Pi

## Status
Accepted

## Context
Continuous video streaming to the cloud would introduce high bandwidth usage, latency, and energy consumption.

## Decision
AI inference (person detection) is executed directly on edge devices using a lightweight YOLOv8-Nano model. Only aggregated results are transmitted to the cloud.

## Consequences
- Reduces network traffic and cloud compute load.
- Improves latency and privacy.
- Requires optimized models and hardware-aware deployment.
