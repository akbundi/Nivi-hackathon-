"""OCR functionality using Tesseract via pytesseract with robust executable discovery."""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any

from PIL import Image

logger = logging.getLogger("member_2_evidence.ocr")

_TESSERACT_AVAILABLE: bool | None = None
_TESSERACT_VERSION: str | None = None
_TESSERACT_PATH: str | None = None


def find_tesseract_binary() -> str | None:
    """Find tesseract executable across PATH, standard Windows/Linux locations, and TESSERACT_CMD."""
    env_cmd = os.getenv("TESSERACT_CMD") or os.getenv("TESSERACT_PATH")
    if env_cmd:
        p = Path(env_cmd)
        if p.is_file():
            return str(p)
        exe = p / "tesseract.exe" if os.name == "nt" else p / "tesseract"
        if exe.is_file():
            return str(exe)

    which_path = shutil.which("tesseract")
    if which_path:
        return which_path

    # Common Windows installation directories
    common_windows_paths = [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
        Path(os.getenv("LOCALAPPDATA", "")) / "Tesseract-OCR" / "tesseract.exe",
    ]
    for candidate in common_windows_paths:
        if candidate.is_file():
            return str(candidate)

    return None


def check_tesseract_availability() -> tuple[bool, str]:
    """
    Check if Tesseract OCR is installed and functional.
    Returns (is_available, message_or_version).
    """
    global _TESSERACT_AVAILABLE, _TESSERACT_VERSION, _TESSERACT_PATH

    if _TESSERACT_AVAILABLE is not None:
        return _TESSERACT_AVAILABLE, _TESSERACT_VERSION or "Not installed"

    import pytesseract

    tess_path = find_tesseract_binary()
    if tess_path:
        pytesseract.pytesseract.tesseract_cmd = tess_path
        _TESSERACT_PATH = tess_path

    try:
        ver = pytesseract.get_tesseract_version()
        _TESSERACT_AVAILABLE = True
        _TESSERACT_VERSION = str(ver)
        return True, f"Tesseract OCR v{ver} available at {_TESSERACT_PATH or 'PATH'}"
    except Exception as exc:
        _TESSERACT_AVAILABLE = False
        _TESSERACT_VERSION = None
        msg = (
            f"Tesseract OCR is not installed or not in PATH ({exc}). "
            "To enable OCR for scanned documents, install Tesseract from "
            "https://github.com/UB-Mannheim/tesseract/wiki (Windows) or 'apt install tesseract-ocr' (Linux), "
            "and add it to PATH or set TESSERACT_CMD."
        )
        return False, msg


def run_ocr_on_image(image: Image.Image | Path | str) -> dict[str, Any]:
    """
    Run Tesseract OCR on a PIL Image or image file path.
    Returns dict with success, text, status, and error details.
    """
    is_available, status_msg = check_tesseract_availability()
    if not is_available:
        return {
            "success": False,
            "status": "tesseract_not_installed",
            "text": "",
            "error": status_msg,
        }

    import pytesseract

    try:
        if isinstance(image, (str, Path)):
            img = Image.open(image)
        else:
            img = image

        text = pytesseract.image_to_string(img).strip()
        return {
            "success": True,
            "status": "ocr_completed",
            "text": text,
            "error": None,
        }
    except Exception as exc:
        logger.warning("OCR processing error: %s", exc)
        return {
            "success": False,
            "status": "ocr_failed",
            "text": "",
            "error": f"OCR processing failed: {exc}",
        }
