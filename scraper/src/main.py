from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, ValidationError, field_validator

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "cache"
OUTPUT_DIR = ROOT / "output"
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/HaiderHumayon/task-api)"
TIMEOUT_SECONDS = 8
MIN_DELAY_SECONDS = 0.55
PAGE_1_URL = "https://books.toscrape.com/catalogue/page-1.html"
RATINGS = {"One", "Two", "Three", "Four", "Five"}


class FetchError(Exception):
    pass


class BookRecord(BaseModel):
    title: str = Field(min_length=1)
    product_url: str
    price_text: str = Field(min_length=1)
    price_gbp: float = Field(ge=0)
    availability_text: str = Field(min_length=1)
    rating_text: Literal["One", "Two", "Three", "Four", "Five"]
    description: str | None
    source_page: str
    fetched_at: datetime

    @field_validator("product_url", "source_page")
    @classmethod
    def require_https(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("URL must be an absolute https:// URL")
        return value


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
            fetched_at = (
                json.loads(meta_path.read_text(encoding="utf-8"))["fetched_at"]
                if meta_path.exists()
                else datetime.fromtimestamp(
                    cache_path.stat().st_mtime, timezone.utc
                ).isoformat().replace("+00:00", "Z")
            )
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

        # Books to Scrape is UTF-8. Decode bytes explicitly so the pound sign
        # does not become the common mojibake sequence U+00C2 U+00A3.
        html = response.content.decode("utf-8")
        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        cache_path.write_text(html, encoding="utf-8")
        meta_path.write_text(
            json.dumps({"url": url, "fetched_at": fetched_at}, indent=2),
            encoding="utf-8",
        )
        self.pages_fetched += 1
        print(f"FETCH {url} status=200 bytes={len(response.content)}")
        return html, fetched_at


def repair_price_text(value: str) -> str:
    # Existing Stage 1-3 cache files were written after Requests guessed the
    # wrong encoding. Repair only that known decoding artifact while keeping
    # the scraped raw price value otherwise unchanged.
    return value.replace("\u00c2\u00a3", "\u00a3")


def detail_cache_name(product_url: str) -> str:
    digest = hashlib.sha256(product_url.encode("utf-8")).hexdigest()[:20]
    return f"book-{digest}.html"


def discover_three_pages(fetcher: PoliteFetcher) -> list[dict[str, str]]:
    page_url = PAGE_1_URL
    discovered = []

    for page_number in range(1, 4):
        html, _ = fetcher.fetch(page_url, f"catalogue-page-{page_number}.html")
        soup = BeautifulSoup(html, "html.parser")

        for link in soup.select("article.product_pod h3 a[href]"):
            discovered.append(
                {
                    "product_url": urljoin(page_url, link["href"]),
                    "source_page": page_url,
                }
            )

        if page_number < 3:
            next_link = soup.select_one("li.next a[href]")
            if next_link is None:
                raise RuntimeError("Expected catalogue next link")
            page_url = urljoin(page_url, next_link["href"])

    unique = {}
    for item in discovered:
        unique.setdefault(item["product_url"], item)

    print(
        f"catalogue_pages=3 discovered={len(discovered)} "
        f"unique_urls={len(unique)}"
    )
    return list(unique.values())


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
    soup = BeautifulSoup(html, "html.parser")
    product = soup.select_one("article.product_page")
    if product is None:
        raise ValueError("Missing article.product_page")

    rating_node = product.select_one(".product_main p.star-rating")
    if rating_node is None:
        raise ValueError("Missing rating")

    rating_text = next(
        (x for x in rating_node.get("class", []) if x in RATINGS),
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

    price_text = required_text(
        product.select_one(".product_main .price_color"),
        "price_text",
    )
    price_text = repair_price_text(price_text)

    return {
        "title": required_text(
            product.select_one(".product_main h1"), "title"
        ),
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": required_text(
            product.select_one(".product_main .availability"),
            "availability_text",
        ),
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }


def normalize_price(price_text: str) -> float:
    match = re.fullmatch(r"\u00a3(\d+(?:\.\d{2})?)", price_text.strip())
    if match is None:
        raise ValueError(f"Invalid GBP price: {price_text!r}")
    return float(match.group(1))


def validate_records(raw_records: list[dict]) -> tuple[list[dict], list[dict]]:
    unique = {}
    for raw in raw_records:
        unique.setdefault(raw["product_url"], raw)

    good = []
    errors = []

    for raw in unique.values():
        try:
            normalized = dict(raw)
            normalized["price_gbp"] = normalize_price(raw["price_text"])
            book = BookRecord.model_validate(normalized)
            good.append(book.model_dump(mode="json"))
        except (ValidationError, ValueError) as exc:
            errors.append({"record": raw, "reason": str(exc)})

    return good, errors


def write_json(filename: str, value) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / filename).write_text(
        json.dumps(value, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def run_once() -> tuple[list[dict], list[dict]]:
    fetcher = PoliteFetcher()
    items = discover_three_pages(fetcher)
    raw = []

    for item in items:
        html, fetched_at = fetcher.fetch(
            item["product_url"],
            detail_cache_name(item["product_url"]),
        )
        raw.append(
            extract_raw_record(
                html,
                item["product_url"],
                item["source_page"],
                fetched_at,
            )
        )

    good, errors = validate_records(raw)
    write_json("books.json", good)
    write_json("errors.json", errors)

    print(f"valid_records={len(good)} invalid_records={len(errors)}")
    return good, errors


def main() -> None:
    good, errors = run_once()
    if len(good) != 60 or errors:
        raise RuntimeError(
            f"Expected 60 valid and 0 invalid records; got "
            f"{len(good)} valid and {len(errors)} invalid."
        )


if __name__ == "__main__":
    main()
