import re

INTENT_MAP = {
    "coding": {
        "keywords": ["error", "exception", "traceback", "debug", "python", "syntax", "pip", "npm", "docker", "json", "api"],
        "allowed_tools": ["search_stackoverflow", "search_web"],
    },
    "construction": {
        "keywords": ["construction", "building", "real estate", "contractor", "tenders", "developer", "property", "roads"],
        "allowed_tools": ["fetch_construction_portals", "search_web"],
    },
    "factual": {
        "keywords": ["what is", "history of", "who was", "definition", "origin", "meaning", "explain"],
        "allowed_tools": ["search_wikipedia", "get_article_summary"],
    },
    "recent_news": {
        "keywords": ["latest", "recent", "breaking", "update", "current", "news", "today"],
        "allowed_tools": ["search_web"],
    },
    "aviation": {
        "keywords": ["flight", "aircraft", "plane", "icao", "tail number", "transponder", "airport", "arrival", "departure", "adsb", "landed", "jkia", "airline"],
        "allowed_tools": ["get_flight_status", "get_airport_arrivals", "search_web"],
    },
    "cyber_recon": {
        "keywords": ["domain", "ip address", "dns", "whois", "nameserver", "host", "subdomain", "ssl cert", "reverse ip", "asn"],
        "allowed_tools": ["run_dns_recon", "search_web"],
    },
    "people_profiling": {
        "keywords": ["username", "handle", "profile", "identity", "alias", "footprint", "social media", "pseudonym"],
        "allowed_tools": ["check_username_footprint", "search_web"],
    },
    "maritime": {
        "keywords": ["vessel", "ship", "tanker", "cargo", "mmsi", "imo", "port", "anchorage", "ais"],
        "allowed_tools": ["search_web"],
    },
    "orbital": {
        "keywords": ["satellite", "norad", "orbit", "tle", "cospar", "spacecraft", "iss"],
        "allowed_tools": ["search_web"],
    },
    "vehicles": {
        "keywords": ["plate", "numberplate", "chassis", "vin", "registration", "car", "vehicle"],
        "allowed_tools": ["search_web"],
    },
    "geospatial": {
        "keywords": [
            "route",
            "route from",
            "best route",
            "fastest route",
            "how long",
            "how long will it take",
            "how far",
            "distance",
            "drive",
            "driving",
            "traffic",
            "travel time",
            "eta",
            "directions",
            "road trip",
            "kph",
            "mph",
            "fuel station",
            "petrol station",
            "rest stop",
        ],
        "allowed_tools": [
            "calculate_travel_matrix",
            "search_google_places",
            "geocode_place",
            "search_web",
        ],
    },
}

# High-precision entity formats to trigger domains even if keywords are missing
ENTITY_PATTERNS = {
    "aviation": [
        r"\b([A-Z]{2,3}|[A-Z][0-9]|[0-9][A-Z])\s?\d{1,4}\b",  # IATA/ICAO: KQ116, 5Y102, BAW65
        r"\b(?:icao24|transponder)\s*[:#]?\s*([0-9a-fA-F]{6})\b",
    ],
    "cyber_recon": [
        r"\b(?:[a-zA-Z0-9-]+\.)+(?:com|org|net|io|ke|co\.ke|gov|edu)\b",  # Domains
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",  # IPv4
    ],
    "maritime": [
        r"(?i)\bIMO\s?[1-9]\d{6}\b",  # IMO numbers
        r"(?i)\b(?:mmsi\s*[:#]?\s*)?([2-7]\d{8})\b",  # MMSI numbers
    ],
    "orbital": [
        r"\b(19|20)\d{2}-\d{3}[A-Z]{1,3}\b",  # COSPAR ID
        r"(?i)\b(?:norad|satcat|satellite)\s*#?:?\s*(\d{5})\b",  # NORAD Cat ID
    ],
    "vehicles": [
        r"(?i)\bK[A-Z]{2}\s?\d{3}[A-Z]\b",  # Kenyan plates (e.g., KDA 123A)
        r"\b[A-HJ-NPR-Z0-9]{17}\b",  # Standard 17-character VIN
    ],
}


def get_filtered_tool_schemas(query: str, all_schemas: list[dict]) -> list[dict]:
    """Single-pass router evaluating both semantic keywords and structural regex signatures."""
    allowed_names: set[str] = set()

    # Pass 1: Semantic Keyword Matching
    for intent, config in INTENT_MAP.items():
        for kw in config["keywords"]:
            if re.search(rf"\b{re.escape(kw)}\b", query, re.IGNORECASE):
                allowed_names.update(config["allowed_tools"])
                break

    # Pass 2: Structural Entity Regex Matching
    for intent, patterns in ENTITY_PATTERNS.items():
        if any(re.search(pat, query) for pat in patterns):
            if intent in INTENT_MAP:
                allowed_names.update(INTENT_MAP[intent]["allowed_tools"])

    # Fallback to general open discovery
    if not allowed_names:
        allowed_names = {"search_web", "search_wikipedia"}

    return [s for s in all_schemas if s["function"]["name"] in allowed_names]