import os
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "deco_agent"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )

def record_telemetry(
    entity_id: str,
    entity_type: str,
    lat: float,
    lon: float,
    altitude_m: float | None = None,
    metadata: dict | None = None,
):
    """
    Upserts master entity registry with the latest location fix and
    appends an immutable record to the spatial telemetry log.
    """
    if metadata is None:
        metadata = {}

    query_upsert_entity = """
        INSERT INTO entities (entity_id, entity_type, last_seen, last_location, metadata)
        VALUES (%s, %s, NOW(), ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s)
        ON CONFLICT (entity_id) DO UPDATE SET
            last_seen = NOW(),
            last_location = EXCLUDED.last_location,
            metadata = entities.metadata || EXCLUDED.metadata;
    """

    query_log = """
        INSERT INTO telemetry_log (entity_id, observed_at, geom, altitude_m, raw_payload)
        VALUES (%s, NOW(), ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s);
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            # PostGIS ST_MakePoint uses (longitude, latitude)
            cur.execute(query_upsert_entity, (entity_id, entity_type, lon, lat, Json(metadata)))
            cur.execute(query_log, (entity_id, lon, lat, altitude_m, Json(metadata)))
        conn.commit()

def find_entities_within_radius(lat: float, lon: float, radius_meters: float):
    """
    Executes a native PostGIS geodetic distance scan on EPSG:4326.
    """
    query = """
        SELECT 
            entity_id, 
            entity_type, 
            ST_Y(last_location::geometry) AS lat,
            ST_X(last_location::geometry) AS lon,
            ST_Distance(last_location, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) AS distance_meters,
            last_seen,
            metadata
        FROM entities
        WHERE ST_DWithin(last_location, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s)
        ORDER BY distance_meters ASC;
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (lon, lat, lon, lat, radius_meters))
            return cur.fetchall()