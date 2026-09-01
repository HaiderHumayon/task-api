# PDF Report Generator

FlyRank Internship — Backend Track — Assignment A8.

This assignment builds a synchronous data-to-document pipeline:

```text
SQLite data -> SQL aggregation -> HTML -> PDF -> file link
```

The Python lane uses FastAPI, Python's built-in `sqlite3`, and Playwright with headless Chromium.

The project uses the bookstore dataset option: 60 validated book records are seeded into a local SQLite database in Stage 1.

## Stage 0

Stage 0 provides:

- `GET /health`
- FastAPI on port 8000
- Playwright installed
- Chromium installed for PDF rendering

Run the API from this folder:

```powershell
$env:PYTHONUTF8="1"
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

Health check:

```powershell
curl.exe -i http://localhost:8000/health
```

Expected body:

```json
{"status":"ok"}
```

Later stages add SQLite seeding, aggregation queries, HTML-to-PDF rendering, report records, download links, and once-per-day idempotency.
## Stage 1 - Data worth reporting on

This project uses the bookstore dataset from `../scraper/output/books.json`.

The SQLite schema is:

```sql
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    price REAL NOT NULL,
    rating INTEGER NOT NULL,
    url TEXT NOT NULL UNIQUE
);
```

Seed the database:

```powershell
.\.venv\Scripts\python.exe seed.py
```

`seed.py` converts the scraper's `rating_text` values (`One` through `Five`) into integers `1` through `5`.

The script starts with `DELETE FROM books`, so running the seed twice does not duplicate development data. Both runs finish with:

```text
SELECT COUNT(*) FROM books -> 60
```

The generated `report.db` is intentionally ignored by Git. The committed seed script is the reproducible recipe.
## Stage 2 - Aggregation queries

`report_data.py` contains the reusable query layer for the report.

Run it with:

```powershell
.\.venv\Scripts\python.exe report_data.py
```

The summary query calculates the total number of books and average price:

```sql
SELECT
    COUNT(*) AS total_books,
    ROUND(AVG(price), 2) AS average_price
FROM books;
```

The five most expensive books are selected with:

```sql
SELECT title, price, rating, url
FROM books
ORDER BY price DESC, title ASC
LIMIT 5;
```

Rating distribution is calculated with:

```sql
SELECT rating, COUNT(*) AS book_count
FROM books
GROUP BY rating
ORDER BY rating ASC;
```

The function also loads the complete 60-book table so the next stage can render a multi-page PDF without duplicating database logic.
## Stage 3 - HTML to PDF

`pdf_renderer.py` turns the Stage 2 aggregation data into an HTML report and uses headless Chromium through Playwright to print it as an A4 PDF.

Generate the checkpoint file:

```powershell
.\.venv\Scripts\python.exe pdf_renderer.py --output reports/test.pdf
```

The renderer uses:

```python
page.pdf(
    path=str(output_path),
    format="A4",
    print_background=True,
    prefer_css_page_size=True,
)
```

The report includes summary metrics, the five most expensive books, rating counts, and the complete 60-book table.

Print-safe table CSS includes:

```css
thead {
  display: table-header-group;
}

tr {
  break-inside: avoid;
  page-break-inside: avoid;
}
```

This keeps rows from splitting awkwardly and repeats the table header on later PDF pages. `reports/` is generated output and remains ignored by Git.