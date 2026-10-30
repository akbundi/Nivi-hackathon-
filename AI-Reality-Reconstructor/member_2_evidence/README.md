# Member 2 — Multimodal Evidence Processing
**Project:** AI-Reality-Reconstructor  
**Component:** Multimodal Evidence Ingestion, Validation, Computer Vision, and Dispatch Layer

---

## 1. Responsibilities & Scope
Member 2 is responsible for ingesting, validating, extracting metadata from, analyzing, and structuring all multimodal evidence for the AI-Reality-Reconstructor system.

It provides four core specialized processing modules:
1. **Image Processing:** File validation, dimensions, color mode, EXIF extraction (timestamp, camera info), GPS coordinate conversion from DMS to decimal degrees, and computer vision object detection via YOLOv8.
2. **Video Processing:** Video decoding via OpenCV, metadata extraction (duration, FPS, resolution, frame count), configurable frame extraction, scene change / keyframe detection, and FFmpeg fallback.
3. **Document / PDF Processing:** Document metadata extraction, page-by-page text extraction via PyMuPDF, scanned page detection, and Tesseract OCR integration.
4. **Sensor Time-Series Processing:** CSV and JSON reading, timestamp detection and ISO-8601 normalization, numeric metric extraction, statistics calculation (min, max, mean), and record accounting.

It also provides:
- **Unified Multimodal Dispatcher:** Routes incoming evidence files automatically based on modality.
- **Member 6 Integration Adapter:** Implements the `EvidenceProcessor` protocol for seamless execution within Member 6's asynchronous processing pipeline.
- **Validation Engine:** Rigorous schema compliance validator (`validate_evidence.py`).

---

## 2. Supported Evidence Types & Formats

| Modality | Supported Extensions | Engine / Library | Features |
| :--- | :--- | :--- | :--- |
| **Image** | `.png`, `.jpg`, `.jpeg`, `.webp` | Pillow, Ultralytics YOLOv8 | Dimensions, EXIF timestamps, GPS decimal degrees, YOLO object detection |
| **Video** | `.mp4`, `.avi`, `.mov`, `.mkv` | OpenCV (`cv2`), FFmpeg | Duration, FPS, frame count, interval sampling, scene changes, frame images |
| **Document** | `.pdf` | PyMuPDF (`fitz`), Tesseract OCR | Page text, document metadata, scanned detection, OCR for image pages |
| **Sensor** | `.csv`, `.json` | Python `csv`, `json` | Time series parsing, ISO-8601 timestamps, sensor statistics, error accounting |

---

## 3. Architecture & Directory Structure

```text
member_2_evidence/
├── __init__.py                 # Package exports (process_image, process_video, etc.)
├── README.md                   # Complete documentation
├── requirements.txt            # Python dependencies
├── validate_evidence.py        # Schema validation CLI and helper
├── image/
│   ├── __init__.py
│   ├── image_processor.py      # EXIF, GPS decimal conversion, metadata
│   └── vision.py               # YOLOv8 object detection and model caching
├── video/
│   ├── __init__.py
│   └── video_processor.py      # OpenCV decoding, frame extraction, FFmpeg fallback
├── document/
│   ├── __init__.py
│   ├── pdf_processor.py        # PyMuPDF text and page extraction
│   └── ocr.py                  # Tesseract OCR runner and binary discovery
├── sensor/
│   ├── __init__.py
│   └── sensor_processor.py     # CSV/JSON time-series parser and normalizer
├── processors/
│   ├── __init__.py
│   ├── dispatcher.py           # Auto-detection and routing dispatcher
│   └── adapter.py              # RealEvidenceProcessor for Member 6 pipeline
└── tests/
    ├── __init__.py
    ├── conftest.py             # Synthetic fixtures (images, videos, PDFs, CSVs)
    ├── test_image.py           # Image metadata, GPS, EXIF, and YOLO tests
    ├── test_video.py           # Video decoding and frame extraction tests
    ├── test_document.py        # PDF text and scanned page OCR tests
    ├── test_sensor.py          # Sensor CSV/JSON and normalization tests
    └── test_integration.py     # Dispatcher, schema validation, and pipeline integration tests
```

---

## 4. Dependencies & Installation

### Python Dependencies
Install dependencies using `pip`:

```powershell
python -m pip install -r member_2_evidence/requirements.txt
```

Core libraries required:
- `Pillow` (image decoding, EXIF)
- `opencv-python-headless` or `opencv-python` (video processing)
- `pymupdf` (PDF extraction)
- `pytesseract` (OCR integration)
- `ultralytics` & `torch` (YOLOv8 vision inference)
- `pytest` (test execution)

### External Tools Setup

#### A. FFmpeg Setup (Optional / Video Fallback)
OpenCV handles standard video decoding natively. If a video format requires FFmpeg fallback:
- FFmpeg is discovered automatically from `PATH`.
- Or set the `FFMPEG_PATH` environment variable:
  ```powershell
  $env:FFMPEG_PATH = "C:\ffmpeg-temp\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe"
  ```
- The processor also checks common project paths automatically.

#### B. Tesseract OCR Setup (Scanned PDF OCR)
PyMuPDF extracts digital text from PDF files directly without external tools. If a PDF contains scanned image-only pages:
- Install Tesseract OCR:
  - **Windows:** Download the installer from [UB-Mannheim Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki) (default: `C:\Program Files\Tesseract-OCR\tesseract.exe`).
  - **Linux:** `sudo apt-get install tesseract-ocr`
- If installed in a non-standard directory, set:
  ```powershell
  $env:TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"
  ```
- If Tesseract is not installed, the processor reports `"ocr_status": "tesseract_not_installed"` without crashing or fabricating text.

#### C. AI Model Loading (Ultralytics YOLOv8)
- The module uses `yolov8n.pt` (nano) by default for fast, lightweight CPU inference.
- On first execution, Ultralytics downloads `yolov8n.pt` (~6 MB) automatically.
- Model loading is cached in memory. If offline or unavailable, AI analysis reports `"status": "unavailable"` gracefully.

---

## 5. How to Run Processors

All processors can be run standalone from CLI or imported as Python functions:

### 1. Image Processor
```powershell
python member_2_evidence/image/image_processor.py sample_data/images/sample_evidence_photo.jpg case-001
```

### 2. Video Processor
```powershell
python member_2_evidence/video/video_processor.py sample_data/videos/sample_cctv_clip.mp4 case-001
```
Extracted frames are saved under `real_outputs/video_frames/<video_name>/`.

### 3. Document / PDF Processor
```powershell
python member_2_evidence/document/pdf_processor.py sample_data/documents/sample_case_report.pdf case-001
```

### 4. Sensor Processor
```powershell
python member_2_evidence/sensor/sensor_processor.py sample_data/sensors/environmental_readings.csv case-001
```

### 5. Validate Evidence Output
```powershell
python member_2_evidence/validate_evidence.py
```

---

## 6. Integration with Member 6 Backend

Member 2 integrates directly with Member 6's FastAPI backend and background orchestration pipeline.

### Integration Workflow
1. A client uploads evidence to Member 6 (`POST /api/v1/cases/{case_id}/evidence`).
2. Member 6 stores the file bytes in `storage` and creates an `EvidenceRecord`.
3. Client triggers processing (`POST /api/v1/cases/{case_id}/process`).
4. Member 6 loads the configured real adapter via `load_adapters()`.
5. Member 2's `RealEvidenceProcessor.process(case_id, evidence)` is invoked:
   - Identifies modality from the original filename and file content.
   - Dispatches to `image_processor`, `video_processor`, `pdf_processor`, or `sensor_processor`.
   - Appends records to `real_outputs/evidence/evidence.json`.
   - Returns strict `EvidenceProcessingOutput(records=..., adapter_mode="real")`.
6. Member 6's pipeline marks the `evidence_processing` stage as completed and passes evidence down the pipeline.

### Configuring Real Adapter in Member 6
Set these environment variables before launching Member 6's server:
```powershell
$env:ADAPTER_MODE = "real"
$env:REAL_ADAPTER_FACTORY = "member_2_evidence.processors.adapter:create_adapter_bundle"
```

---

## 7. Evidence Record Schema & Example Output

Every evidence record adheres to the following contract:

```json
{
    "id": "e98e0904-874e-4f70-a3bc-223d6fa33c5e",
    "case_id": "case-001",
    "type": "image",
    "timestamp": "2026-10-28T09:15:30",
    "source": "C:\\path\\to\\sample_evidence_photo.jpg",
    "confidence": null,
    "status": "OBSERVED",
    "data": {
        "filename": "sample_evidence_photo.jpg",
        "format": "JPEG",
        "width": 640,
        "height": 480,
        "mode": "RGB",
        "file_size_bytes": 15420,
        "exif": {
            "date_time_original": "2026:10:28 09:15:30",
            "date_time": "2026:10:28 09:15:30",
            "gps": {
                "latitude": 26.9200,
                "longitude": 75.7894,
                "altitude": 435.0
            }
        },
        "objects_detected": [
            {
                "label": "person",
                "confidence": 0.8921,
                "box": [120.4, 85.0, 310.2, 420.5],
                "status": "INFERRED"
            }
        ],
        "ai_analysis": {
            "available": true,
            "status": "completed",
            "model": "yolov8n",
            "error": null,
            "detected_count": 1
        }
    }
}
```

---

## 8. Testing

Run the full Member 2 multimodal test suite:

```powershell
python -m pytest member_2_evidence/tests -v
```

Run both Member 2 and Member 6 integration tests:

```powershell
python -m pytest member_2_evidence/tests member_6_backend/tests -v
```

---

## 9. Known Limitations
- **Tesseract Executable:** Digital PDF text extraction does not require Tesseract. Scanned / image-only documents require the external Tesseract OCR binary to be installed on the host system.
- **Hardware Acceleration:** YOLOv8 runs on CPU by default. While fast for individual images and sampled keyframes, heavy inference on full 60fps video should be sampled (as implemented) rather than analyzing every individual frame.
