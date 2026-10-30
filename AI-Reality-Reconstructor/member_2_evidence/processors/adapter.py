"""Adapter integrating Member 2's multimodal processors with Member 6's background async pipeline."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from .dispatcher import dispatch_process

logger = logging.getLogger("member_2_evidence.adapter")


# Fallback Pydantic models ensuring execution even when backend modules are not installed
class FallbackEvidenceProcessingRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence_id: str
    outcome: Literal["available", "failed"] = "available"
    provenance: list[str]


class FallbackEvidenceProcessingOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    records: list[FallbackEvidenceProcessingRecord]
    adapter_mode: Literal["mock", "real"] = "real"


class RealEvidenceProcessor:
    """
    Real implementation of Member 6's EvidenceProcessor protocol.
    Processes all multimodal evidence inputs through Member 2's specialized modules,
    writes canonical records to real_outputs/evidence/evidence.json, produces provenance
    tracking, and records execution outcome ('available' or 'failed').
    """

    def __init__(self, output_path: Path | None = None) -> None:
        self.output_path = output_path

    def process(self, case_id: str, evidence: list[Any]) -> Any:
        # Dynamically import backend models if present; otherwise use fallback models
        RecordClass = FallbackEvidenceProcessingRecord
        OutputClass = FallbackEvidenceProcessingOutput

        try:
            from member_6_backend.schemas import (
                EvidenceProcessingOutput as BackendOutput,
                EvidenceProcessingRecord as BackendRecord,
            )
            RecordClass = BackendRecord
            OutputClass = BackendOutput
        except ImportError:
            pass

        output_records: list[Any] = []

        for item in evidence:
            file_path = getattr(item, "storage_path", None)
            ev_id = getattr(item, "id", None) or "unknown"
            filename = getattr(item, "filename", None)

            outcome = "available"
            if file_path and Path(file_path).is_file():
                try:
                    dispatch_process(
                        file_path,
                        case_id=case_id,
                        filename=filename,
                        save_to_shared=True,
                        shared_output_path=self.output_path,
                    )
                    outcome = "available"
                except Exception as exc:
                    logger.warning("Error processing evidence item %s (%s): %s", ev_id, file_path, exc)
                    outcome = "failed"
            else:
                logger.warning("Evidence file not found or inaccessible: %s", file_path)
                outcome = "failed"

            try:
                rec = RecordClass(
                    evidence_id=ev_id,
                    outcome=outcome,
                    provenance=[ev_id],
                )
            except Exception:
                rec = FallbackEvidenceProcessingRecord(
                    evidence_id=ev_id,
                    outcome=outcome,
                    provenance=[ev_id],
                )
            output_records.append(rec)

        try:
            return OutputClass(
                records=output_records,
                adapter_mode="real",
            )
        except Exception:
            return FallbackEvidenceProcessingOutput(
                records=output_records,
                adapter_mode="real",
            )

    async def process_evidence_item(self, item: Any, case_id: str = "case-001") -> dict[str, Any] | tuple[dict[str, Any], list[dict[str, Any]]]:
        """Async execution support for single-item background workers."""
        file_path = getattr(item, "storage_path", None)
        filename = getattr(item, "filename", None)
        if not file_path or not Path(file_path).is_file():
            raise FileNotFoundError(f"Evidence file not found: {file_path}")
        return dispatch_process(
            file_path,
            case_id=case_id,
            filename=filename,
            save_to_shared=True,
            shared_output_path=self.output_path,
        )

    async def process_async(self, case_id: str, evidence: list[Any]) -> Any:
        """Async execution matching Member 6 pipeline execution."""
        return self.process(case_id=case_id, evidence=evidence)


class DefaultRealTimelineGenerator:
    """Default downstream real-mode timeline generator producing valid unasserted timeline."""

    def generate(self, case_id: str, evidence: list[Any], processed: Any) -> Any:
        del evidence, processed
        try:
            from member_6_backend.schemas import TimelineOutput
            return TimelineOutput(case_id=case_id, events=[], adapter_mode="real")
        except ImportError:
            return {"case_id": case_id, "events": [], "adapter_mode": "real"}


class DefaultRealInvestigationAnalyzer:
    """Default downstream real-mode investigation analyzer."""

    def analyze(self, case_id: str, evidence: list[Any], timeline: Any) -> Any:
        del evidence, timeline
        try:
            from member_6_backend.schemas import InvestigationOutput
            return InvestigationOutput(case_id=case_id, findings=[], adapter_mode="real")
        except ImportError:
            return {"case_id": case_id, "findings": [], "adapter_mode": "real"}


class DefaultRealSceneReconstructor:
    """Default downstream real-mode scene reconstructor."""

    def reconstruct(self, case_id: str, evidence: list[Any], timeline: Any, investigation: Any) -> Any:
        del evidence, timeline, investigation
        try:
            from member_6_backend.schemas import SceneOutput
            return SceneOutput(case_id=case_id, objects=[], adapter_mode="real")
        except ImportError:
            return {"case_id": case_id, "objects": [], "adapter_mode": "real"}


def create_adapter_bundle() -> Any:
    """
    Factory function for REAL_ADAPTER_FACTORY setting in Member 6 backend:
    REAL_ADAPTER_FACTORY="member_2_evidence.processors.adapter:create_adapter_bundle"
    """
    from member_6_backend.services.adapters import AdapterBundle

    return AdapterBundle(
        evidence_processor=RealEvidenceProcessor(),
        timeline_generator=DefaultRealTimelineGenerator(),
        investigation_analyzer=DefaultRealInvestigationAnalyzer(),
        scene_reconstructor=DefaultRealSceneReconstructor(),
        mode="real",
    )
