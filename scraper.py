import time
import warnings
import requests
import urllib3
from bs4 import BeautifulSoup

# Suppress the package rename deprecation warning and SSL warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

# ---------------------------------------------------------
# 1. STATIC PORTAL SCRAPER
# ---------------------------------------------------------
def fetch_construction_leads() -> list[dict]:
    leads: list[dict] = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    target_sources = [
        {
            "name": "Construction Kenya (Projects)",
            "url": "https://www.constructionkenya.com/projects/",
            "article_tag": "article",
            "title_tags": ["h2", "h3"],
            "summary_selectors": ["div.entry-content", "p"],
        },
        {
            "name": "Africa Property News",
            "url": "https://www.africapropertynews.com/east-africa.html",
            "article_tag": "div",
            "class_name": "catItemView",
            "title_tags": ["h3"],
            "summary_selectors": ["div.catItemIntroText", "p"],
        },
    ]

    for source in target_sources:
        print(f"🌐 Scraping Portal: {source['name']}...")
        try:
            response = requests.get(
                str(source["url"]), headers=headers, timeout=15, verify=False
            )
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                if "class_name" in source:
                    articles = soup.find_all(
                        source["article_tag"],
                        class_=source["class_name"],
                        limit=2,
                    )
                else:
                    articles = soup.find_all(source["article_tag"], limit=2)

                for article in articles:
                    title_elem = article.find(source["title_tags"])
                    title = title_elem.get_text(strip=True) if title_elem else ""

                    summary = ""
                    for selector in source.get("summary_selectors", []):
                        summary_elem = article.select_one(selector)
                        if summary_elem:
                            summary = summary_elem.get_text(strip=True)
                            if summary:
                                break

                    if title and len(title) > 10:
                        leads.append({
                            "source": str(source["name"]),
                            "headline": title,
                            "raw_text": f"Source: {source['name']}\nHeadline: {title}\nDetails: {summary}",
                        })
        except Exception as e:
            print(f"  [!] Connection error for {source['name']}: {e}")

        time.sleep(2)

    return leads


# ---------------------------------------------------------
# 2. DYNAMIC SEARCH ENGINE CRAWLER (DDGS)
# ---------------------------------------------------------
def search_dynamic_leads(
    queries: list[str], max_results_per_query: int = 2
) -> list[dict]:
    leads: list[dict] = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    with DDGS() as ddgs:
        for query in queries:
            print(f"🔍 Searching Web: '{query}'...")
            try:
                search_results = list(
                    ddgs.text(query, max_results=max_results_per_query)
                )

                for result in search_results:
                    if not isinstance(result, dict):
                        continue

                    url = str(result.get("href") or "")
                    title = str(result.get("title") or "")
                    snippet = str(result.get("body") or "")

                    if not url or not url.startswith("http"):
                        continue

                    try:
                        page_response = requests.get(
                            url, headers=headers, timeout=10, verify=False
                        )
                        if page_response.status_code == 200:
                            soup = BeautifulSoup(page_response.text, "html.parser")
                            paragraphs = soup.find_all("p")
                            full_text = " ".join(
                                [p.get_text(strip=True) for p in paragraphs[:5]]
                            )

                            leads.append({
                                "source": f"Search: {query}",
                                "headline": title,
                                "raw_text": f"Title: {title}\nURL: {url}\nSnippet: {snippet}\nContent: {full_text}",
                            })
                    except Exception:
                        pass

                    time.sleep(1)

            except Exception as e:
                print(f"  [!] Search failed for query '{query}': {e}")

    return leads