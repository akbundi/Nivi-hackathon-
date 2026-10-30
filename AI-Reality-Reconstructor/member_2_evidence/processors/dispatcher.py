"""Unified multimodal evidence dispatcher routing files to the specialized Member 2 processor."""

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


def identify_evidence_type(file_path: str | Path, filename: str | None = None) -> str:
    """Identify multimodal evidence category based on file extension or provided filename."""
    name_to_check = filename or Path(file_path).name
    suffix = Path(name_to_check).suffix.lower()

    if suffix in SUPPORTED_IMAGE_EXTENSIONS:
        return "image"
    if suffix in SUPPORTED_VIDEO_EXTENSIONS:
        return "video"
    if suffix in SUPPORTED_DOCUMENT_EXTENSIONS:
        return "document"
    if suffix in SUPPORTED_SENSOR_EXTENSIONS:
        return "sensor"
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
    Supports stored blob files by checking original filename extension.
    Optionally appends the resulting evidence record(s) to the shared evidence JSON file.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Evidence file not found: {path}")

    display_name = filename or path.name
    ev_type = identify_evidence_type(path, filename=display_name)

    if shared_output_path is None:
        project_root = Path(__file__).resolve().parents[2]
        shared_output_path = project_root / "real_outputs" / "evidence" / "evidence.json"

    # If backend stored file as a .blob with generic name, provide a path with proper extension
    active_path = path
    temp_named_path: Path | None = None
    target_suffix = Path(display_name).suffix.lower()

    if target_suffix and path.suffix.lower() != target_suffix:
        # Create a linked or copied path with correct suffix in same folder
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
                f"Unsupported evidence file extension '{Path(display_name).suffix}'. "
                f"Supported extensions: images {sorted(SUPPORTED_IMAGE_EXTENSIONS)}, "
                f"videos {sorted(SUPPORTED_VIDEO_EXTENSIONS)}, "
                f"documents {sorted(SUPPORTED_DOCUMENT_EXTENSIONS)}, "
                f"sensors {sorted(SUPPORTED_SENSOR_EXTENSIONS)}."
            )
    finally:
        if temp_named_path and temp_named_path.exists():
            try:
                temp_named_path.unlink()
            except Exception:
                pass
