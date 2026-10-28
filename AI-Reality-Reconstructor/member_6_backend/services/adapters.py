"""Pluggable AI/module interfaces and deterministic no-claim mock adapters."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from ..config import settings
from ..schemas import EvidenceProcessingOutput, InvestigationOutput, SceneOutput, TimelineOutput


@dataclass(frozen=True)
class EvidenceInput:
    id: str
    filename: str
    content_type: str
    sha256: str
    storage_path: Path
    metadata: dict[str, Any]


class EvidenceProcessor(Protocol):
    def process(self, case_id: str, evidence: list[EvidenceInput]) -> EvidenceProcessingOutput: ...


class TimelineGenerator(Protocol):
    def generate(self, case_id: str, evidence: list[EvidenceInput], processed: EvidenceProcessingOutput) -> TimelineOutput: ...


class InvestigationAnalyzer(Protocol):
    def analyze(self, case_id: str, evidence: list[EvidenceInput], timeline: TimelineOutput) -> InvestigationOutput: ...


class SceneReconstructor(Protocol):
    def reconstruct(self, case_id: str, evidence: list[EvidenceInput], timeline: TimelineOutput, investigation: InvestigationOutput) -> SceneOutput: ...


@dataclass(frozen=True)
class AdapterBundle:
    evidence_processor: EvidenceProcessor
    timeline_generator: TimelineGenerator
    investigation_analyzer: InvestigationAnalyzer
    scene_reconstructor: SceneReconstructor
    mode: str


class MockEvidenceProcessor:
    def process(self, case_id: str, evidence: list[EvidenceInput]) -> EvidenceProcessingOutput:
        del case_id
        return EvidenceProcessingOutput(
            records=[{"evidence_id": item.id, "outcome": "available", "provenance": [item.id]} for item in evidence],
            adapter_mode="mock",
        )


class MockTimelineGenerator:
    def generate(self, case_id: str, evidence: list[EvidenceInput], processed: EvidenceProcessingOutput) -> TimelineOutput:
        del evidence, processed
        return TimelineOutput(case_id=case_id, events=[], adapter_mode="mock")


class MockInvestigationAnalyzer:
    def analyze(self, case_id: str, evidence: list[EvidenceInput], timeline: TimelineOutput) -> InvestigationOutput:
        del evidence, timeline
        return InvestigationOutput(case_id=case_id, findings=[], adapter_mode="mock")


class MockSceneReconstructor:
    def reconstruct(self, case_id: str, evidence: list[EvidenceInput], timeline: TimelineOutput, investigation: InvestigationOutput) -> SceneOutput:
        del evidence, timeline, investigation
        return SceneOutput(case_id=case_id, objects=[], adapter_mode="mock")


def load_adapters() -> AdapterBundle:
    """Load configured implementations; real mode never falls back to mocks."""
    if settings.adapter_mode == "mock":
        return AdapterBundle(MockEvidenceProcessor(), MockTimelineGenerator(), MockInvestigationAnalyzer(), MockSceneReconstructor(), "mock")
    if settings.adapter_mode != "real":
        raise ValueError("ADAPTER_MODE must be either 'mock' or 'real'")
    if not settings.real_adapter_factory:
        raise RuntimeError("Real adapter factory is not configured")
    module_name, separator, attribute = settings.real_adapter_factory.partition(":")
    if not separator or not module_name or not attribute:
        raise RuntimeError("REAL_ADAPTER_FACTORY must use module.path:factory_name")
    factory = getattr(importlib.import_module(module_name), attribute)
    bundle = factory()
    required = ("evidence_processor", "timeline_generator", "investigation_analyzer", "scene_reconstructor")
    if any(not hasattr(bundle, name) for name in required):
        raise RuntimeError("Configured real adapter bundle is missing a required adapter")
    return AdapterBundle(*(getattr(bundle, name) for name in required), mode="real")
