import os
import re
import json
from typing import Dict
from urllib.parse import urljoin

import requests

BASE_URL = "https://www.realmeye.com"
DISCOVERY_PAGES = ("/", "/recent-deaths")
CACHED_URLS_PATH = "./images/sprite_urls.json"

# Fallback URLs if dynamic discovery fails.
FALLBACK_SPRITE_URLS = {
    "sheets.png": "https://www.realmeye.com/s/gu/img/sheets.png",
    "renders.png": "https://www.realmeye.com/s/gu/css/renders.png",
}

# Matches both absolute and relative links that end in sheets.png/renders.png.
SPRITE_LINK_PATTERN = re.compile(
    r"""(?P<url>https?://[^\s"'<>]+/(?:img|css)/(?:sheets|renders)\.png|/s/[^/"'<>\s]+/(?:img|css)/(?:sheets|renders)\.png)""",
    re.IGNORECASE,
)


def _extract_sprite_urls(html: str) -> Dict[str, str]:
    discovered: Dict[str, str] = {}

    for match in SPRITE_LINK_PATTERN.finditer(html):
        resolved_url = urljoin(BASE_URL, match.group("url"))
        file_name = os.path.basename(resolved_url.split("?", maxsplit=1)[0])
        if file_name in ("sheets.png", "renders.png"):
            discovered[file_name] = resolved_url

    return discovered


def _discover_sprite_urls(session: requests.Session) -> Dict[str, str]:
    discovered: Dict[str, str] = {}

    for page in DISCOVERY_PAGES:
        if len(discovered) == 2:
            break

        try:
            response = session.get(urljoin(BASE_URL, page), timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error discovering sprite URLs from {page}: {e}")
            continue

        discovered.update(_extract_sprite_urls(response.text))

    return discovered


def _load_cached_sprite_urls() -> Dict[str, str]:
    if not os.path.exists(CACHED_URLS_PATH):
        return {}

    try:
        with open(CACHED_URLS_PATH, "r", encoding="utf-8") as file:
            cached = json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}

    return {
        "sheets.png": cached.get("sheets.png"),
        "renders.png": cached.get("renders.png"),
    }


def _save_cached_sprite_urls(urls: Dict[str, str]) -> None:
    cache_data = {
        "sheets.png": urls.get("sheets.png"),
        "renders.png": urls.get("renders.png"),
    }

    with open(CACHED_URLS_PATH, "w", encoding="utf-8") as file:
        json.dump(cache_data, file)


def _download_image(session: requests.Session, url: str, file_name: str) -> None:
    response = session.get(url, stream=True, timeout=20)
    response.raise_for_status()

    with open(os.path.join("./images", file_name), "wb") as file:
        for chunk in response.iter_content(1024):
            if chunk:
                file.write(chunk)

    print(f"Image saved as {file_name} ({url})")


def Download_Images() -> None:
    os.makedirs("./images", exist_ok=True)

    with requests.Session() as session:
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/132.0.0.0 Safari/537.36"
                )
            }
        )

        discovered_urls = _discover_sprite_urls(session)
        cached_urls = _load_cached_sprite_urls()

        if discovered_urls:
            merged_cache = dict(cached_urls)
            merged_cache.update(discovered_urls)
            _save_cached_sprite_urls(merged_cache)
            cached_urls = merged_cache

        resolved_urls = {
            "sheets.png": discovered_urls.get(
                "sheets.png",
                cached_urls.get("sheets.png", FALLBACK_SPRITE_URLS["sheets.png"]),
            ),
            "renders.png": discovered_urls.get(
                "renders.png",
                cached_urls.get("renders.png", FALLBACK_SPRITE_URLS["renders.png"]),
            ),
        }

        for file_name, url in resolved_urls.items():
            if file_name not in discovered_urls:
                print(f"Using fallback URL for {file_name}: {url}")

            try:
                _download_image(session, url, file_name)
            except requests.exceptions.RequestException as e:
                print(f"Error downloading image: {e}, {file_name}")
            except Exception as e:
                print(f"An error occurred: {e}, {file_name}")
