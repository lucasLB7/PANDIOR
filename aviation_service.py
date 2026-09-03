import os
import requests
from dotenv import load_dotenv

load_dotenv()

AEROAPI_KEY = os.getenv("AEROAPI_KEY")
AEROAPI_BASE = "https://aeroapi.flightaware.com/aeroapi"
HEADERS = {"x-apikey": AEROAPI_KEY, "Accept": "application/json; charset=UTF-8"}

AIRPORT_MAP = {
    "JKIA": "HKJK",
    "NBO": "HKJK",
    "WILSON": "HKNW",
    "WIL": "HKNW",
    "MOMBASA": "HKMO",
    "MBA": "HKMO",
    "KISUMU": "HKKI",
    "KIS": "HKKI",
    "HEATHROW": "EGLL",
    "LHR": "EGLL",
    "DUBAI": "OMDB",
    "DXB": "OMDB",
}


def resolve_airport(code: str) -> str:
    cleaned = code.strip().upper()
    return AIRPORT_MAP.get(cleaned, cleaned)


def get_flight_status(flight_ident: str) -> list[dict]:
    """Retrieves real-time status, delays, and progress for a flight number or tail (e.g. 'KQ102', '5Y-KXP')."""
    if not AEROAPI_KEY:
        return [{"error": "AEROAPI_KEY not configured in .env"}]

    ident = flight_ident.strip().upper()
    url = f"{AEROAPI_BASE}/flights/{ident}"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json()
            flights = data.get("flights", [])
            if not flights:
                return [{"message": f"No active flights found for '{ident}'."}]

            results = []
            for leg in flights[:3]:
                dep_delay = round((leg.get("departure_delay") or 0) / 60)
                arr_delay = round((leg.get("arrival_delay") or 0) / 60)

                results.append({
                    "ident": leg.get("ident"),
                    "status": leg.get("status"),
                    "origin": (leg.get("origin") or {}).get("code_icao"),
                    "destination": (leg.get("destination") or {}).get("code_icao"),
                    "scheduled_out": leg.get("scheduled_out"),
                    "estimated_out": leg.get("estimated_out"),
                    "scheduled_in": leg.get("scheduled_in"),
                    "estimated_in": leg.get("estimated_in"),
                    "departure_delay_min": dep_delay,
                    "arrival_delay_min": arr_delay,
                    "aircraft_type": leg.get("aircraft_type"),
                })
            return results
        return [{"error": f"FlightAware API returned HTTP {res.status_code}"}]
    except Exception as e:
        return [{"error": f"Request failed: {e}"}]


def get_airport_arrivals(airport_code: str, max_results: int = 5) -> list[dict]:
    """Retrieves recent and upcoming scheduled arrivals, delays, and origin airports for an airport."""
    if not AEROAPI_KEY:
        return [{"error": "AEROAPI_KEY not configured in .env"}]

    icao = resolve_airport(airport_code)
    url = f"{AEROAPI_BASE}/airports/{icao}/flights/arrivals"
    params = {"max_pages": 1}

    try:
        res = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            arrivals = data.get("arrivals", [])
            if not arrivals:
                return [{"message": f"No arrival records found for airport '{icao}'."}]

            results = []
            for flight in arrivals[:max_results]:
                arr_delay = round((flight.get("arrival_delay") or 0) / 60)
                results.append({
                    "ident": flight.get("ident"),
                    "origin": (flight.get("origin") or {}).get("code_icao") or "Unknown",
                    "status": flight.get("status"),
                    "arrival_delay_min": arr_delay,
                    "scheduled_in": flight.get("scheduled_in"),
                    "estimated_in": flight.get("estimated_in") or flight.get("actual_in"),
                    "aircraft_type": flight.get("aircraft_type"),
                })
            return results
        return [{"error": f"FlightAware API returned HTTP {res.status_code}"}]
    except Exception as e:
        return [{"error": f"Request failed: {e}"}]