"""Multimodal processors and adapters package."""

from .dispatcher import identify_evidence_type, dispatch_process
from .adapter import RealEvidenceProcessor, create_adapter_bundle

__all__ = [
    "identify_evidence_type",
    "dispatch_process",
    "RealEvidenceProcessor",
    "create_adapter_bundle",
]
