from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "http://localhost:8000"
HERE = Path(__file__).resolve().parent
CASES_PATH = HERE / "cases.json"
RESULTS_PATH = HERE / "results.json"


def call_endpoint(payload: dict) -> tuple[int, dict]:
    request = urllib.request.Request(
        BASE_URL + "/enrich",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = {"raw_error": raw}
        return exc.code, body


def main() -> int:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    results = []
    matched = 0

    for case in cases:
        status, output = call_endpoint(case["input"])
        actual = output.get("category") if status == 200 else None
        passed = status == 200 and actual == case["expected_category"]
        matched += int(passed)

        results.append({
            "id": case["id"],
            "name": case["name"],
            "expected_category": case["expected_category"],
            "actual_category": actual,
            "http_status": status,
            "passed": passed,
            "input": case["input"],
            "output": output,
        })

        print(
            f"{'PASS' if passed else 'FAIL'} {case['id']}: {case['name']} | "
            f"expected={case['expected_category']} | actual={actual} | HTTP {status}"
        )

    total = len(cases)
    percent = round((matched / total) * 100, 2)

    report = {
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "prompt_version": "book-enrich-v1",
        "key_field": "category",
        "matched": matched,
        "total": total,
        "accuracy_percent": percent,
        "results": results,
    }

    RESULTS_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print()
    print(f"EVAL SCORE: {matched}/{total} ({percent:.2f}%)")
    failures = [item for item in results if not item["passed"]]
    if failures:
        print("Failures:")
        for item in failures:
            print(
                f"- case {item['id']} {item['name']}: "
                f"expected={item['expected_category']}, "
                f"actual={item['actual_category']}, HTTP={item['http_status']}"
            )
    else:
        print("Failures: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
