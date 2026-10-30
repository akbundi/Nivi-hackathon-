"""Tests for video decoding, metadata, frame extraction, and scene change detection."""

from __future__ import annotations

from pathlib import Path
import pytest

from member_2_evidence.video.video_processor import (
    find_ffmpeg_executable,
    process_video,
)


def test_video_metadata_and_frame_extraction(synthetic_video: Path, tmp_path: Path):
    out_dir = tmp_path / "custom_frames"
    thumb_dir = tmp_path / "custom_thumbs"
    video_rec, frame_recs = process_video(
        synthetic_video,
        case_id="case-201",
        interval_seconds=0.5,  # Sample every 0.5s of the 2.0s video
        max_frames=10,
        detect_scene_changes=True,
        generate_thumb=True,
        output_dir=out_dir,
        thumbnails_dir=thumb_dir,
    )

    assert video_rec["case_id"] == "case-201"
    assert video_rec["type"] == "video"
    assert video_rec["status"] == "OBSERVED"

    # Verify video thumbnail was created
    assert video_rec["data"].get("thumbnail_file") is not None
    assert Path(video_rec["data"]["thumbnail_file"]).is_file()

    meta = video_rec["data"]["metadata"]
    assert meta["width"] == 320
    assert meta["height"] == 240
    assert meta["fps"] == 10.0
    assert meta["frame_count"] == 20
    assert meta["duration_seconds"] == 2.0

    assert len(frame_recs) > 0
    first_frame = frame_recs[0]
    assert first_frame["type"] == "video_frame"
    assert first_frame["case_id"] == "case-201"
    assert first_frame["data"]["frame_number"] == 1
    assert Path(first_frame["data"]["frame_file"]).is_file()


def test_video_scene_change_detection(synthetic_video: Path, tmp_path: Path):
    video_rec, frame_recs = process_video(
        synthetic_video,
        case_id="case-202",
        interval_seconds=0.5,
        detect_scene_changes=True,
        output_dir=tmp_path / "frames",
    )
    # At least one frame should be evaluated for scene change
    assert any("is_scene_change" in f["data"] for f in frame_recs)


def test_video_invalid_format_raises(tmp_path: Path):
    bad_file = tmp_path / "test.txt"
    bad_file.write_text("not a video")
    with pytest.raises(ValueError, match="Unsupported video format"):
        process_video(bad_file, case_id="case-201")


def test_ffmpeg_locator():
    ffmpeg_bin = find_ffmpeg_executable()
    # If installed at C:\ffmpeg-temp or in PATH, it should be detected
    if ffmpeg_bin is not None:
        assert ffmpeg_bin.is_file()
