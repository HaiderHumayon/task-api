from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "cache"
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/HaiderHumayon/task-api)"
TIMEOUT_SECONDS = 8
MIN_DELAY_SECONDS = 0.55
PAGE_1_URL = "https://books.toscrape.com/catalogue/page-1.html"


class FetchError(Exception):
    pass


class PoliteFetcher:
    def __init__(self) -> None:
        self.last_request_at = 0.0
        self.pages_fetched = 0
        self.cache_hits = 0

    def _wait(self) -> None:
        remaining = MIN_DELAY_SECONDS - (time.monotonic() - self.last_request_at)
        if remaining > 0:
            time.sleep(remaining)

    def fetch(self, url: str, cache_name: str) -> tuple[str, str]:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path = CACHE_DIR / cache_name
        meta_path = CACHE_DIR / f"{cache_name}.meta.json"

        if cache_path.exists():
            html = cache_path.read_text(encoding="utf-8")
            if meta_path.exists():
                fetched_at = json.loads(meta_path.read_text(encoding="utf-8"))["fetched_at"]
            else:
                fetched_at = datetime.fromtimestamp(
                    cache_path.stat().st_mtime, timezone.utc
                ).isoformat().replace("+00:00", "Z")
            self.cache_hits += 1
            print(f"CACHE HIT {url} bytes={len(html.encode('utf-8'))}")
            return html, fetched_at

        self._wait()
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
        )
        self.last_request_at = time.monotonic()

        if response.status_code != 200:
            raise FetchError(f"HTTP {response.status_code} for {url}")

        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        cache_path.write_text(response.text, encoding="utf-8")
        meta_path.write_text(
            json.dumps({"url": url, "fetched_at": fetched_at}, indent=2),
            encoding="utf-8",
        )
        self.pages_fetched += 1
        print(f"FETCH {url} status=200 bytes={len(response.content)}")
        return response.text, fetched_at


def discover_three_pages(fetcher: PoliteFetcher) -> list[dict[str, str]]:
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin

    page_url = PAGE_1_URL
    discovered: list[dict[str, str]] = []

    for page_number in range(1, 4):
        html, _ = fetcher.fetch(page_url, f"catalogue-page-{page_number}.html")
        soup = BeautifulSoup(html, "html.parser")

        for link in soup.select("article.product_pod h3 a[href]"):
            discovered.append({
                "product_url": urljoin(page_url, link["href"]),
                "source_page": page_url,
            })

        if page_number < 3:
            next_link = soup.select_one("li.next a[href]")
            if next_link is None:
                raise RuntimeError("Expected the catalogue next link.")
            page_url = urljoin(page_url, next_link["href"])

    unique: dict[str, dict[str, str]] = {}
    for item in discovered:
        unique.setdefault(item["product_url"], item)

    print(
        f"catalogue_pages=3 discovered={len(discovered)} "
        f"unique_urls={len(unique)}"
    )
    return list(unique.values())


def main() -> None:
    items = discover_three_pages(PoliteFetcher())
    if len(items) != 60:
        raise RuntimeError(f"Expected 60 unique URLs, found {len(items)}.")


if __name__ == "__main__":
    main()
