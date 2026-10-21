# Member 2 — Multimodal Evidence Processing

## Overview
This module processes image, PDF, sensor CSV/JSON, and video evidence for the AI-Reality-Reconstructor project.

## Components
- `image/image_processor.py` — extracts image metadata and available EXIF information.
- `document/pdf_processor.py` — extracts PDF text and metadata.
- `sensor/sensor_processor.py` — reads sensor records from CSV or JSON.
- `video/video_processor.py` — extracts video frames using FFmpeg.
- `validate_evidence.py` — checks basic evidence record requirements.

## Requirements
- Python 3
- PyMuPDF for PDF processing
- FFmpeg for video processing

Install the PDF dependency if needed:

```powershell
python -m pip install pymupdf
```

The video processor currently expects FFmpeg at:

`C:\ffmpeg-temp\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe`

Update the `FFMPEG` path in `video/video_processor.py` if FFmpeg is installed elsewhere.

## Running the processors
Run commands from the project root:

```powershell
python member_2_evidence/image/image_processor.py
python member_2_evidence/document/pdf_processor.py
python member_2_evidence/sensor/sensor_processor.py
python member_2_evidence/video/video_processor.py
python member_2_evidence/validate_evidence.py
```

The processors append evidence records to:

`real_outputs/evidence/evidence.json`

The video processor also saves extracted frames under:

`real_outputs/video_frames/`

## Evidence record format
Records include `id`, `case_id`, `type`, `timestamp`, `source`, `confidence`, `status`, and `data`.

Use a non-empty case ID, such as `case-001`, when running a processor.

## Notes
The video processor requires FFmpeg to be installed separately. The evidence output format should be confirmed with the project team before integration.