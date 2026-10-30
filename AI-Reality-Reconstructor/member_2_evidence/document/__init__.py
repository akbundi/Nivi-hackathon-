"""Document evidence processing package."""

from .pdf_processor import process_pdf, save_document_evidence
from .ocr import check_tesseract_availability, run_ocr_on_image

__all__ = ["process_pdf", "save_document_evidence", "check_tesseract_availability", "run_ocr_on_image"]
