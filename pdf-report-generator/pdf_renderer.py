from __future__ import annotations

import argparse
import html
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

from report_data import DEFAULT_DATABASE, get_report_data


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "reports" / "test.pdf"


def money(value: float) -> str:
    return f"£{value:,.2f}"


def stars(rating: int) -> str:
    return "★" * rating + "☆" * (5 - rating)


def render_html(data: dict[str, Any]) -> str:
    generated_at = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    top_rows = "\n".join(
        f"""
        <tr>
          <td>{position}</td>
          <td>{html.escape(book["title"])}</td>
          <td class="money">{money(book["price"])}</td>
          <td>{stars(book["rating"])}</td>
        </tr>
        """
        for position, book in enumerate(
            data["top_five_expensive"],
            start=1,
        )
    )

    rating_rows = "\n".join(
        f"""
        <div class="rating-row">
          <span>{rating} star{"s" if rating != 1 else ""}</span>
          <strong>{data["rating_counts"].get(rating, 0)}</strong>
        </div>
        """
        for rating in range(1, 6)
    )

    book_rows = "\n".join(
        f"""
        <tr>
          <td>{book["id"]}</td>
          <td>{html.escape(book["title"])}</td>
          <td class="money">{money(book["price"])}</td>
          <td>{book["rating"]}</td>
          <td class="url">{html.escape(book["url"])}</td>
        </tr>
        """
        for book in data["books"]
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Bookstore Analytics Report</title>
  <style>
    @page {{
      size: A4;
      margin: 14mm 12mm 15mm;
    }}

    * {{
      box-sizing: border-box;
    }}

    html {{
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}

    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: #172033;
      background: #ffffff;
      font-size: 10.5px;
      line-height: 1.42;
    }}

    h1, h2, p {{
      margin-top: 0;
    }}

    .hero {{
      padding: 18px 20px;
      border-radius: 12px;
      background: linear-gradient(135deg, #172033, #34415f);
      color: #ffffff;
      margin-bottom: 14px;
    }}

    .hero h1 {{
      font-size: 25px;
      margin-bottom: 5px;
      letter-spacing: -0.3px;
    }}

    .hero p {{
      margin-bottom: 0;
      color: #e2e8f0;
    }}

    .section {{
      margin-top: 15px;
    }}

    .section h2 {{
      margin-bottom: 8px;
      font-size: 15px;
      color: #172033;
    }}

    .cards {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 9px;
      margin-bottom: 12px;
    }}

    .card {{
      padding: 13px;
      border: 1px solid #dce2ec;
      border-radius: 10px;
      background: #f7f9fc;
    }}

    .card .label {{
      color: #667085;
      font-size: 9px;
      text-transform: uppercase;
      letter-spacing: 0.6px;
    }}

    .card .value {{
      display: block;
      margin-top: 4px;
      font-size: 22px;
      font-weight: 700;
      color: #172033;
    }}

    .split {{
      display: grid;
      grid-template-columns: 1.55fr 0.75fr;
      gap: 12px;
      align-items: start;
    }}

    .panel {{
      border: 1px solid #dce2ec;
      border-radius: 10px;
      overflow: hidden;
    }}

    .panel-title {{
      padding: 9px 11px;
      background: #eef2f7;
      font-weight: 700;
      color: #344054;
    }}

    .rating-list {{
      padding: 7px 11px;
    }}

    .rating-row {{
      display: flex;
      justify-content: space-between;
      padding: 5px 0;
      border-bottom: 1px solid #edf0f5;
    }}

    .rating-row:last-child {{
      border-bottom: 0;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
    }}

    th {{
      background: #eef2f7;
      color: #344054;
      font-weight: 700;
      text-align: left;
      padding: 6px 7px;
      border-bottom: 1px solid #cfd7e5;
    }}

    td {{
      vertical-align: top;
      padding: 6px 7px;
      border-bottom: 1px solid #e4e8ef;
    }}

    tbody tr:nth-child(even) {{
      background: #fafbfc;
    }}

    thead {{
      display: table-header-group;
    }}

    tfoot {{
      display: table-footer-group;
    }}

    tr {{
      break-inside: avoid;
      page-break-inside: avoid;
    }}

    .money {{
      white-space: nowrap;
      font-variant-numeric: tabular-nums;
    }}

    .url {{
      font-size: 8px;
      color: #475467;
      word-break: break-all;
    }}

    .detail-table {{
      font-size: 8.7px;
    }}

    .detail-table th:nth-child(1),
    .detail-table td:nth-child(1) {{
      width: 6%;
    }}

    .detail-table th:nth-child(2),
    .detail-table td:nth-child(2) {{
      width: 34%;
    }}

    .detail-table th:nth-child(3),
    .detail-table td:nth-child(3) {{
      width: 12%;
    }}

    .detail-table th:nth-child(4),
    .detail-table td:nth-child(4) {{
      width: 9%;
    }}

    .detail-table th:nth-child(5),
    .detail-table td:nth-child(5) {{
      width: 39%;
    }}

    .footer-note {{
      margin-top: 9px;
      color: #667085;
      font-size: 8.5px;
    }}
  </style>
</head>
<body>
  <section class="hero">
    <h1>Bookstore Analytics Report</h1>
    <p>
      Generated from the local SQLite dataset · {generated_at}
    </p>
  </section>

  <section class="cards">
    <div class="card">
      <span class="label">Total books</span>
      <span class="value">{data["total_books"]}</span>
    </div>
    <div class="card">
      <span class="label">Average price</span>
      <span class="value">{money(data["average_price"])}</span>
    </div>
  </section>

  <section class="section split">
    <div class="panel">
      <div class="panel-title">Five most expensive books</div>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Title</th>
            <th>Price</th>
            <th>Rating</th>
          </tr>
        </thead>
        <tbody>
          {top_rows}
        </tbody>
      </table>
    </div>

    <div class="panel">
      <div class="panel-title">Rating distribution</div>
      <div class="rating-list">
        {rating_rows}
      </div>
    </div>
  </section>

  <section class="section">
    <h2>Complete 60-book dataset</h2>
    <table class="detail-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Title</th>
          <th>Price</th>
          <th>Rating</th>
          <th>Source URL</th>
        </tr>
      </thead>
      <tbody>
        {book_rows}
      </tbody>
    </table>
    <p class="footer-note">
      Rows use break-inside: avoid and the table header is configured
      as a repeating print header across PDF pages.
    </p>
  </section>
</body>
</html>
"""


def generate_pdf(
    output_path: Path = DEFAULT_OUTPUT,
    database: Path = DEFAULT_DATABASE,
    html_debug_path: Path | None = None,
) -> Path:
    data = get_report_data(database)
    report_html = render_html(data)

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if html_debug_path is not None:
        html_debug_path = html_debug_path.resolve()
        html_debug_path.parent.mkdir(parents=True, exist_ok=True)
        html_debug_path.write_text(
            report_html,
            encoding="utf-8",
        )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            page = browser.new_page()
            page.set_content(
                report_html,
                wait_until="load",
            )
            page.emulate_media(media="print")
            page.pdf(
                path=str(output_path),
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
            )
        finally:
            browser.close()

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render the SQLite bookstore report as a PDF."
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help="Path to report.db",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="PDF output path",
    )
    parser.add_argument(
        "--html-debug",
        type=Path,
        default=None,
        help="Optional path to save the generated HTML",
    )
    args = parser.parse_args()

    output = generate_pdf(
        output_path=args.output,
        database=args.database,
        html_debug_path=args.html_debug,
    )

    print(f"PDF created: {output}")
    print(f"Bytes: {output.stat().st_size}")


if __name__ == "__main__":
    main()