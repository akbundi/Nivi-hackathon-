"""PDF and document evidence processor with PyMuPDF text extraction, scanned page detection, and Tesseract OCR."""

from __future__ import annotations

import io
import json
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image

from .ocr import check_tesseract_availability, run_ocr_on_image

logger = logging.getLogger("member_2_evidence.document")

SUPPORTED_DOCUMENT_EXTENSIONS = frozenset({".pdf"})


def _parse_pdf_date(raw_date: str | None) -> str | None:
    """Parse standard PDF date string 'D:YYYYMMDDHHmmSS[OHH'mm']' into ISO 8601."""
    if not raw_date or not isinstance(raw_date, str):
        return None

    cleaned = raw_date.strip().lstrip("D:")
    # Match YYYYMMDDHHmmss
    match = re.match(r"^(\d{4})(\d{2})(\d{2})(\d{2})?(\d{2})?(\d{2})?", cleaned)
    if not match:
        return None

    try:
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        hour = int(match.group(4) or 0)
        minute = int(match.group(5) or 0)
        second = int(match.group(6) or 0)
        dt = datetime(year, month, day, hour, minute, second)
        return dt.isoformat()
    except Exception:
        return None


def process_pdf(
    file_path: str | Path,
    case_id: str = "case-001",
    enable_ocr: bool = True,
    ocr_dpi_scale: float = 2.0,
) -> dict[str, Any]:
    """
    Process PDF document evidence.
    Extracts metadata and text page-by-page. For scanned or image-only pages,
    renders the page and applies OCR if Tesseract is available.
    """
    if not case_id or not str(case_id).strip():
        raise ValueError("A non-empty case_id is required.")

    pdf_path = Path(file_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if not pdf_path.is_file():
        raise ValueError(f"Path is not a regular file: {pdf_path}")

    if pdf_path.stat().st_size == 0:
        raise ValueError(f"PDF file is empty (0 bytes): {pdf_path}")

    if pdf_path.suffix.lower() not in SUPPORTED_DOCUMENT_EXTENSIONS:
        raise ValueError(f"Unsupported document format '{pdf_path.suffix}'. Only PDF files are supported.")

    import fitz  # PyMuPDF

    try:
        document = fitz.open(pdf_path)
    except Exception as exc:
        raise ValueError(f"Failed to open or decode PDF: {exc}") from exc

    try:
        if document.is_encrypted:
            # Try blank password
            auth_ok = document.authenticate("")
            if not auth_ok:
                raise ValueError(f"PDF is encrypted and password-protected: {pdf_path.name}")

        metadata = document.metadata or {}
        raw_creation = metadata.get("creationDate") or metadata.get("creation_date")
        normalized_timestamp = _parse_pdf_date(raw_creation)

        pages: list[dict[str, Any]] = []
        scanned_pages_detected = 0
        ocr_performed_pages = 0
        overall_ocr_status = "not_required"
        overall_ocr_error: str | None = None

        tess_ok, tess_info = check_tesseract_availability()

        for page_index, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            char_count = len(text)
            has_images = len(page.get_images()) > 0
            # A page is considered scanned or image-only if extractable text is very sparse (< 25 chars)
            is_scanned = char_count < 25

            ocr_applied = False
            ocr_text = ""
            page_ocr_status = "text_sufficient"
            page_ocr_error: str | None = None

            if is_scanned:
                scanned_pages_detected += 1
                if enable_ocr:
                    if tess_ok:
                        try:
                            # Render page at high resolution for OCR
                            mat = fitz.Matrix(ocr_dpi_scale, ocr_dpi_scale)
                            pix = page.get_pixmap(matrix=mat)
                            img_bytes = pix.tobytes("png")
                            pil_img = Image.open(io.BytesIO(img_bytes))

                            ocr_result = run_ocr_on_image(pil_img)
                            if ocr_result.get("success"):
                                ocr_text = ocr_result.get("text", "")
                                text = ocr_text
                                ocr_applied = True
                                ocr_performed_pages += 1
                                page_ocr_status = "ocr_completed"
                            else:
                                page_ocr_status = ocr_result.get("status", "ocr_failed")
                                page_ocr_error = ocr_result.get("error")
                        except Exception as ocr_exc:
                            page_ocr_status = "ocr_failed"
                            page_ocr_error = str(ocr_exc)
                    else:
                        page_ocr_status = "tesseract_not_installed"
                        page_ocr_error = tess_info
                else:
                    page_ocr_status = "ocr_disabled"

            pages.append({
                "page_number": page_index,
                "text": text,
                "char_count": len(text),
                "is_scanned": is_scanned,
                "has_images": has_images,
                "ocr_applied": ocr_applied,
                "ocr_status": page_ocr_status,
                "ocr_error": page_ocr_error,
            })

        if scanned_pages_detected > 0:
            if ocr_performed_pages == scanned_pages_detected:
                overall_ocr_status = "ocr_completed"
            elif ocr_performed_pages > 0:
                overall_ocr_status = "ocr_partial"
            elif not tess_ok:
                overall_ocr_status = "tesseract_not_installed"
                overall_ocr_error = tess_info
            else:
                overall_ocr_status = "ocr_not_applied"

        extraction_method = "ocr" if ocr_performed_pages > 0 else "text_extraction"

        evidence = {
            "id": str(uuid.uuid4()),
            "case_id": case_id,
            "type": "document",
            "timestamp": normalized_timestamp,
            "source": str(pdf_path.resolve()),
            "confidence": None,
            "status": "OBSERVED",
            "data": {
                "filename": pdf_path.name,
                "format": "PDF",
                "file_size_bytes": pdf_path.stat().st_size,
                "page_count": len(document),
                "metadata": {
                    "title": metadata.get("title") or "",
                    "author": metadata.get("author") or "",
                    "creation_date": metadata.get("creationDate") or "",
                    "modification_date": metadata.get("modDate") or "",
                    "creator": metadata.get("creator") or "",
                    "producer": metadata.get("producer") or "",
                },
                "pages": pages,
                "extraction_method": extraction_method,
                "ocr_required": scanned_pages_detected > 0,
                "ocr_status": overall_ocr_status,
                "ocr_error": overall_ocr_error,
                "scanned_pages_count": scanned_pages_detected,
                "ocr_performed_pages_count": ocr_performed_pages,
            },
        }

        return evidence

    finally:
        document.close()


def save_document_evidence(evidence: dict[str, Any], output_path: str | Path) -> None:
    """Save document evidence into the shared evidence JSON file."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    if output.exists():
        try:
            with open(output, "r", encoding="utf-8") as file:
                existing = json.load(file)
                records = existing if isinstance(existing, list) else [existing]
        except (json.JSONDecodeError, OSError):
            records = []

    records.append(evidence)

    with open(output, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)

    print(f"Document evidence saved to: {output.resolve()}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        file_p = sys.argv[1]
        c_id = sys.argv[2] if len(sys.argv) > 2 else "case-001"
    else:
        file_p = input("Enter the PDF file path: ").strip().strip('"')
        c_id = input("Enter case ID (or press Enter for case-001): ").strip() or "case-001"

    try:
        ev = process_pdf(file_p, c_id)
        project_root = Path(__file__).resolve().parents[2]
        shared_output = project_root / "real_outputs" / "evidence" / "evidence.json"
        save_document_evidence(ev, shared_output)
        print("\nExtracted evidence:")
        print(json.dumps(ev, indent=4, ensure_ascii=False))
    except Exception as error:
        print(f"Error: {error}")
