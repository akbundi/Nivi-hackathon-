
import json
import uuid
from datetime import datetime
from pathlib import Path

from PIL import Image, UnidentifiedImageError


def process_image(image_path, case_id="case-001"):
    """
    Extract basic metadata from an image and return
    a structured evidence record.
    """

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    try:
        with Image.open(path) as image:
            exif_data = image.getexif()

            # Read available EXIF timestamps.
            # These are kept as raw metadata because the
            # timezone and accuracy may be unknown.
            date_original = exif_data.get(36867)
            date_modified = exif_data.get(306)

            evidence = {
                "id": str(uuid.uuid4()),
                "case_id": case_id,
                "type": "image",
                "timestamp": None,
                "source": str(path),
                "confidence": None,
                "status": "OBSERVED",
                "data": {
                    "filename": path.name,
                    "format": image.format,
                    "width": image.width,
                    "height": image.height,
                    "mode": image.mode,
                    "file_size_bytes": path.stat().st_size,
                    "exif": {
                        "date_time_original": date_original,
                        "date_time": date_modified
                    }
                }
            }

            return evidence

    except UnidentifiedImageError as error:
        raise ValueError(
            f"The file is not a supported image: {path}"
        ) from error


def save_evidence(evidence, output_path):
    """Save evidence as a JSON array."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Keep evidence records in a list so future images
    # can be added to the same output file.
    records = []

    if output.exists():
        with output.open("r", encoding="utf-8") as file:
            records = json.load(file)

        if not isinstance(records, list):
            raise ValueError(
                "Expected the evidence JSON to contain a list."
            )

    records.append(evidence)

    with output.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)

    print(f"Evidence saved to: {output.resolve()}")


if __name__ == "__main__":
    image_file = input("Enter the image file path: ").strip().strip('"')
    case_id = input("Enter case ID (or press Enter for case-001): ").strip()

    if not case_id:
        case_id = "case-001"

    try:
        record = process_image(image_file, case_id)

        output_file = (
            Path(__file__).resolve().parents[2]
            / "real_outputs"
            / "evidence"
            / "evidence.json"
        )

        save_evidence(record, output_file)

        print("\nExtracted evidence:")
        print(json.dumps(record, indent=4))

    except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError) as error:
        print(f"Error: {error}")
