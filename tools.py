import json
import os
import requests
from dotenv import load_dotenv

from aviation_service import (
    get_airport_arrivals,
    get_flight_status,
)
from maps_service import calculate_travel_matrix, geocode_place, search_google_places
from osint_service import check_username_footprint, run_dns_recon
from scraper import fetch_construction_leads, search_dynamic_leads
from semantic_filter import filter_relevant_records
from wiki_service import get_article_summary, search_wikipedia

# Load environment variables
load_dotenv()
STACK_KEY = os.getenv("STACK_EXCHANGE_KEY")
STACK_EXCHANGE_API = "https://api.stackexchange.com/2.3/search/advanced"


# ---------------------------------------------------------
# 1. CORE TOOL IMPLEMENTATIONS
# ---------------------------------------------------------
def search_stackoverflow(
    query: str, tagged: str | None = None, max_results: int = 2
) -> list[dict]:
    """Queries Stack Overflow REST API for questions and accepted answers."""
    params = {
        "order": "desc",
        "sort": "relevance",
        "q": query,
        "site": "stackoverflow",
        "filter": "!9_bDDx6aq",
        "pagesize": max_results,
    }

    if STACK_KEY:
        params["key"] = STACK_KEY

    if tagged:
        params["tagged"] = tagged

    headers = {"User-Agent": "ResearchAgent/1.0"}

    try:
        response = requests.get(
            STACK_EXCHANGE_API, params=params, headers=headers, timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "score": item.get("score"),
                    "is_answered": item.get("is_answered"),
                    "tags": item.get("tags", []),
                    "excerpt": item.get("body_markdown")
                    or item.get("body", "No body available")[:1000],
                })
            return results
    except Exception as e:
        print(f"  [!] Stack Overflow API search error: {e}")

    return []


# ---------------------------------------------------------
# 2. TOOL RUNNER WRAPPERS
# ---------------------------------------------------------
def run_search_wikipedia(query: str) -> str:
    print(f"  🔍 [Tool: Wikipedia Search] Query: '{query}'")
    results = search_wikipedia(query)
    return json.dumps(results)


def run_get_article_summary(title: str) -> str:
    print(f"  📖 [Tool: Read Article] Title: '{title}'")
    content = get_article_summary(title)
    return json.dumps({"title": title, "content": content})


def run_search_web(query: str, max_results: int = 3) -> str:
    print(f"  🌐 [Tool: Web Search] Query: '{query}'")
    results = search_dynamic_leads([query], max_results_per_query=max_results)
    pruned = filter_relevant_records(query, results, threshold=0.38)
    return json.dumps(pruned)


def run_search_stackoverflow(
    query: str, tag: str | None = None, max_results: int = 2
) -> str:
    print(
        f"  💻 [Tool: Stack Overflow] Query: '{query}'"
        + (f" | Tag: {tag}" if tag else "")
    )
    results = search_stackoverflow(query, tagged=tag, max_results=max_results)
    return json.dumps(results)


def run_fetch_construction_portals(
    query: str = "East Africa construction tenders real estate",
) -> str:
    print("  🏗️ [Tool: Construction Portals] Scraping direct feeds...")
    results = fetch_construction_leads()
    pruned = filter_relevant_records(query, results, threshold=0.35)
    return json.dumps(pruned)


def run_get_flight_status(flight_ident: str) -> str:
    print(f"  ✈️ [Tool: Flight Status] Ident: '{flight_ident}'")
    results = get_flight_status(flight_ident)
    return json.dumps(results)


def run_get_airport_arrivals(airport_code: str, max_results: int = 5) -> str:
    print(f"  🛬 [Tool: Airport Arrivals] Airport: '{airport_code}'")
    results = get_airport_arrivals(airport_code, max_results=max_results)
    return json.dumps(results)


def run_tool_dns_recon(domain: str) -> str:
    print(f"  🌐 [Tool: DNS Recon] Domain: '{domain}'")
    return json.dumps(run_dns_recon(domain))


def run_tool_username_footprint(username: str) -> str:
    print(f"  👤 [Tool: Username Check] Target: '{username}'")
    return json.dumps(check_username_footprint(username))


def run_calculate_travel_matrix(
    origin: str, destination: str, mode: str = "driving"
) -> str:
    print(f"  🚗 [Tool: Travel Matrix] '{origin}' -> '{destination}' ({mode})")
    res = calculate_travel_matrix(origin, destination, mode)
    return json.dumps(res)


def run_search_google_places(query: str) -> str:
    print(f"  📍 [Tool: Google Places] Query: '{query}'")
    res = search_google_places(query)
    return json.dumps(res)


def run_geocode_place(address: str) -> str:
    print(f"  🌍 [Tool: Geocoding] Address: '{address}'")
    res = geocode_place(address)
    return json.dumps(res)


# ---------------------------------------------------------
# 3. TOOL REGISTRY & FUNCTION SCHEMAS
# ---------------------------------------------------------
AVAILABLE_TOOLS = {
    "search_wikipedia": run_search_wikipedia,
    "get_article_summary": run_get_article_summary,
    "search_web": run_search_web,
    "search_stackoverflow": run_search_stackoverflow,
    "fetch_construction_portals": run_fetch_construction_portals,
    "get_flight_status": run_get_flight_status,
    "get_airport_arrivals": run_get_airport_arrivals,
    "run_dns_recon": run_tool_dns_recon,
    "check_username_footprint": run_tool_username_footprint,
    "calculate_travel_matrix": run_calculate_travel_matrix,
    "search_google_places": run_search_google_places,
    "geocode_place": run_geocode_place,
}

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "search_wikipedia",
            "description": "Search Wikipedia for articles matching general concepts, historical background, or foundational topics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up on Wikipedia.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_article_summary",
            "description": "Fetch the extract/summary of a specific Wikipedia article by exact title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The exact title of the Wikipedia page.",
                    }
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Perform live DuckDuckGo web searches and scrape resulting page contents. Use for recent news, coding bugs, current data, or specific queries not covered by Wikipedia.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Specific web search keywords or question.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of search results to fetch (default: 3).",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_stackoverflow",
            "description": "Search Stack Overflow for programming solutions, debugging error logs, software libraries, and code implementations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The programming question, function name, or error trace.",
                    },
                    "tag": {
                        "type": "string",
                        "description": "Optional specific language or framework tag (e.g., 'python', 'c++', 'arduino', 'onnx').",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of Q&A threads to retrieve (default: 2).",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_construction_portals",
            "description": "Directly scrape live construction and property development portal feeds in East Africa.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional focus query to filter the scraped leads (defaults to general construction).",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_flight_status",
            "description": "Get real-time flight status, delay minutes, gate times, and progress for a flight number or tail registration (e.g. 'KQ102', 'BA65', '5Y-KXP').",
            "parameters": {
                "type": "object",
                "properties": {
                    "flight_ident": {
                        "type": "string",
                        "description": "Flight callsign, flight number, or registration (e.g., 'KQ102', 'ET308').",
                    }
                },
                "required": ["flight_ident"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_airport_arrivals",
            "description": "Retrieve recent and upcoming scheduled arrivals, delay minutes, and status for an airport (e.g. 'HKJK', 'JKIA', 'LHR').",
            "parameters": {
                "type": "object",
                "properties": {
                    "airport_code": {
                        "type": "string",
                        "description": "Airport ICAO or IATA code (e.g., 'JKIA', 'HKJK').",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of arrivals to return (default: 5).",
                    },
                },
                "required": ["airport_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_dns_recon",
            "description": "Resolve a web domain to its underlying host IP address for digital infrastructure intelligence.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "The root domain or hostname (e.g. 'example.com').",
                    }
                },
                "required": ["domain"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_username_footprint",
            "description": "Scan open social and developer platforms to see if an online handle or alias is active.",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "The exact username/handle to investigate.",
                    }
                },
                "required": ["username"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_travel_matrix",
            "description": "Calculate driving distance, standard time, and current live traffic travel duration between two locations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Starting address, airport, landmark, or coordinates.",
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination address, airport, landmark, or coordinates.",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["driving", "walking", "transit", "bicycling"],
                        "default": "driving",
                        "description": "Mode of transport.",
                    },
                },
                "required": ["origin", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_google_places",
            "description": "Search physical places, businesses, facilities, and landmarks to get exact addresses, ratings, and coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Place, landmark, or business name to locate.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "geocode_place",
            "description": "Resolve an address or geographic name directly to latitude and longitude coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Physical address, city, or landmark name.",
                    }
                },
                "required": ["address"],
            },
        },
    },
]