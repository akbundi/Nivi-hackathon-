
import json
from pathlib import Path

evidence_file = (
    Path(__file__).resolve().parents[1]
    / "real_outputs"
    / "evidence"
    / "evidence.json"
)

required_fields = [
    "id",
    "case_id",
    "type",
    "timestamp",
    "source",
    "confidence",
    "status",
    "data"
]

with open(evidence_file, "r", encoding="utf-8") as file:
    records = json.load(file)

if not isinstance(records, list):
    raise ValueError("Evidence file must contain a JSON list.")

errors = []

for index, record in enumerate(records, start=1):
    missing = [field for field in required_fields if field not in record]

    if missing:
        errors.append(f"Record {index}: missing fields {missing}")

    if not record.get("case_id"):
        errors.append(f"Record {index}: case_id is empty")

    if record.get("status") not in ["OBSERVED", "INFERRED", "UNKNOWN"]:
        errors.append(f"Record {index}: invalid status")

if errors:
    print("Validation failed:")
    for error in errors:
        print("-", error)
else:
    print("Validation passed!")
    print("Total evidence records:", len(records))
    print("All records contain the required fields.")
