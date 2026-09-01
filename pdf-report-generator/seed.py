from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_DATABASE = ROOT / "report.db"
DEFAULT_SOURCE = ROOT.parent / "scraper" / "output" / "books.json"

RATING_TO_NUMBER = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def load_books(source: Path) -> list[dict[str, Any]]:
    with source.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    if not isinstance(raw, list):
        raise ValueError("books.json must contain a JSON array")

    if len(raw) != 60:
        raise ValueError(
            f"Expected exactly 60 validated books, found {len(raw)}"
        )

    normalized: list[dict[str, Any]] = []

    for index, book in enumerate(raw, start=1):
        if not isinstance(book, dict):
            raise ValueError(f"Book #{index} is not a JSON object")

        title = book.get("title")
        price = book.get("price_gbp")
        rating_text = book.get("rating_text")
        url = book.get("product_url")

        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"Book #{index} has an invalid title")

        if not isinstance(price, (int, float)):
            raise ValueError(f"Book #{index} has an invalid price")

        if rating_text not in RATING_TO_NUMBER:
            raise ValueError(
                f"Book #{index} has unsupported rating {rating_text!r}"
            )

        if not isinstance(url, str) or not url.startswith("https://"):
            raise ValueError(f"Book #{index} has an invalid URL")

        normalized.append(
            {
                "title": title.strip(),
                "price": float(price),
                "rating": RATING_TO_NUMBER[rating_text],
                "url": url,
            }
        )

    unique_urls = {book["url"] for book in normalized}

    if len(unique_urls) != 60:
        raise ValueError(
            f"Expected 60 unique book URLs, found {len(unique_urls)}"
        )

    return normalized


def initialize_database(
    database: Path,
    books: list[dict[str, Any]],
) -> int:
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                price REAL NOT NULL CHECK(price >= 0),
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                url TEXT NOT NULL UNIQUE
            )
            """
        )

        # Safe to run repeatedly: remove the previous development seed
        # before inserting the current clean copy.
        connection.execute("DELETE FROM books")
        connection.execute(
            "DELETE FROM sqlite_sequence WHERE name = 'books'"
        )

        connection.executemany(
            """
            INSERT INTO books (title, price, rating, url)
            VALUES (:title, :price, :rating, :url)
            """,
            books,
        )

        row_count = connection.execute(
            "SELECT COUNT(*) FROM books"
        ).fetchone()[0]

        connection.commit()

    return int(row_count)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed report.db from the validated bookstore JSON."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Path to books.json",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help="Path to report.db",
    )
    args = parser.parse_args()

    source = args.source.resolve()
    database = args.database.resolve()

    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    books = load_books(source)
    row_count = initialize_database(database, books)

    print(f"Source: {source}")
    print(f"Database: {database}")
    print(f"SELECT COUNT(*) FROM books -> {row_count}")


if __name__ == "__main__":
    main()