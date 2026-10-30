"""Video evidence processing package."""

from .video_processor import process_video, find_ffmpeg_executable, save_video_evidence

__all__ = ["process_video", "find_ffmpeg_executable", "save_video_evidence"]
