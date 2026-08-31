from __future__ import annotations

import hashlib
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


RATINGS = {"One", "Two", "Three", "Four", "Five"}


def detail_cache_name(product_url: str) -> str:
    digest = hashlib.sha256(product_url.encode("utf-8")).hexdigest()[:20]
    return f"book-{digest}.html"


def required_text(node, field: str) -> str:
    if node is None:
        raise ValueError(f"Missing required field: {field}")
    value = node.get_text(" ", strip=True)
    if not value:
        raise ValueError(f"Empty required field: {field}")
    return value


def extract_raw_record(
    html: str,
    product_url: str,
    source_page: str,
    fetched_at: str,
) -> dict:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    product = soup.select_one("article.product_page")
    if product is None:
        raise ValueError("Missing article.product_page")

    rating_node = product.select_one(".product_main p.star-rating")
    if rating_node is None:
        raise ValueError("Missing rating")

    rating_text = next(
        (name for name in rating_node.get("class", []) if name in RATINGS),
        None,
    )
    if rating_text is None:
        raise ValueError("Unknown rating")

    description = None
    heading = soup.select_one("#product_description")
    if heading is not None:
        node = heading.find_next_sibling("p")
        if node is not None:
            description = node.get_text(" ", strip=True) or None

    return {
        "title": required_text(product.select_one(".product_main h1"), "title"),
        "product_url": product_url,
        "price_text": required_text(
            product.select_one(".product_main .price_color"), "price_text"
        ),
        "availability_text": required_text(
            product.select_one(".product_main .availability"),
            "availability_text",
        ),
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }


def main() -> None:
    fetcher = PoliteFetcher()
    items = discover_three_pages(fetcher)
    records = []

    for item in items:
        html, fetched_at = fetcher.fetch(
            item["product_url"],
            detail_cache_name(item["product_url"]),
        )
        records.append(
            extract_raw_record(
                html,
                item["product_url"],
                item["source_page"],
                fetched_at,
            )
        )

    if len(records) != 60:
        raise RuntimeError(f"Expected 60 detail records, got {len(records)}.")

    print(json.dumps(records[0], indent=2, ensure_ascii=False))
    print(f"detail_pages={len(records)}")


if __name__ == "__main__":
    main()
