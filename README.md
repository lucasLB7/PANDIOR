# 🛰️ PANDIOR

### Modular Geospatial Intelligence & Autonomous Agent Framework

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![PostGIS](https://img.shields.io/badge/PostGIS-3.4+-2B7489?style=for-the-badge&logo=databricks&logoColor=white)](https://postgis.net/)
[![Architecture](https://img.shields.io/badge/Edge--Native-Cyberdeck%20%2F%20Dual--SBC-orange?style=for-the-badge)]()

PANDIOR is an edge-ready, local-first intelligence operating system designed to ingest, evaluate, and correlate multi-source spatiotemporal telemetry, digital OSINT feeds, and localized sensor networks. It merges PostGIS geodetic storage with dynamic in-memory graph correlation and a **Corrective Retrieval-Augmented Generation (CRAG)** reasoning core to yield actionable situational awareness under constrained environments.

---

## 🏗️ Operational & Pipeline Architecture

```text
       [ OPERATOR QUERY / SENSOR TELEMETRY ]
    (ADS-B 1090MHz, LoRa RF Links, GPS, OSINT Feeds)
                           │
                           ▼
                  [ query_router.py ]
          (Intent Routing & Service Dispatch)
           │               │               │
           ▼               ▼               ▼
     [ Aviation ]      [ Maps ]     [ OSINT / Wiki ]
     (Flight data)  (Overpass/OSM)  (Entities/Scraper)
           │               │               │
           └───────────────┼───────────────┘
                           ▼
                 [ semantic_filter.py ]
                 (CRAG Relevance Gate)
                  /                 \
       [ High Confidence ]     [ Low / Ambiguous ]
                │                       │
                │              [ Corrective Action ]
                │              (Trigger scraper.py /
                │               Fallback Refinement)
                │                       │
                └───────────┬───────────┘
                            ▼
                   [ main.py Agent ]
                (Synthesis & Reasoning)
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
    [ InMemoryGraphLinker ]     [ PostGIS Engine ]
     (Entity Association &       (WGS84 Geodesics &
     Confidence Edge Decay)      GiST Spatial Scans)
              │                           │
              └─────────────┬─────────────┘
                            ▼
               [ entity_relations (DB) ]
```

---

## ⚡ Comprehensive Feature Breakdown

### 1. High-Precision Geospatial Engine
- **Native Geodetic Coordinate Space:** Stores coordinates as `GEOGRAPHY(Point, 4326)` in PostgreSQL 18 with PostGIS, computing true spherical distances across the Earth's curvature.
- **Sub-Millisecond GiST Scans:** Employs spatial indexing to execute instantaneous radius queries (`ST_DWithin`), spherical distances (`ST_Distance`), and geofence boundary checks.
- **Bifurcated Temporal Architecture:**
  - `entities`: Dynamic master registry tracking latest known spatial fix, status, and GIN-indexed JSONB metadata.
  - `telemetry_log`: Immutable, append-only historical log tracking positional fixes, altitudes, velocities, timestamps, and raw payloads.

### 2. Corrective RAG (CRAG) Intelligence Pipeline
- **Deterministic Intent Routing (`query_router.py`):** Dispatches inbound requests across dedicated domain collectors (flight tracking, spatial mapping, structured OSINT, wiki retrieval).
- **Automated Relevance Grading (`semantic_filter.py`):** Evaluates retrieved operational context prior to model synthesis. Documents and records are scored to prevent hallucinated linkages.
- **Autonomous Corrective Fallback (`scraper.py`):** When retrieval confidence is ambiguous or insufficient, the pipeline triggers secondary targeted extractions to fill intelligence gaps before synthesis.
- **Decoupled Tool Matrix (`tools.py`):** Standalone interface hooks allowing the agent to dynamically query spatial bounds, inspect entity states, and fetch real-time data.

### 3. In-Memory Graph & Edge Persistence
- **Attributed Graph Modeling (`graph_linker.py`):** Represents vehicles, aircraft, base stations, and digital identities as nodes connected by directional, typed relationships (e.g., `observed_near`, `relayed_by`, `associated_with`).
- **Dynamic Link Scoring & Decay:** Weights operational relationships using temporal confidence scores, allowing intermittent or stale connections to gracefully decay.
- **Relational Persistence (`entity_relations`):** Commits correlated in-memory graph edges to PostgreSQL for long-term historical link analysis.

### 4. Edge-First Operations & Constrained Triage
- **Local-First Autonomy:** Fully functional off-grid with zero external cloud dependencies—designed for field laptops, embedded systems, and cyberdecks.
- **Telemetry Triage & Compression:** Implements delta encoding and priority queues to transmit essential spatial vectors across narrow RF links (LoRa, packet radio).
- **Minimal Dependency Footprint:** Relies on lean, deterministic libraries and raw database drivers (`psycopg2`) to optimize CPU and memory usage on embedded platforms.

---

## 🛰️ Future Roadmap: Multilayered Hardware Architecture

PANDIOR is being architected for direct deployment onto a ruggedized, multi-node edge field unit (Cyberdeck / Tactical Deployment Node) split across dedicated compute tiers:

```text
 ┌─────────────────────────────────────────────────────────────────┐
 │                ESP32-S3 SUPERVISOR SUBSYSTEM                    │
 │  - Power rail switching, battery state & bus health             │
 │  - Low-power wake, thermal control, watchdog heartbeat          │
 └──────────────┬───────────────────────────────────┬──────────────┘
                │ Serial / I2C Bus                  │ GPIO / Relays
                ▼                                   ▼
 ┌──────────────────────────────┐   ┌──────────────────────────────┐
 │       FRONTEND NODE          │   │        BACKEND NODE          │
 │   (Raspberry Pi 4 / 5)       │   │  (NVIDIA Jetson / Orin Nano) │
 ├──────────────────────────────┤   ├──────────────────────────────┤
 │ - Dynamic UI (MapLibre/React)│   │ - Local LLM / CRAG Engine    │
 │ - Operator Control Terminal  │◄─►│ - PostgreSQL 18 + PostGIS    │
 │ - ADS-B & SDR Interfacing    │   │ - In-Memory Graph Linker     │
 │ - Display Server / TUI       │   │ - Spatial Analysis Daemon    │
 └──────────────────────────────┘   └──────────────────────────────┘
```

### 1. Supervisory Layer (ESP32-S3)
- **Power Management & Telemetry:** Monitors input rails, battery charge levels, and system thermals.
- **Hardware Watchdog:** Provides hard-reset signaling, controlled power sequencing between frontend and backend, and low-power standby modes.
- **Peripheral Bridge:** Handles analog sensors, hardware status LEDs, and emergency bus disconnects.

### 2. Frontend Interface Node (Raspberry Pi)
- **Visualization & UI:** Renders low-latency operational dashboards, vector maps (MapLibre GL), and tactical heads-up interfaces.
- **Sensor Ingest Interface:** Connects directly to SDR receivers (ADS-B 1090 MHz, VHF/UHF), LoRa serial transceivers, and GPS modules.
- **Operator I/O:** Manages display drivers, mechanical pulse encoders, and peripheral keyboards.

### 3. Backend Analytical Core (NVIDIA Jetson / Orin)
- **CRAG & Local Inference:** Runs quantized local language models for real-time document grading, synthesis, and autonomous intent routing.
- **Spatial Data Core:** Hosts the PostgreSQL/PostGIS database instance, executing GiST spatial queries and logging historical telemetry.
- **Continuous Graph Correlator:** Runs the `InMemoryGraphLinker` background daemon to detect proximity patterns and sync to persistent storage.

---

## 🗄️ Relational Schema

```sql
-- Dynamic master registry
CREATE TABLE entities (
    entity_id VARCHAR(64) PRIMARY KEY,
    entity_type VARCHAR(32) NOT NULL,
    last_location GEOGRAPHY(Point, 4326),
    last_seen TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Append-only historical spatial track log
CREATE TABLE telemetry_log (
    log_id BIGSERIAL PRIMARY KEY,
    entity_id VARCHAR(64) REFERENCES entities(entity_id),
    geom GEOGRAPHY(Point, 4326) NOT NULL,
    altitude FLOAT,
    observed_at TIMESTAMPTZ NOT NULL,
    raw_payload JSONB DEFAULT '{}'::jsonb
);

-- Attributed graph edge table
CREATE TABLE entity_relations (
    source_id VARCHAR(64) REFERENCES entities(entity_id),
    target_id VARCHAR(64) REFERENCES entities(entity_id),
    relation_type VARCHAR(32) NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    attributes JSONB DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source_id, target_id, relation_type)
);
```

---

## 🚀 Quickstart & Setup

### 1. Environment Initialization
```powershell
# Activate local environment
.\venv\Scripts\Activate.ps1

# Install runtime dependencies
pip install -r requirements.txt
```

### 2. Configuration (`.env`)
```ini
DB_NAME=deco_agent
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### 3. Verify Telemetry & Spatial Ingestion
```powershell
python test_ingest.py
```

### 4. Run CRAG Agent & Query Pipeline
```powershell
python main.py
```