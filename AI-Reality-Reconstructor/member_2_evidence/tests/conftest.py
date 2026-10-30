"""Pytest fixtures for generating synthetic multimodal test evidence."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import ExifTags, Image

import fitz  # PyMuPDF


@pytest.fixture
def test_dir(tmp_path: Path) -> Path:
    """Fixture providing a clean isolated directory for test artifacts."""
    return tmp_path


@pytest.fixture
def synthetic_image_no_exif(test_dir: Path) -> Path:
    """Generate a clean synthetic PNG image without EXIF."""
    img_path = test_dir / "test_no_exif.png"
    img = Image.new("RGB", (320, 240), color=(73, 109, 137))
    img.save(img_path)
    return img_path


@pytest.fixture
def synthetic_image_with_exif_and_gps(test_dir: Path) -> Path:
    """Generate a synthetic JPEG image containing EXIF timestamp and GPS coordinates."""
    img_path = test_dir / "test_gps.jpg"
    img = Image.new("RGB", (640, 480), color=(200, 100, 50))

    # Construct EXIF data using PIL getexif()
    exif = img.getexif()
    # 36867: DateTimeOriginal, 306: DateTime
    exif[36867] = "2026:10:25 14:30:45"
    exif[306] = "2026:10:25 14:35:00"

    # GPS IFD
    # Latitude: 26° 55' 12.34" N -> 26.920094
    # Longitude: 75° 47' 22.56" E -> 75.7896
    gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
    gps_ifd[1] = "N"
    gps_ifd[2] = (26.0, 55.0, 12.34)
    gps_ifd[3] = "E"
    gps_ifd[4] = (75.0, 47.0, 22.56)
    gps_ifd[5] = 0
    gps_ifd[6] = 430.0

    img.save(img_path, exif=exif)
    return img_path


@pytest.fixture
def synthetic_video(test_dir: Path) -> Path:
    """Generate a small 2-second synthetic MP4 video with color transitions."""
    vid_path = test_dir / "test_video.mp4"
    width, height, fps = 320, 240, 10.0
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(vid_path), fourcc, fps, (width, height))

    # 20 frames total: first 10 frames blue, next 10 frames yellow (scene change)
    for i in range(20):
        color = (255, 0, 0) if i < 10 else (0, 255, 255)
        frame = np.full((height, width, 3), color, dtype=np.uint8)
        out.write(frame)

    out.release()
    return vid_path


@pytest.fixture
def synthetic_text_pdf(test_dir: Path) -> Path:
    """Generate a synthetic text-rich PDF with metadata."""
    pdf_path = test_dir / "test_document.pdf"
    doc = fitz.open()

    page1 = doc.new_page()
    page1.insert_text((50, 72), "Incident Report 2026\nInvestigation evidence document.\nAll systems operational.")

    page2 = doc.new_page()
    page2.insert_text((50, 72), "Appendix A: Sensor station parameters and readings recorded successfully.")

    doc.set_metadata({
        "title": "Incident Audit Summary",
        "author": "Forensic Investigator",
        "creationDate": "D:20261025120000",
    })

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def synthetic_scanned_pdf(test_dir: Path) -> Path:
    """Generate a synthetic PDF page containing an image without extractable text."""
    pdf_path = test_dir / "test_scanned.pdf"
    doc = fitz.open()

    page = doc.new_page(width=300, height=300)
    # Create a small image and insert it
    img_path = test_dir / "temp_page_img.png"
    img = Image.new("RGB", (200, 200), color=(240, 240, 240))
    img.save(img_path)

    rect = fitz.Rect(50, 50, 250, 250)
    page.insert_image(rect, filename=str(img_path))

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def synthetic_sensor_csv(test_dir: Path) -> Path:
    """Generate a synthetic sensor CSV file."""
    csv_path = test_dir / "test_sensor.csv"
    rows = [
        ["timestamp", "temperature", "humidity", "station_id"],
        ["2026-10-25T10:00:00", "22.5", "55.0", "ST-01"],
        ["2026-10-25T10:05:00", "23.1", "54.2", "ST-01"],
        ["2026-10-25T10:10:00", "24.0", "53.8", "ST-01"],
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return csv_path


@pytest.fixture
def synthetic_sensor_json(test_dir: Path) -> Path:
    """Generate a synthetic sensor JSON file."""
    json_path = test_dir / "test_sensor.json"
    data = {
        "device": "IoT-Gateway-42",
        "records": [
            {"time": "2026-10-25 11:00:00", "pressure_kpa": 101.3, "vibration_hz": 12.4},
            {"time": "2026-10-25 11:01:00", "pressure_kpa": 101.5, "vibration_hz": 13.1},
        ],
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return json_path
