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
```

For INT measurements, the programmable data plane captures packet timestamps and generates a telemetry report containing:

- ingress timestamp
- egress timestamp
- packet size

The collector extracts these fields and calculates packet latency.

---

## Telemetry Techniques

### ICMP

The ICMP implementation uses raw sockets to generate ICMP Echo Request packets.

The client allows the experimenter to configure:

- destination IP address
- number of packets
- payload size
- packet transmission interval

The ICMP checksum is calculated manually and packets are identified using a custom payload identifier.

Example:

```bash
sudo python3 tecnicas/icmp_client_socket.py <server_ip> <packet_count> <payload_size>
```

Example:

```bash
sudo python3 tecnicas/icmp_client_socket.py 192.168.1.10 100 512
```

> Raw ICMP sockets require root privileges.

---

### OWAMP-style Unidirectional Measurement

The OWAMP-style implementation uses UDP packets to perform unidirectional latency measurements.

Each packet includes:

- sequence number
- transmission timestamp
- configurable payload

Example:

```bash
python3 tecnicas/owamp_client_simple.py <server_ip> <packet_count> <payload_size>
```

Example:

```bash
python3 tecnicas/owamp_client_simple.py 192.168.1.10 100 512
```

The implementation is designed for controlled experimentation rather than full RFC-compliant OWAMP interoperability.

---

### In-band Network Telemetry (INT)

The INT implementation is written in **P4_16** using the **v1model architecture**.

The programmable data plane captures telemetry information directly inside the switch pipeline.

The telemetry header contains:

| Field | Size |
|---|---:|
| Ingress timestamp | 48 bits |
| Egress timestamp | 48 bits |
| Packet size | 32 bits |

The egress P4 program creates telemetry reports using EtherType:

```text
0x88B9
```

Telemetry packets can then be collected and processed externally.

---

## Telemetry Collector

The collector is implemented in Python using **Scapy**.

It listens for INT telemetry packets and extracts:

```text
Ingress timestamp
Egress timestamp
Packet size
```

Latency is calculated as:

```text
latency = egress_timestamp - ingress_timestamp
```

Run the collector with:

```bash
sudo python3 Colector/collector.py --interface <interface> --offset <telemetry_offset>
```

Example:

```bash
sudo python3 Colector/collector.py --interface eth0 --offset 0
```

Collected measurements are written to:

```text
datos.txt
```

with a format similar to:

```text
tecnica:int, paquete:1, latencia:10.0000, payload:512
```

---

## Repository Structure

```text
telemetry/
│
├── Colector/
│   └── collector.py
│
├── P4/
│   ├── basic_int_source.p4
│   ├── basic_int_exit.p4
│   └── comanos_sw_bmv2.txt
│
└── tecnicas/
    ├── icmp_client_socket.py
    ├── icmp_server.py
    ├── owamp_client_simple.py
    └── owampd_server_simple.py
```

### `P4/`

Contains the programmable data-plane implementation for INT.

- `basic_int_source.p4`
  - packet parsing
  - UDP processing
  - ingress timestamp handling

- `basic_int_exit.p4`
  - ingress and egress timestamps
  - packet size collection
  - INT report generation
  - packet cloning/mirroring for telemetry export

### `tecnicas/`

Contains the host-based telemetry implementations.

- ICMP client/server
- UDP-based unidirectional latency measurement

### `Colector/`

Contains the INT telemetry collector implemented with Scapy.

---

## Technologies

| Technology | Purpose |
|---|---|
| Python 3 | Traffic generation and telemetry processing |
| Scapy | Packet capture and parsing |
| P4_16 | Programmable data-plane implementation |
| BMv2 | Software programmable switch |
| v1model | P4 target architecture |
| ICMP | Traditional active latency measurement |
| UDP | Unidirectional measurement transport |
| Linux | Experimental environment |
| Raw sockets | ICMP packet generation |

---

## Experimental Parameters

The framework allows experiments to vary:

- telemetry technique
- packet payload size
- packet count
- traffic rate

This makes it possible to compare the behavior of each technique under equivalent traffic conditions.

A typical experiment can evaluate latency for several packet sizes while maintaining the same topology and network path.

---

## Research Context

This repository was developed as part of research comparing traditional network telemetry techniques with programmable data-plane telemetry.

The objective is to evaluate:

- latency measurement behavior
- variability and stability
- sensitivity to packet payload size
- measurement resolution
- operational differences between host-based and in-network telemetry

The project specifically compares:

```text
ICMP vs OWAMP vs INT
```

with INT implemented directly in the programmable data plane.

---

## Key Design Difference

Traditional approaches:

```text
Host ---- Network ---- Host
  \_______measurement______/
```

INT approach:

```text
Host --> Programmable Switches --> Host
              |
              +--> telemetry generated inside the network
```

This allows INT to observe network behavior at the data-plane level instead of relying exclusively on end-host measurements.

---

## Requirements

### Python

```bash
python3
pip install scapy
```

### P4 environment

A P4 development environment supporting:

- P4_16
- BMv2
- `simple_switch`
- v1model

is required to compile and execute the INT programs.

---

## Notes

This repository contains experimental research code.

Some parameters such as:

- MAC addresses
- interfaces
- EtherTypes
- mirror session IDs
- network addresses

are currently defined for the original testbed and may need to be adapted before running the experiments in another environment.

---

## Author

**Andrés Felipe Osorio Henker**

Electronic Engineer  
M.Sc. Telecommunications Research  
Network Programmability · P4 · SDN · Network Telemetry

GitHub:  
https://github.com/aosorih

LinkedIn:  
https://www.linkedin.com/in/andres-felipe-osorio-henker
