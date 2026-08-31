# The polite scraper

FlyRank Internship - Backend Track - Week 5 - Assignment A9.

This Python pipeline processes **exactly the first three catalogue pages** of Books to Scrape, discovers **60 unique book URLs**, visits all 60 detail pages, extracts raw fields, normalizes and validates the data, stores clean JSON, survives a deliberately broken page, and writes an honest run report.

## Target classification

- **Target:** Books to Scrape - `https://books.toscrape.com/`
- **Classification:** ToScrape explicitly describes Books to Scrape as a safe sandbox for learning web scraping and validating scraping technology. The catalogue also identifies itself as a demo website for web scraping.
- **Scope:** the first **3 catalogue pages only**: 20 books per page, 60 books total.
- **Collected data:** title, canonical product URL, price text, availability text, rating text, description when present, source catalogue page, fetch timestamp, and normalized GBP price.
- **robots.txt check:** `https://books.toscrape.com/robots.txt` returned **404 Not Found**, so **no robots file found**. A missing robots file is not permission; the target is appropriate because the site explicitly exists as a scraping sandbox.
- **Rule:** I will not reuse this code on another site without checking its rules and terms first.

## Python lane

- Requests for HTTP
- Beautiful Soup for HTML extraction
- Pydantic for schema validation
- Python built-in JSON module for output

## Install

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r scraper\requirements.txt
```

## Run

```powershell
cd scraper
..\.venv\Scripts\python.exe src\main.py
```

That command writes `output/books.json`, `output/errors.json`, and `output/run-report.json`.

## Record schema

Every detail page produces the eight required raw fields: `title`, `product_url`, `price_text`, `availability_text`, `rating_text`, `description`, `source_page`, and `fetched_at`. The validated record also adds numeric `price_gbp`.

The scraper keeps the corrected raw GBP text (for example `£51.77`) beside the normalized number (`51.77`). `description` is `null` when absent. Pydantic validates required fields, HTTPS URLs, the numeric price, the One-to-Five rating, and the timestamp. Invalid records go to `errors.json` with the reason and never enter `books.json`.

## Politeness rules

Every real request:

- sends the identifying user-agent `FlyRankInternship-A9/1.0 (+https://github.com/HaiderHumayon/task-api)`
- uses an 8-second timeout
- checks status before parsing
- waits at least 0.55 seconds between real requests
- caches successful HTML
- retries a timeout, connection error, or 5xx response once
- does not retry 403 or 404

Cached pages have no delay because they do not contact the site.

## Discovery and idempotency

The crawler follows the catalogue's own `next` link from page 1 to page 2 to page 3 and then stops. Relative links are converted with `urljoin`, and canonical product URLs remove duplicates.

A clean run and a rerun both produce exactly **60 records**, not 120.

## Failure isolation

Stage 5 adds one made-up book URL on our side. Its 404 response is logged and skipped without retrying, while all 60 real books survive.

### Failure-demo run report

```json
{
  "start_time": "2026-08-31T13:59:30.646068Z",
  "duration_seconds": 2.292,
  "catalogue_pages": 3,
  "discovered_urls": 60,
  "unique_urls": 60,
  "detail_pages_attempted": 61,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1,
  "failures": [
    {
      "url": "https://books.toscrape.com/catalogue/flyrank-a9-deliberately-missing-book/index.html",
      "status": 404,
      "error": "HTTP 404"
    }
  ]
}
```

## Real clean run report

```json
{
  "start_time": "2026-08-31T13:59:35.799952Z",
  "duration_seconds": 0.923,
  "catalogue_pages": 3,
  "discovered_urls": 60,
  "unique_urls": 60,
  "detail_pages_attempted": 60,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0,
  "failures": []
}
```

## Why no browser was needed

The required data is already present in the HTML returned by the server, so browser automation would add time and memory cost without providing additional data.

## Ethics

Use an official API when one exists. Never bypass logins, paywalls, robots directives, rate limits, or technical blocks. Collect only what is needed, identify automated requests honestly, and check a site's rules and terms before adapting this code to another target.

## Limitation

The selectors are specific to the Books to Scrape sandbox and may require an update if its HTML structure changes. The crawler intentionally stops after three catalogue pages instead of crawling the full catalogue.