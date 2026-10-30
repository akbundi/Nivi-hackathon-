"""Video evidence processing with OpenCV decoding, frame extraction, scene change detection, and FFmpeg fallback."""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any

import cv2

from ..image.vision import detect_objects

logger = logging.getLogger("member_2_evidence.video")

SUPPORTED_VIDEO_EXTENSIONS = frozenset({".mp4", ".avi", ".mov", ".mkv"})


def find_ffmpeg_executable() -> Path | None:
    """Dynamically locate FFmpeg executable via PATH, FFMPEG_PATH env var, or local search."""
    env_path = os.getenv("FFMPEG_PATH")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return p
        candidate = p / "ffmpeg.exe" if os.name == "nt" else p / "ffmpeg"
        if candidate.is_file():
            return candidate

    which_path = shutil.which("ffmpeg")
    if which_path:
        return Path(which_path)

    # Common Windows fallback location documented in project
    fallback = Path(r"C:\ffmpeg-temp\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe")
    if fallback.is_file():
        return fallback

    return None


def extract_video_metadata_cv2(cap: cv2.VideoCapture) -> dict[str, Any]:
    """Extract FPS, frame count, width, height, and duration using OpenCV."""
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    duration_seconds = round(frame_count / fps, 3) if fps > 0 else 0.0

    return {
        "fps": round(fps, 2),
        "frame_count": frame_count,
        "width": width,
        "height": height,
        "duration_seconds": duration_seconds,
    }


def is_scene_change(prev_frame: Any, current_frame: Any, threshold: float = 0.35) -> bool:
    """
    Detect significant scene change between frames using grayscale histogram comparison.
    A correlation drop below threshold indicates a noticeable transition.
    """
    if prev_frame is None or current_frame is None:
        return False
    try:
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        hist1 = cv2.calcHist([prev_gray], [0], None, [64], [0, 256])
        hist2 = cv2.calcHist([curr_gray], [0], None, [64], [0, 256])
        cv2.normalize(hist1, hist1, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        cv2.normalize(hist2, hist2, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        return correlation < threshold
    except Exception as exc:
        logger.debug("Scene change computation failed: %s", exc)
        return False


def _extract_frames_ffmpeg(
    video_path: Path,
    output_dir: Path,
    interval_seconds: float,
) -> list[Path]:
    """Fallback frame extraction using FFmpeg CLI."""
    ffmpeg = find_ffmpeg_executable()
    if not ffmpeg:
        raise RuntimeError("FFmpeg executable not found and OpenCV could not decode the video.")

    output_dir.mkdir(parents=True, exist_ok=True)
    fps_filter = f"fps=1/{interval_seconds}"
    pattern = str(output_dir / "frame_%04d.jpg")

    cmd = [
        str(ffmpeg),
        "-i", str(video_path),
        "-vf", fps_filter,
        "-y",
        pattern,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg extraction failed: {result.stderr[-500:]}")

    return sorted(output_dir.glob("frame_*.jpg"))


def process_video(
    video_path: str | Path,
    case_id: str = "case-001",
    interval_seconds: float = 5.0,
    max_frames: int = 60,
    detect_scene_changes: bool = True,
    run_ai_on_frames: bool = False,
    output_dir: Path | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Process video evidence with OpenCV (and FFmpeg fallback).
    Extracts metadata and sampled frames, identifies scene transitions, and produces
    standardized evidence records for the video and individual frames.

    Returns:
        (video_evidence_record, list_of_frame_evidence_records)
    """
    if not case_id or not str(case_id).strip():
        raise ValueError("A non-empty case_id is required.")

    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a regular file: {path}")

    if path.stat().st_size == 0:
        raise ValueError(f"Video file is empty (0 bytes): {path}")

    if path.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
        raise ValueError(
            f"Unsupported video format '{path.suffix}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_VIDEO_EXTENSIONS))}"
        )

    # Resolve frame storage directory
    if output_dir is None:
        project_root = Path(__file__).resolve().parents[2]
        frames_dir = project_root / "real_outputs" / "video_frames" / path.stem
    else:
        frames_dir = output_dir / path.stem

    frames_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(path))
    metadata: dict[str, Any] = {}
    extracted_frames_info: list[dict[str, Any]] = []
    used_engine = "opencv"

    if cap.isOpened():
        try:
            metadata = extract_video_metadata_cv2(cap)
            fps = metadata["fps"] if metadata["fps"] > 0 else 25.0
            frame_step = max(1, int(round(fps * interval_seconds)))

            frame_idx = 0
            saved_count = 0
            prev_frame = None

            while cap.isOpened() and saved_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % frame_step == 0:
                    saved_count += 1
                    timestamp_sec = round(frame_idx / fps, 3)
                    frame_filename = f"frame_{saved_count:04d}.jpg"
                    frame_path = frames_dir / frame_filename

                    cv2.imwrite(str(frame_path), frame)

                    is_scene_keyframe = False
                    if detect_scene_changes and prev_frame is not None:
                        is_scene_keyframe = is_scene_change(prev_frame, frame)

                    frame_objects: list[dict[str, Any]] = []
                    if run_ai_on_frames:
                        vision_res = detect_objects(frame_path, confidence_threshold=0.3)
                        frame_objects = vision_res.get("objects", [])

                    extracted_frames_info.append({
                        "frame_number": saved_count,
                        "frame_file": str(frame_path),
                        "timestamp_seconds": timestamp_sec,
                        "is_scene_change": is_scene_keyframe,
                        "objects_detected": frame_objects,
                    })

                    prev_frame = frame.copy()

                frame_idx += 1
        finally:
            cap.release()

    # If OpenCV could not read frames, fallback to FFmpeg
    if not extracted_frames_info:
        logger.warning("OpenCV could not decode frames for %s; attempting FFmpeg fallback", path)
        ffmpeg_files = _extract_frames_ffmpeg(path, frames_dir, interval_seconds)
        used_engine = "ffmpeg"
        for idx, f_path in enumerate(ffmpeg_files[:max_frames], start=1):
            ts = round((idx - 1) * interval_seconds, 3)
            extracted_frames_info.append({
                "frame_number": idx,
                "frame_file": str(f_path),
                "timestamp_seconds": ts,
                "is_scene_change": False,
                "objects_detected": [],
            })

    if not extracted_frames_info:
        raise ValueError(f"Failed to decode or extract any frames from video: {path}")

    # Primary Video Record
    video_record = {
        "id": str(uuid.uuid4()),
        "case_id": case_id,
        "type": "video",
        "timestamp": None,
        "source": str(path.resolve()),
        "confidence": None,
        "status": "OBSERVED",
        "data": {
            "filename": path.name,
            "format": path.suffix.lstrip(".").upper(),
            "file_size_bytes": path.stat().st_size,
            "engine": used_engine,
            "metadata": metadata,
            "extracted_frames_count": len(extracted_frames_info),
            "extraction_interval_seconds": interval_seconds,
            "frames_directory": str(frames_dir),
        },
    }

    # Individual Frame Records
    frame_records: list[dict[str, Any]] = []
    for info in extracted_frames_info:
        f_rec = {
            "id": str(uuid.uuid4()),
            "case_id": case_id,
            "type": "video_frame",
            "timestamp": None,
            "source": str(path.resolve()),
            "confidence": None,
            "status": "OBSERVED",
            "data": {
                "frame_number": info["frame_number"],
                "frame_file": info["frame_file"],
                "timestamp_seconds": info["timestamp_seconds"],
                "extraction_interval_seconds": interval_seconds,
                "is_scene_change": info["is_scene_change"],
                "objects_detected": info["objects_detected"],
            },
        }
        frame_records.append(f_rec)

    return video_record, frame_records


def save_video_evidence(
    video_record: dict[str, Any],
    frame_records: list[dict[str, Any]],
    output_path: str | Path,
) -> None:
    """Save video and frame records into evidence JSON array."""
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

    records.append(video_record)
    records.extend(frame_records)

    with output.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)

    print(f"Video evidence saved to: {output.resolve()}")
    print(f"Total frame records added: {len(frame_records)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        video_file = sys.argv[1]
        case_id = sys.argv[2] if len(sys.argv) > 2 else "case-001"
    else:
        video_file = input("Enter the video file path: ").strip().strip('"')
        case_id = input("Enter case ID (e.g. case-001): ").strip() or "case-001"

    try:
        vid_rec, f_recs = process_video(video_file, case_id)
        project_root = Path(__file__).resolve().parents[2]
        output_file = project_root / "real_outputs" / "evidence" / "evidence.json"
        save_video_evidence(vid_rec, f_recs, output_file)
    except Exception as error:
        print(f"Error: {error}")
