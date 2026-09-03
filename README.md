# 🛰️ PANDIOR

### Modular Geospatial Intelligence & Autonomous Agent Framework

PANDIOR is an edge-to-cloud intelligence operating system designed to ingest, normalize, and fuse heterogeneous sensor telemetry, spatial tracks, and open-source intelligence (OSINT) into a unified, actionable graph network.

---

## 🏗️ System Architecture

```text
       [ SENSOR TELEMETRY & OSINT FEEDS ]
  (ADS-B 1090MHz, LoRa/RF Links, GPS, Web Services)
                         │
                         ▼
             ┌───────────────────────┐
             │  Low-Bandwidth Triage │
             │  & Payload Normalizer │
             └───────────┬───────────┘
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
┌──────────────────┐          ┌───────────────────┐
│ PostGIS Storage  │          │   InMemoryGraph   │
│ (WGS84 Geodesic) │◄────────►│ Correlation Engine│
└─────────┬────────┘          └─────────┬─────────┘
          │                             │
          ▼                             ▼
   [ Spatial Radius &             [ Attributed Edge
     Proximity Scans ]              Persistence ]
```

---

## ⚡ Core Capabilities

### 1. High-Precision Geospatial Telemetry
- **Native Geodetic Tracking:** Ingests coordinates directly into WGS84 (`EPSG:4326`) space using PostGIS `GEOGRAPHY(Point)` to calculate true geodesic distances over the Earth's curvature.
- **Sub-Millisecond Proximity Scans:** GiST spatial indexing (`ST_DWithin`, `ST_Distance`) powers instantaneous radius searches, geofence verification, and proximity triggers.
- **Dual-State Spatial Model:**
  - `entities`: Master registry tracking the latest known position, status, and JSONB metadata.
  - `telemetry_log`: Append-only historical log capturing track altitude, time series, and raw payloads.

### 2. Relational Entity Graph Correlation
- **Attributed Graph Modeling:** Resolves physical platforms (vehicles, base stations, sensors) and digital identifiers into directed graph edges (`entity_relations`).
- **Dynamic Link Scoring:** Applies confidence metrics and temporal decay to evaluate evolving operational relationships.
- **Cross-Domain Fusion:** Fuses RF/telemetry hits with digital identifiers and OSINT context.

### 3. Edge-First & Low-Bandwidth Operations
- **Local-First Survivability:** Runs fully isolated without external cloud dependencies—optimized for field laptops, cyberdecks, or single-board computers.
- **Constrained-Network Triage:** Payload deduplication, delta compression, and priority scheduling built to operate across narrow RF pipelines (LoRa, packet radio).
- **Minimal Footprint:** Lean runtime profile (sub-10 core Python libraries, raw SQL/psycopg2 drivers) ensuring deterministic execution.

### 4. Multi-Source Intelligence & Agent Routing
- **Multi-Sensor Ingest:** Modular collectors for ADS-B tracking, RF sensor links, and environmental probes.
- **Semantic Query Router:** Routes queries across geospatial lookups, graph traversals, and scrapers.
- **API & UI Ready:** Built to expose low-latency REST and WebSocket feeds for dynamic operational interfaces (React/Vue/MapLibre GL).

---

## 🗄️ Relational Schema

- **`entities`**: Master entity registry (ID, type, last fix, GiST spatial index, GIN metadata index).
- **`telemetry_log`**: Immutable time-series observation log (ID, timestamp, coordinates, altitude, raw payload).
- **`entity_relations`**: Correlated directional graph edges (source, target, relation type, confidence score, attributes).

---

## 🚀 Quickstart

### 1. Environment & Setup
```powershell
# Activate runtime
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Ingestion Verification
```powershell
python test_ingest.py