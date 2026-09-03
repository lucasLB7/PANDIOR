import requests

HEADERS = {
    "User-Agent": "ResearchAgent/1.0 (https://github.com/example; contact@example.com)"
}

def search_wikipedia(query: str, limit: int = 3) -> list[dict]:
    """Searches Wikipedia and returns top matching article titles and descriptions."""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "opensearch",
        "search": query,
        "limit": limit,
        "namespace": 0,
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            titles = data[1]
            descriptions = data[2]
            urls = data[3]
            
            results = []
            for t, d, u in zip(titles, descriptions, urls):
                results.append({
                    "title": t,
                    "description": d,
                    "url": u
                })
            return results
    except Exception as e:
        print(f"  [!] Wikipedia search error: {e}")
        
    return []

def get_article_summary(title: str) -> str:
    """Fetches the lead extract/summary of a specific Wikipedia article."""
    formatted_title = title.replace(" ", "_")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{formatted_title}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("extract", "No extract found for this article.")
        elif response.status_code == 404:
            return f"Article '{title}' was not found on Wikipedia."
    except Exception as e:
        return f"Error retrieving article summary: {e}"
        
    return "Failed to fetch content from Wikipedia."