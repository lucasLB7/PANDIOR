import socket
import requests

PLATFORMS = {
    "github": "https://github.com/{}",
    "reddit": "https://www.reddit.com/user/{}",
    "keybase": "https://keybase.io/{}",
}


def run_dns_recon(domain: str) -> dict:
    """Resolves DNS host IP addresses for infrastructure recon."""
    cleaned_domain = (
        domain.strip()
        .replace("http://", "")
        .replace("https://", "")
        .split("/")[0]
    )
    try:
        ip = socket.gethostbyname(cleaned_domain)
        return {"domain": cleaned_domain, "resolved_ip": ip, "status": "active"}
    except Exception as e:
        return {"domain": cleaned_domain, "error": str(e)}


def check_username_footprint(username: str) -> list[dict]:
    """Checks public platforms for active profiles matching a handle."""
    results = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for platform, url_tpl in PLATFORMS.items():
        url = url_tpl.format(username.strip())
        try:
            r = requests.head(
                url, timeout=4, headers=headers, allow_redirects=True
            )
            if r.status_code == 200:
                results.append(
                    {"platform": platform, "profile_url": url, "found": True}
                )
        except Exception:
            pass
    return results