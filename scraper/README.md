# The polite scraper

FlyRank Internship — Backend Track — Week 5 — Assignment A9.

## Target classification

- **Target:** Books to Scrape — `https://books.toscrape.com/`
- **Why appropriate:** ToScrape explicitly describes Books to Scrape as a safe sandbox for beginners learning web scraping and for developers validating scraping technology. The catalogue itself also identifies the site as a demo website for web scraping.
- **Scope:** exactly the first **3 catalogue pages**, which contain 60 books.
- **Data collected:** title, canonical product URL, price text, availability text, rating text, description when present, source catalogue page, and fetch timestamp. A numeric GBP price is added after normalization.
- **robots.txt result:** `https://books.toscrape.com/robots.txt` returned **404 Not Found**, so **no robots file found**. A missing robots file is not permission; this target is appropriate because the site explicitly exists as a scraping sandbox.
- **Rule:** I will not reuse this code on another site without checking its rules and terms first.
