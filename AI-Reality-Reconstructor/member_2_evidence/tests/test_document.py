"""Tests for PDF text extraction, metadata parsing, scanned page detection, and OCR."""

from __future__ import annotations

from pathlib import Path
import pytest

from member_2_evidence.document.ocr import check_tesseract_availability
from member_2_evidence.document.pdf_processor import process_pdf


def test_pdf_metadata_and_text_extraction(synthetic_text_pdf: Path):
    record = process_pdf(synthetic_text_pdf, case_id="case-301", enable_ocr=False)

    assert record["case_id"] == "case-301"
    assert record["type"] == "document"
    assert record["status"] == "OBSERVED"

    data = record["data"]
    assert data["format"] == "PDF"
    assert data["page_count"] == 2
    assert data["metadata"]["title"] == "Incident Audit Summary"
    assert data["metadata"]["author"] == "Forensic Investigator"
    assert record["timestamp"] is not None

    pages = data["pages"]
    assert len(pages) == 2
    assert "Incident Report 2026" in pages[0]["text"]
    assert "Appendix A" in pages[1]["text"]
    assert pages[0]["ocr_applied"] is False


def test_scanned_pdf_detection_and_ocr_fallback(synthetic_scanned_pdf: Path):
    tess_installed, msg = check_tesseract_availability()

    record = process_pdf(synthetic_scanned_pdf, case_id="case-302", enable_ocr=True)
    data = record["data"]

    assert data["ocr_required"] is True
    assert data["scanned_pages_count"] == 1
    page = data["pages"][0]
    assert page["is_scanned"] is True

    if not tess_installed:
        assert data["ocr_status"] == "tesseract_not_installed"
        assert page["ocr_status"] == "tesseract_not_installed"
        assert data["ocr_performed_pages_count"] == 0
        assert page["ocr_applied"] is False
    else:
        assert page["ocr_applied"] is True
        assert data["ocr_status"] == "ocr_completed"


def test_pdf_validation_errors(tmp_path: Path):
    non_existent = tmp_path / "missing.pdf"
    with pytest.raises(FileNotFoundError):
        process_pdf(non_existent, case_id="case-301")

    empty_pdf = tmp_path / "empty.pdf"
    empty_pdf.write_bytes(b"")
    with pytest.raises(ValueError, match="empty"):
        process_pdf(empty_pdf, case_id="case-301")

    not_pdf = tmp_path / "file.csv"
    not_pdf.write_text("a,b\n1,2")
    with pytest.raises(ValueError, match="Only PDF files are supported"):
        process_pdf(not_pdf, case_id="case-301")
