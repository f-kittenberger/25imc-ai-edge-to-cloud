# ADR: Physical Multi-Region Redeployment

## Status
Deprecated

## Context
To achieve "Carbon Aware Computing," the ideal scenario involves physically moving the workload (the Virtual Machine) to the Google Cloud region that currently has the lowest Carbon Intensity (e.g., moving from europe-west3 to us-central1 when the wind is blowing in the US).

## Decision
We have deprecated the concept of physically moving the VM between regions. We will instead rely on the logical simulation described in ADR-010.

## Reasons

- Google Cloud Static External IP addresses are regional resources. They cannot be transferred between regions.
- Moving the VM to a new region would inevitably result in a change of the server's public IP address.
- The Edge devices connect to the cloud via a specific IP address defined in BOOTSTRAP_SERVERS. Changing the server IP would break connectivity for all edge devices, requiring manual reconfiguration or a complex dynamic discovery service