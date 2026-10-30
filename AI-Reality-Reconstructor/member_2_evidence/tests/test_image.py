"""Tests for image evidence processing, EXIF timestamp, GPS extraction, and YOLO object detection."""

from __future__ import annotations

from pathlib import Path
import pytest
from PIL import Image

from member_2_evidence.image.image_processor import (
    extract_gps_info,
    process_image,
)
from member_2_evidence.image.vision import detect_objects, get_yolo_model


def test_image_metadata_extraction(synthetic_image_no_exif: Path):
    record = process_image(synthetic_image_no_exif, case_id="case-101", run_ai=False)

    assert record["case_id"] == "case-101"
    assert record["type"] == "image"
    assert record["status"] == "OBSERVED"
    assert record["source"] == str(synthetic_image_no_exif.resolve())

    data = record["data"]
    assert data["filename"] == "test_no_exif.png"
    assert data["format"] == "PNG"
    assert data["width"] == 320
    assert data["height"] == 240
    assert data["mode"] == "RGB"
    assert data["file_size_bytes"] > 0
    assert data["exif"]["date_time_original"] is None
    assert record["timestamp"] is None


def test_image_exif_timestamp_and_gps_extraction(synthetic_image_with_exif_and_gps: Path):
    record = process_image(synthetic_image_with_exif_and_gps, case_id="case-102", run_ai=False)

    assert record["case_id"] == "case-102"
    assert record["timestamp"] == "2026-10-25T14:30:45"

    data = record["data"]
    assert data["format"] == "JPEG"
    assert data["width"] == 640
    assert data["height"] == 480

    gps = data["exif"]["gps"]
    assert gps is not None
    # 26 + 55/60 + 12.34/3600 = 26.920094
    assert pytest.approx(gps["latitude"], rel=1e-4) == 26.920094
    # 75 + 47/60 + 22.56/3600 = 75.7896
    assert pytest.approx(gps["longitude"], rel=1e-4) == 75.7896
    assert gps["altitude"] == 430.0


def test_image_without_exif_handled_gracefully(tmp_path: Path):
    webp_path = tmp_path / "simple.webp"
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    img.save(webp_path)

    record = process_image(webp_path, case_id="case-103", run_ai=False)
    assert record["status"] == "OBSERVED"
    assert record["timestamp"] is None
    assert record["data"]["exif"]["gps"] is None


def test_image_validation_errors(tmp_path: Path):
    non_existent = tmp_path / "does_not_exist.jpg"
    with pytest.raises(FileNotFoundError):
        process_image(non_existent, case_id="case-001")

    with pytest.raises(ValueError, match="non-empty case_id"):
        process_image(tmp_path, case_id="")

    empty_file = tmp_path / "empty.jpg"
    empty_file.write_bytes(b"")
    with pytest.raises(ValueError, match="empty"):
        process_image(empty_file, case_id="case-001")

    unsupported = tmp_path / "file.exe"
    unsupported.write_bytes(b"MZ12345")
    with pytest.raises(ValueError, match="Unsupported image format"):
        process_image(unsupported, case_id="case-001")


def test_image_yolo_object_detection(synthetic_image_no_exif: Path):
    model, load_err = get_yolo_model("yolov8n.pt")
    if model is None:
        pytest.skip(f"YOLO model unavailable: {load_err}")

    result = detect_objects(synthetic_image_no_exif, confidence_threshold=0.1)
    assert result["available"] is True
    assert result["status"] == "completed"
    assert isinstance(result["objects"], list)


def test_image_thumbnail_generation(synthetic_image_no_exif: Path, tmp_path: Path):
    thumb_dir = tmp_path / "custom_thumbs"
    record = process_image(
        synthetic_image_no_exif,
        case_id="case-thumb",
        run_ai=False,
        generate_thumb=True,
        thumbnails_dir=thumb_dir,
    )
    thumb_path_str = record["data"].get("thumbnail_file")
    assert thumb_path_str is not None
    thumb_path = Path(thumb_path_str)
    assert thumb_path.is_file()
    assert thumb_path.name == "test_no_exif_thumb.jpg"
    with Image.open(thumb_path) as thumb_img:
        assert thumb_img.format == "JPEG"
        assert thumb_img.width <= 320
        assert thumb_img.height <= 320
