import os
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
BASE_URL = "https://maps.googleapis.com/maps/api"


def geocode_place(address: str) -> dict:
    """Translates a place name or address into exact coordinates and formatted address."""
    if not GOOGLE_MAPS_API_KEY:
        return {"error": "GOOGLE_MAPS_API_KEY not configured in .env"}

    url = f"{BASE_URL}/geocode/json"
    params = {"address": address, "key": GOOGLE_MAPS_API_KEY}

    try:
        res = requests.get(url, params=params, timeout=8).json()
        if res.get("status") == "OK" and res.get("results"):
            top = res["results"][0]
            loc = top["geometry"]["location"]
            return {
                "formatted_address": top.get("formatted_address"),
                "lat": loc.get("lat"),
                "lng": loc.get("lng"),
                "place_id": top.get("place_id"),
            }
        return {"error": f"Geocoding failed with status: {res.get('status')}"}
    except Exception as exc:
        return {"error": f"Geocoding request error: {exc}"}


def calculate_travel_matrix(origin: str, destination: str, mode: str = "driving") -> dict:
    """Calculates real-time transit distance, standard duration, and live traffic duration."""
    if not GOOGLE_MAPS_API_KEY:
        return {"error": "GOOGLE_MAPS_API_KEY not configured in .env"}

    url = f"{BASE_URL}/distancematrix/json"
    params = {
        "origins": origin,
        "destinations": destination,
        "mode": mode,
        "departure_time": "now",
        "key": GOOGLE_MAPS_API_KEY,
    }

    try:
        res = requests.get(url, params=params, timeout=8).json()
        if res.get("status") == "OK":
            element = res["rows"][0]["elements"][0]
            if element.get("status") == "OK":
                duration_traffic = element.get("duration_in_traffic", element.get("duration", {}))
                return {
                    "origin": res.get("origin_addresses", [origin])[0],
                    "destination": res.get("destination_addresses", [destination])[0],
                    "distance": element.get("distance", {}).get("text"),
                    "typical_duration": element.get("duration", {}).get("text"),
                    "live_duration_in_traffic": duration_traffic.get("text"),
                }
            return {"error": f"Route element error: {element.get('status')}"}
        return {"error": f"Distance Matrix failed with status: {res.get('status')}"}
    except Exception as exc:
        return {"error": f"Matrix request error: {exc}"}


def search_google_places(query: str) -> list[dict]:
    """Finds physical landmarks, facilities, developments, and businesses."""
    if not GOOGLE_MAPS_API_KEY:
        return [{"error": "GOOGLE_MAPS_API_KEY not configured in .env"}]

    url = f"{BASE_URL}/place/textsearch/json"
    params = {"query": query, "key": GOOGLE_MAPS_API_KEY}

    try:
        res = requests.get(url, params=params, timeout=8).json()
        if res.get("status") == "OK":
            places = []
            for place in res.get("results", [])[:3]:
                places.append({
                    "name": place.get("name"),
                    "address": place.get("formatted_address"),
                    "coordinates": place.get("geometry", {}).get("location"),
                    "rating": place.get("rating"),
                    "user_ratings_total": place.get("user_ratings_total"),
                })
            return places
        return [{"error": f"Places API failed with status: {res.get('status')}"}]
    except Exception as exc:
        return [{"error": f"Places request error: {exc}"}]