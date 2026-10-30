"""Unified multimodal evidence dispatcher with header-based magic byte inspection and blob handling."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from ..image.image_processor import SUPPORTED_IMAGE_EXTENSIONS, process_image, save_evidence
from ..video.video_processor import SUPPORTED_VIDEO_EXTENSIONS, process_video, save_video_evidence
from ..document.pdf_processor import SUPPORTED_DOCUMENT_EXTENSIONS, process_pdf, save_document_evidence
from ..sensor.sensor_processor import SUPPORTED_SENSOR_EXTENSIONS, process_sensor_file, save_sensor_evidence

logger = logging.getLogger("member_2_evidence.dispatcher")


def detect_type_from_header(file_path: Path) -> str | None:
    """
    Inspect the binary header (magic bytes) to identify file modality.
    Essential for backend storage files with generic extensions (e.g. .blob).
    """
    try:
        with open(file_path, "rb") as f:
            header = f.read(512)

        if not header:
            return None

        # 1. PDF Document (%PDF)
        if header.startswith(b"%PDF"):
            return "document"

        # 2. PNG Image (\x89PNG\r\n\x1a\n)
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image"

        # 3. JPEG Image (\xff\xd8\xff)
        if header.startswith(b"\xff\xd8\xff"):
            return "image"

        # 4. WEBP Image (RIFF....WEBP)
        if header.startswith(b"RIFF") and b"WEBP" in header[:16]:
            return "image"

        # 5. GIF Image (GIF87a / GIF89a)
        if header.startswith(b"GIF8"):
            return "image"

        # 6. AVI Video (RIFF....AVI )
        if header.startswith(b"RIFF") and b"AVI " in header[:16]:
            return "video"

        # 7. MP4 / MOV Video (ftyp container box)
        if len(header) >= 12 and header[4:8] == b"ftyp":
            return "video"

        # 8. Matroska / WebM Video (\x1a\x45\xdf\xa3)
        if header.startswith(b"\x1a\x45\xdf\xa3"):
            return "video"

        # 9. Text-based sensor records (JSON or CSV)
        try:
            text = header.decode("utf-8", errors="ignore").strip()
            if text.startswith("{") or text.startswith("["):
                return "sensor"
            if "\n" in text:
                first_line = text.split("\n")[0]
                if "," in first_line or "\t" in first_line:
                    return "sensor"
        except Exception:
            pass

    except Exception as exc:
        logger.debug("Header inspection failed for %s: %s", file_path, exc)

    return None


def identify_evidence_type(file_path: str | Path, filename: str | None = None) -> str:
    """
    Identify multimodal evidence category using file extensions, filename hint,
    and fallback to binary header (magic bytes) inspection.
    """
    path = Path(file_path)
    name_to_check = filename or path.name
    suffix = Path(name_to_check).suffix.lower()

    # Known extensions
    if suffix in SUPPORTED_IMAGE_EXTENSIONS:
        return "image"
    if suffix in SUPPORTED_VIDEO_EXTENSIONS:
        return "video"
    if suffix in SUPPORTED_DOCUMENT_EXTENSIONS:
        return "document"
    if suffix in SUPPORTED_SENSOR_EXTENSIONS:
        return "sensor"

    # If generic suffix (e.g. .blob, .tmp, .bin) or unknown, inspect header bytes
    if path.is_file():
        detected = detect_type_from_header(path)
        if detected:
            return detected

    return "unknown"


def dispatch_process(
    file_path: str | Path,
    case_id: str = "case-001",
    filename: str | None = None,
    save_to_shared: bool = True,
    shared_output_path: Path | None = None,
    **kwargs: Any,
) -> dict[str, Any] | tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Process any multimodal evidence file using the appropriate specialized processor.
    Supports raw backend blob storage files (.blob) by resolving original filenames
    and magic bytes headers.
    Optionally appends the resulting evidence record(s) directly to the canonical
    output file (real_outputs/evidence/evidence.json).
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Evidence file not found: {path}")

    display_name = filename or path.name
    ev_type = identify_evidence_type(path, filename=display_name)

    if shared_output_path is None:
        project_root = Path(__file__).resolve().parents[2]
        shared_output_path = project_root / "real_outputs" / "evidence" / "evidence.json"

    # For blob files, determine appropriate suffix for decoders requiring file extensions
    default_ext_for_type = {
        "image": ".jpg",
        "video": ".mp4",
        "document": ".pdf",
        "sensor": ".csv",
    }
    target_suffix = Path(display_name).suffix.lower()
    if not target_suffix or target_suffix == ".blob":
        target_suffix = default_ext_for_type.get(ev_type, "")

    active_path = path
    temp_named_path: Path | None = None

    if target_suffix and path.suffix.lower() != target_suffix:
        temp_named_path = path.parent / f"temp_{path.stem}{target_suffix}"
        try:
            shutil.copy2(path, temp_named_path)
            active_path = temp_named_path
        except Exception:
            active_path = path

    try:
        if ev_type == "image":
            record = process_image(active_path, case_id=case_id, **kwargs)
            record["data"]["filename"] = display_name
            if save_to_shared:
                save_evidence(record, shared_output_path)
            return record

        elif ev_type == "video":
            vid_record, frame_records = process_video(active_path, case_id=case_id, **kwargs)
            vid_record["data"]["filename"] = display_name
            if save_to_shared:
                save_video_evidence(vid_record, frame_records, shared_output_path)
            return vid_record, frame_records

        elif ev_type == "document":
            record = process_pdf(active_path, case_id=case_id, **kwargs)
            record["data"]["filename"] = display_name
            if save_to_shared:
                save_document_evidence(record, shared_output_path)
            return record

        elif ev_type == "sensor":
            record = process_sensor_file(active_path, case_id=case_id, **kwargs)
            record["data"]["filename"] = display_name
            if save_to_shared:
                save_sensor_evidence(record, shared_output_path)
            return record

        else:
            raise ValueError(
                f"Unsupported evidence type or format for '{display_name}' (detected: '{ev_type}'). "
                f"Supported modalities: image, video, document, sensor."
            )
    finally:
        if temp_named_path and temp_named_path.exists():
            try:
                temp_named_path.unlink()
            except Exception:
                pass
