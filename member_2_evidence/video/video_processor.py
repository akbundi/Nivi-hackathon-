
import json
import uuid
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_FILE = PROJECT_ROOT / "real_outputs" / "evidence" / "evidence.json"

FFMPEG = Path(
    r"C:\ffmpeg-temp\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe"
)


def process_video(video_path, case_id):
    video_path = Path(video_path)

    if not video_path.exists():
        print("Error: Video file not found.")
        return

    if not FFMPEG.exists():
        print("Error: FFmpeg executable not found.")
        return

    frame_dir = PROJECT_ROOT / "real_outputs" / "video_frames" / video_path.stem
    frame_dir.mkdir(parents=True, exist_ok=True)

    # Extract one frame every 5 seconds
    command = [
        str(FFMPEG),
        "-i", str(video_path),
        "-vf", "fps=1/5",
        "-y",
        str(frame_dir / "frame_%04d.jpg")
    ]

    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as error:
        print("Video processing failed.")
        print(error.stderr[-1500:])
        return

    frames = sorted(frame_dir.glob("frame_*.jpg"))

    if not frames:
        print("No frames were extracted.")
        return

    evidence_records = []

    for index, frame in enumerate(frames, start=1):
        record = {
            "id": str(uuid.uuid4()),
            "case_id": case_id,
            "type": "video_frame",
            "timestamp": None,
            "source": str(video_path),
            "confidence": None,
            "status": "OBSERVED",
            "data": {
                "frame_number": index,
                "frame_file": str(frame.relative_to(PROJECT_ROOT)),
                "extraction_interval_seconds": 5
            }
        }
        evidence_records.append(record)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
                existing_records = json.load(file)
            if not isinstance(existing_records, list):
                existing_records = []
        except (json.JSONDecodeError, OSError):
            existing_records = []
    else:
        existing_records = []

    existing_records.extend(evidence_records)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(existing_records, file, indent=4, ensure_ascii=False)

    print(f"Video processed successfully.")
    print(f"Frames extracted: {len(frames)}")
    print(f"Evidence records added: {len(evidence_records)}")
    print(f"Evidence saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    video = input("Enter the video file path: ").strip().strip('"')
    case = input("Enter case ID (e.g. case-001): ").strip()
    process_video(video, case)
