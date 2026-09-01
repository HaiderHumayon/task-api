from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_DATABASE = ROOT / "report.db"


def get_report_data(database: Path = DEFAULT_DATABASE) -> dict[str, Any]:
    database = database.resolve()

    if not database.exists():
        raise FileNotFoundError(
            f"Database not found: {database}. Run seed.py first."
        )

    with sqlite3.connect(database) as connection:
        connection.row_factory = sqlite3.Row

        summary = connection.execute(
            """
            SELECT
                COUNT(*) AS total_books,
                ROUND(AVG(price), 2) AS average_price
            FROM books
            """
        ).fetchone()

        top_five = connection.execute(
            """
            SELECT
                title,
                price,
                rating,
                url
            FROM books
            ORDER BY price DESC, title ASC
            LIMIT 5
            """
        ).fetchall()

        rating_rows = connection.execute(
            """
            SELECT
                rating,
                COUNT(*) AS book_count
            FROM books
            GROUP BY rating
            ORDER BY rating ASC
            """
        ).fetchall()

        all_books = connection.execute(
            """
            SELECT
                id,
                title,
                price,
                rating,
                url
            FROM books
            ORDER BY price DESC, title ASC
            """
        ).fetchall()

    rating_counts = {
        int(row["rating"]): int(row["book_count"])
        for row in rating_rows
    }

    return {
        "total_books": int(summary["total_books"]),
        "average_price": float(summary["average_price"]),
        "top_five_expensive": [
            {
                "title": str(row["title"]),
                "price": float(row["price"]),
                "rating": int(row["rating"]),
                "url": str(row["url"]),
            }
            for row in top_five
        ],
        "rating_counts": rating_counts,
        "books": [
            {
                "id": int(row["id"]),
                "title": str(row["title"]),
                "price": float(row["price"]),
                "rating": int(row["rating"]),
                "url": str(row["url"]),
            }
            for row in all_books
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the PDF report aggregation queries."
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help="Path to report.db",
    )
    args = parser.parse_args()

    data = get_report_data(args.database)

    print(
        json.dumps(
            {
                "total_books": data["total_books"],
                "average_price": data["average_price"],
                "top_five_expensive": data["top_five_expensive"],
                "rating_counts": data["rating_counts"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()