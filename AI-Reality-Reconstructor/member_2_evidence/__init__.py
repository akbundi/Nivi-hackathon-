"""Member 2: Multimodal Evidence Processing package for AI-Reality-Reconstructor."""

from .image.image_processor import process_image
from .video.video_processor import process_video
from .document.pdf_processor import process_pdf
from .sensor.sensor_processor import process_sensor_file
from .processors.dispatcher import dispatch_process, identify_evidence_type
from .processors.adapter import RealEvidenceProcessor, create_adapter_bundle

__all__ = [
    "process_image",
    "process_video",
    "process_pdf",
    "process_sensor_file",
    "dispatch_process",
    "identify_evidence_type",
    "RealEvidenceProcessor",
    "create_adapter_bundle",
]
