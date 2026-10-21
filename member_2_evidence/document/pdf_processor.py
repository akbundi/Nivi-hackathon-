
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

import fitz  # PyMuPDF


def process_pdf(file_path, case_id="case-001"):
    pdf_path = Path(file_path)

    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Please provide a PDF file.")

    evidence = {
        "id": str(uuid.uuid4()),
        "case_id": case_id,
        "type": "document",
        "timestamp": None,
        "source": str(pdf_path.resolve()),
        "confidence": None,
        "status": "OBSERVED",
        "data": {}
    }

    with fitz.open(pdf_path) as document:
        metadata = document.metadata or {}
        pages = []

        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()

            pages.append({
                "page_number": page_number,
                "text": text
            })

        evidence["data"] = {
            "filename": pdf_path.name,
            "format": "PDF",
            "page_count": len(document),
            "metadata": {
                "title": metadata.get("title"),
                "author": metadata.get("author"),
                "creation_date": metadata.get("creationDate"),
                "modification_date": metadata.get("modDate")
            },
            "pages": pages,
            "extraction_method": "text_extraction",
            "ocr_required": any(
                not page["text"] for page in pages
            )
        }

    return evidence



if __name__ == "__main__":
    file_path = input("Enter the PDF file path: ").strip().strip('"')
    case_id = input(
        "Enter case ID (or press Enter for case-001): "
    ).strip() or "case-001"

    try:
        evidence = process_pdf(file_path, case_id)

        # Locate the shared output file
        output_path = (
            Path(__file__).resolve().parents[2]
            / "real_outputs"
            / "evidence"
            / "evidence.json"
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing evidence so image records are preserved
        if output_path.exists():
            with open(output_path, "r", encoding="utf-8") as file:
                existing = json.load(file)

            if isinstance(existing, list):
                records = existing
            else:
                records = [existing]
        else:
            records = []

        # Add the new PDF record
        records.append(evidence)

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=4, ensure_ascii=False)

        print(f"\nEvidence saved to: {output_path}")
        print("\nExtracted evidence:")
        print(json.dumps(evidence, indent=4, ensure_ascii=False))

    except Exception as error:
        print(f"Error: {error}")
