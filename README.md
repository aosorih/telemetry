# Network Telemetry Benchmark: ICMP, OWAMP and In-band Network Telemetry (INT)

Experimental framework for comparing network latency measurement techniques using:

- **ICMP**
- **OWAMP-style unidirectional measurement**
- **In-band Network Telemetry (INT)**
- **P4 programmable data planes**
- **Python-based traffic generation and telemetry collection**

This repository contains the experimental implementation used to evaluate the behavior of traditional active telemetry techniques against programmable data-plane telemetry.

The project focuses on latency measurement and the impact of packet payload size across different telemetry approaches.

---

## Overview

Traditional network monitoring techniques such as ICMP and OWAMP measure network performance from end hosts. In contrast, In-band Network Telemetry (INT) enables programmable switches to insert telemetry information directly into packets while they traverse the network.

This project implements and compares these approaches in a controlled experimental environment.

The repository includes:

- ICMP latency measurement using raw sockets
- UDP-based unidirectional measurement inspired by OWAMP
- P4 programs for INT timestamp collection
- INT telemetry report generation
- Python/Scapy collector for telemetry extraction
- Configurable packet count and payload sizes for controlled experiments

---

## Architecture

The experimental workflow can be summarized as:

```text
Traffic Generator
      |
      v
+-------------+
| Source Host |
+-------------+
      |
      v
+---------------------+
| P4 Programmable     |
| Network             |
| BMv2 / v1model      |
+---------------------+
      |
      v
+------------------+
| Destination Host |
+------------------+
      |
      +----------> Telemetry Collector
