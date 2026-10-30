"""Image evidence processing with EXIF metadata, GPS coordinate conversion, computer vision, and thumbnail generation."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import ExifTags, Image, UnidentifiedImageError

from .vision import detect_objects

logger = logging.getLogger("member_2_evidence.image")

SUPPORTED_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp"})


def generate_image_thumbnail(
    image: Image.Image,
    source_filename: str,
    output_dir: Path | None = None,
    max_size: tuple[int, int] = (320, 320),
) -> str | None:
    """
    Generate a lightweight JPEG thumbnail saved to real_outputs/processed/thumbnails/.
    Returns the string path of the generated thumbnail.
    """
    try:
        if output_dir is None:
            # Resolve to real_outputs/processed/thumbnails/
            project_root = Path(__file__).resolve().parents[2]
            output_dir = project_root / "real_outputs" / "processed" / "thumbnails"

        output_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(source_filename).stem
        thumb_filename = f"{stem}_thumb.jpg"
        thumb_path = output_dir / thumb_filename

        # Create a copy and resize
        thumb_img = image.copy()
        if thumb_img.mode in ("RGBA", "P"):
            thumb_img = thumb_img.convert("RGB")
        thumb_img.thumbnail(max_size, Image.Resampling.LANCZOS)
        thumb_img.save(thumb_path, format="JPEG", quality=85, optimize=True)

        return str(thumb_path)
    except Exception as exc:
        logger.warning("Failed to generate image thumbnail for %s: %s", source_filename, exc)
        return None


def _convert_dms_to_decimal(dms_values: Any) -> float | None:
    """
    Convert EXIF degree/minute/second rational tuple/list to decimal degrees.
    dms_values is typically ((deg_num, deg_den), (min_num, min_den), (sec_num, sec_den))
    or (deg, min, sec) as floats/ints/IFDRational.
    """
    try:
        def _to_float(v: Any) -> float:
            if hasattr(v, "numerator") and hasattr(v, "denominator"):
                return float(v.numerator) / float(v.denominator) if v.denominator != 0 else 0.0
            if isinstance(v, (tuple, list)) and len(v) == 2:
                return float(v[0]) / float(v[1]) if v[1] != 0 else 0.0
            return float(v)

        degrees = _to_float(dms_values[0])
        minutes = _to_float(dms_values[1])
        seconds = _to_float(dms_values[2])
        return degrees + (minutes / 60.0) + (seconds / 3600.0)
    except Exception as exc:
        logger.debug("Failed to convert DMS to decimal: %s", exc)
        return None


def _parse_exif_timestamp(raw_value: str | None) -> str | None:
    """Parse standard EXIF timestamp format 'YYYY:MM:DD HH:MM:SS' into ISO 8601."""
    if not raw_value or not isinstance(raw_value, str):
        return None
    raw_clean = raw_value.strip().replace("\x00", "")
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y:%m:%d %H:%M:%S%z"):
        try:
            dt = datetime.strptime(raw_clean, fmt)
            return dt.isoformat()
        except ValueError:
            continue
    return None


def extract_gps_info(exif_data: Any) -> dict[str, float | None] | None:
    """Extract GPS latitude and longitude in decimal degrees from EXIF."""
    if not exif_data:
        return None

    gps_info = None
    if hasattr(exif_data, "get_ifd"):
        try:
            gps_info = exif_data.get_ifd(ExifTags.IFD.GPSInfo)
        except Exception:
            gps_info = None

    if not gps_info and hasattr(exif_data, "get"):
        gps_info = exif_data.get(34853)

    if not gps_info or not isinstance(gps_info, dict):
        return None

    lat_dms = gps_info.get(2) or gps_info.get("GPSLatitude")
    lat_ref = gps_info.get(1) or gps_info.get("GPSLatitudeRef")
    lon_dms = gps_info.get(4) or gps_info.get("GPSLongitude")
    lon_ref = gps_info.get(3) or gps_info.get("GPSLongitudeRef")
    alt_val = gps_info.get(6) or gps_info.get("GPSAltitude")
    alt_ref = gps_info.get(5) or gps_info.get("GPSAltitudeRef", 0)

    if not lat_dms or not lon_dms:
        return None

    lat_dec = _convert_dms_to_decimal(lat_dms)
    lon_dec = _convert_dms_to_decimal(lon_dms)

    if lat_dec is None or lon_dec is None:
        return None

    if isinstance(lat_ref, str) and lat_ref.upper() == "S":
        lat_dec = -abs(lat_dec)
    elif isinstance(lat_ref, str) and lat_ref.upper() == "N":
        lat_dec = abs(lat_dec)

    if isinstance(lon_ref, str) and lon_ref.upper() == "W":
        lon_dec = -abs(lon_dec)
    elif isinstance(lon_ref, str) and lon_ref.upper() == "E":
        lon_dec = abs(lon_dec)

    altitude = None
    if alt_val is not None:
        try:
            if hasattr(alt_val, "numerator") and hasattr(alt_val, "denominator"):
                alt_num = float(alt_val.numerator) / float(alt_val.denominator) if alt_val.denominator != 0 else 0.0
            elif isinstance(alt_val, (tuple, list)) and len(alt_val) == 2:
                alt_num = float(alt_val[0]) / float(alt_val[1]) if alt_val[1] != 0 else 0.0
            else:
                alt_num = float(alt_val)
            if alt_ref == 1 or str(alt_ref) == "1":
                alt_num = -abs(alt_num)
            altitude = round(alt_num, 2)
        except Exception:
            altitude = None

    return {
        "latitude": round(lat_dec, 6),
        "longitude": round(lon_dec, 6),
        "altitude": altitude,
    }


def process_image(
    image_path: str | Path,
    case_id: str = "case-001",
    run_ai: bool = True,
    generate_thumb: bool = True,
    thumbnails_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Extract image metadata, EXIF details, GPS coordinates, generate thumbnail,
    and detect objects with YOLO. Produces a standardized evidence record.
    """
    if not case_id or not str(case_id).strip():
        raise ValueError("A non-empty case_id is required.")

    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a regular file: {path}")

    if path.stat().st_size == 0:
        raise ValueError(f"Image file is empty (0 bytes): {path}")

    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError(
            f"Unsupported image format '{path.suffix}'. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_IMAGE_EXTENSIONS))}"
        )

    try:
        with Image.open(path) as image:
            image_format = image.format or path.suffix.lstrip(".").upper()
            width, height = image.width, image.height
            mode = image.mode
            file_size_bytes = path.stat().st_size

            # Extract EXIF tags
            exif_obj = None
            try:
                exif_obj = image.getexif()
            except Exception:
                exif_obj = None

            date_original_raw = None
            date_modified_raw = None
            gps_data = None
            normalized_timestamp = None

            if exif_obj:
                date_original_raw = exif_obj.get(36867) or exif_obj.get(36868)
                date_modified_raw = exif_obj.get(306)
                timestamp_source = date_original_raw or date_modified_raw
                normalized_timestamp = _parse_exif_timestamp(timestamp_source)
                gps_data = extract_gps_info(exif_obj)

            # Automated Thumbnail Generation
            thumbnail_file = None
            if generate_thumb:
                thumbnail_file = generate_image_thumbnail(
                    image=image,
                    source_filename=path.name,
                    output_dir=thumbnails_dir,
                )

            # AI Object Detection using cached YOLO
            objects_detected: list[dict[str, Any]] = []
            ai_analysis_info: dict[str, Any] = {
                "available": False,
                "status": "disabled" if not run_ai else "unavailable",
                "model": "yolov8n",
            }

            if run_ai:
                vision_result = detect_objects(path, confidence_threshold=0.25)
                objects_detected = vision_result.get("objects", [])
                ai_analysis_info = {
                    "available": vision_result.get("available", False),
                    "status": vision_result.get("status", "unavailable"),
                    "model": vision_result.get("model", "yolov8n"),
                    "error": vision_result.get("error"),
                    "detected_count": len(objects_detected),
                }

            evidence = {
                "id": str(uuid.uuid4()),
                "case_id": case_id,
                "type": "image",
                "timestamp": normalized_timestamp,
                "source": str(path.resolve()),
                "confidence": None,
                "status": "OBSERVED",
                "data": {
                    "filename": path.name,
                    "format": image_format,
                    "width": width,
                    "height": height,
                    "mode": mode,
                    "file_size_bytes": file_size_bytes,
                    "thumbnail_file": thumbnail_file,
                    "exif": {
                        "date_time_original": date_original_raw,
                        "date_time": date_modified_raw,
                        "gps": gps_data,
                    },
                    "objects_detected": objects_detected,
                    "ai_analysis": ai_analysis_info,
                },
            }

            return evidence

    except UnidentifiedImageError as error:
        raise ValueError(f"The file is not a supported or valid image: {path}") from error


def save_evidence(evidence: dict[str, Any], output_path: str | Path) -> None:
    """Save or append evidence record into a JSON array file."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    if output.exists():
        try:
            with output.open("r", encoding="utf-8") as file:
                loaded = json.load(file)
                records = loaded if isinstance(loaded, list) else [loaded]
        except (json.JSONDecodeError, OSError):
            records = []

    records.append(evidence)

    with output.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)

    print(f"Evidence saved to: {output.resolve()}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        image_file = sys.argv[1]
        case_id = sys.argv[2] if len(sys.argv) > 2 else "case-001"
    else:
        image_file = input("Enter the image file path: ").strip().strip('"')
        case_id = input("Enter case ID (or press Enter for case-001): ").strip() or "case-001"

    try:
        record = process_image(image_file, case_id)
        project_root = Path(__file__).resolve().parents[2]
        output_file = project_root / "real_outputs" / "evidence" / "evidence.json"
        save_evidence(record, output_file)
        print("\nExtracted evidence:")
        print(json.dumps(record, indent=4, ensure_ascii=False))
    except Exception as error:
        print(f"Error: {error}")
