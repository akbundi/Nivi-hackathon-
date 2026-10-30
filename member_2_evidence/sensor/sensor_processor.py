
import csv
import json
import uuid
from pathlib import Path


def process_sensor_file(file_path, case_id="case-001"):
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    extension = path.suffix.lower()

    if extension == ".csv":
        with open(path, "r", encoding="utf-8-sig", newline="") as file:
            records = list(csv.DictReader(file))

    elif extension == ".json":
        with open(path, "r", encoding="utf-8-sig") as file:
            content = json.load(file)

        if isinstance(content, list):
            records = content
        elif isinstance(content, dict):
            records = content.get("records", [content])
        else:
            raise ValueError("JSON must contain an object or a list of records.")

    else:
        raise ValueError("Only CSV and JSON sensor files are supported.")

    evidence = {
        "id": str(uuid.uuid4()),
        "case_id": case_id,
        "type": "sensor",
        "timestamp": None,
        "source": str(path.resolve()),
        "confidence": None,
        "status": "OBSERVED",
        "data": {
            "filename": path.name,
            "format": extension.lstrip(".").upper(),
            "record_count": len(records),
            "records": records
        }
    }

    return evidence


if __name__ == "__main__":
    file_path = input("Enter sensor CSV/JSON file path: ").strip().strip('"')
    case_id = input(
        "Enter case ID (or press Enter for case-001): "
    ).strip() or "case-001"

    try:
        evidence = process_sensor_file(file_path, case_id)

        output_path = (
            Path(__file__).resolve().parents[2]
            / "real_outputs"
            / "evidence"
            / "evidence.json"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.exists():
            with open(output_path, "r", encoding="utf-8") as file:
                existing = json.load(file)

            records = existing if isinstance(existing, list) else [existing]
        else:
            records = []

        records.append(evidence)

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=4, ensure_ascii=False)

        print(f"\nEvidence saved to: {output_path}")
        print("\nExtracted evidence:")
        print(json.dumps(evidence, indent=4, ensure_ascii=False))

    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Error: {error}")
