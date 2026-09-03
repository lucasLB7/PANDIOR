from db_client import record_telemetry, find_entities_within_radius

# 1. Ingest two sample entities
record_telemetry(
    entity_id="sensor:nrb_base",
    entity_type="ground_station",
    lat=-1.286389,
    lon=36.817223,
    metadata={"status": "active", "band": "uhf"}
)

record_telemetry(
    entity_id="track:target_01",
    entity_type="mobile_unit",
    lat=-1.290000,
    lon=36.820000,
    altitude_m=1680.0,
    metadata={"heading": 142}
)

# 2. Query within 1000m of the base station
results = find_entities_within_radius(lat=-1.286389, lon=36.817223, radius_meters=1000)
print(f"Entities found within 1km: {len(results)}")
for r in results:
    print(f"-> {r['entity_id']} ({r['entity_type']}) at {r['distance_meters']:.1f}m away")