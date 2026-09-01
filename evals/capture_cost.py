from __future__ import annotations

import json
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: capture_cost.py <docker-log.txt> <output.json>")

source = Path(sys.argv[1])
destination = Path(sys.argv[2])
records = []

for line in source.read_text(encoding="utf-8", errors="replace").splitlines():
    brace = line.find("{")
    if brace < 0:
        continue
    try:
        record = json.loads(line[brace:].strip())
    except json.JSONDecodeError:
        continue
    if record.get("event") == "llm_call":
        records.append(record)

if not records:
    raise SystemExit("No llm_call record found in Docker logs")

record = records[-1]
required = [
    "prompt_version",
    "model",
    "input_tokens",
    "output_tokens",
    "duration_ms",
    "repair_count",
    "provider_cost_usd",
]
missing = [field for field in required if field not in record]
if missing:
    raise SystemExit(f"Cost log missing fields: {missing}")

destination.write_text(
    json.dumps(record, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)

print("Captured real structured cost log:")
print(json.dumps(record, indent=2, ensure_ascii=False))
