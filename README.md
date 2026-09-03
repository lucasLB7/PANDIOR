# 🛰️ PANDIOR

Modular Geospatial Intelligence & Autonomous Agent Framework.

## Overview

PANDIOR is a local-first, edge-ready platform for multi-source sensor telemetry ingestion, PostGIS geospatial indexing, and entity graph correlation.

`	ext
[ Telemetry Feeds ] ──► [ Spatial Ingestion ] ──► [ PostGIS (WGS84) ]
                               │                         ▲
                               ▼                         │
                      [ In-Memory Graph ] ─────────────┘
`

## Features

- **PostGIS Storage:** Native WGS84 point tracking with GiST spatial indexing.
- **Entity Tracking:** Master state (entities) and historical fixes (	elemetry_log).
- **Graph Correlation:** In-memory link discovery with edge persistence (entity_relations).
- **Minimal Footprint:** Lightweight dependency profile designed for field nodes.

## Quickstart

`powershell
# 1. Activate environment
.\venv\Scripts\Activate.ps1

# 2. Test ingestion
python test_ingest.py
`

## Database Schema

- entities: Master registry (ID, type, last location, metadata JSONB).
- 	elemetry_log: Immutable raw observation log with timestamps.
- entity_relations: Directed correlation graph edges with confidence weighting.
