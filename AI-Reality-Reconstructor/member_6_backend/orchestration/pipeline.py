"""Persisted, sequential case-processing pipeline."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import select

from ..config import settings
from ..database.models import CaseRecord, EvidenceRecord, JobRecord, OutputRecord
from ..database.session import SessionLocal
from ..services.adapters import EvidenceInput, load_adapters
from ..storage.local import storage

logger = logging.getLogger("member_6_backend.pipeline")


class OutputContractError(Exception):
    """Adapter data has an invalid case identity or provenance reference."""


def _now() -> datetime:
    return datetime.now(UTC)


def _timed_call(function, *args):
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(function, *args)
    try:
        return future.result(timeout=settings.processing_timeout_seconds)
    except FutureTimeout as exc:
        future.cancel()
        raise TimeoutError("Pipeline adapter timed out") from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _record_stage(session, job: JobRecord, name: str, status: str, started: datetime, error_code: str | None = None) -> None:
    outcome = {"stage": name, "status": status, "started_at": started.isoformat(), "completed_at": _now().isoformat()}
    if error_code:
        outcome["error_code"] = error_code
    job.stage_outcomes = [*job.stage_outcomes, outcome]
    job.current_stage = name
    session.commit()


def _failed(session, job: JobRecord, stage: str, code: str) -> None:
    job.status = "failed"
    job.current_stage = stage
    job.error_code = code
    job.error_message = {
        "adapter_unavailable": "A required processing adapter is unavailable.",
        "adapter_failed": "A processing adapter failed.",
        "invalid_output": "A processing adapter returned data that did not match the backend contract.",
        "evidence_unavailable": "A source evidence file is unavailable.",
        "empty_evidence": "This case has no eligible evidence to process.",
        "pipeline_error": "The processing pipeline encountered an unexpected error.",
        "timeout": "A processing stage exceeded its configured time limit.",
    }.get(code, "Processing failed.")
    job.completed_at = _now()
    session.commit()
    logger.error("pipeline_failed case_id=%s job_id=%s stage=%s code=%s", job.case_id, job.id, stage, code)


def run_case_pipeline(case_id: str, job_id: str, options: dict | None = None) -> None:
    """Entry point suitable for FastAPI BackgroundTasks; each stage is persisted."""
    del options
    with SessionLocal() as session:
        job = session.get(JobRecord, job_id)
        if job is None or job.status != "queued":
            return
        job.status = "processing"
        job.started_at = _now()
        session.commit()
        logger.info("pipeline_started case_id=%s job_id=%s", case_id, job_id)

        try:
            started = _now()
            case = session.get(CaseRecord, case_id)
            evidence_rows = list(session.scalars(select(EvidenceRecord).where(EvidenceRecord.case_id == case_id).order_by(EvidenceRecord.created_at)))
            if case is None:
                _failed(session, job, "validate_case", "pipeline_error")
                return
            if not evidence_rows:
                _record_stage(session, job, "validate_evidence", "failed", started, "empty_evidence")
                _failed(session, job, "validate_evidence", "empty_evidence")
                return
            inputs = []
            for record in evidence_rows:
                path = storage.path(record.storage_key)
                if not path.is_file():
                    _record_stage(session, job, "load_evidence", "failed", started, "evidence_unavailable")
                    _failed(session, job, "load_evidence", "evidence_unavailable")
                    return
                inputs.append(EvidenceInput(record.id, record.filename, record.content_type, record.sha256, path, record.metadata_json or {}))
            _record_stage(session, job, "validate_and_load_evidence", "completed", started)

            try:
                adapters = load_adapters()
            except Exception:
                _record_stage(session, job, "load_adapters", "failed", _now(), "adapter_unavailable")
                _failed(session, job, "load_adapters", "adapter_unavailable")
                return

            stage_start = _now()
            job.current_stage = "evidence_processing"
            session.commit()
            processed = _timed_call(adapters.evidence_processor.process, case_id, inputs)
            from ..schemas import EvidenceProcessingOutput
            processed = EvidenceProcessingOutput.model_validate(processed)
            if processed.adapter_mode != adapters.mode:
                raise OutputContractError("Evidence adapter mode mismatch")
            evidence_ids = {item.id for item in inputs}
            if {item.evidence_id for item in processed.records} != evidence_ids:
                raise OutputContractError("Evidence processing output did not account for this case's evidence")
            if any(source_id not in evidence_ids for item in processed.records for source_id in item.provenance):
                raise OutputContractError("Evidence processing output references unknown evidence")
            _record_stage(session, job, "evidence_processing", "completed", stage_start)

            stage_start = _now()
            job.current_stage = "timeline_generation"
            session.commit()
            from ..schemas import TimelineOutput
            timeline = TimelineOutput.model_validate(_timed_call(adapters.timeline_generator.generate, case_id, inputs, processed))
            if timeline.case_id != case_id or timeline.adapter_mode != adapters.mode:
                raise OutputContractError("Timeline output case or mode mismatch")
            _validate_sources(timeline.events, {item.id for item in inputs})
            _record_stage(session, job, "timeline_generation", "completed", stage_start)

            stage_start = _now()
            job.current_stage = "investigation_analysis"
            session.commit()
            from ..schemas import InvestigationOutput
            investigation = InvestigationOutput.model_validate(_timed_call(adapters.investigation_analyzer.analyze, case_id, inputs, timeline))
            if investigation.case_id != case_id or investigation.adapter_mode != adapters.mode:
                raise OutputContractError("Investigation output case or mode mismatch")
            _validate_sources(investigation.findings, {item.id for item in inputs})
            _record_stage(session, job, "investigation_analysis", "completed", stage_start)

            stage_start = _now()
            job.current_stage = "scene_reconstruction"
            session.commit()
            from ..schemas import SceneOutput
            scene = SceneOutput.model_validate(_timed_call(adapters.scene_reconstructor.reconstruct, case_id, inputs, timeline, investigation))
            if scene.case_id != case_id or scene.adapter_mode != adapters.mode:
                raise OutputContractError("Scene output case or mode mismatch")
            _validate_sources(scene.objects, {item.id for item in inputs})
            _record_stage(session, job, "scene_reconstruction", "completed", stage_start)

            for output_type, value in (("timeline", timeline), ("findings", investigation), ("scene", scene)):
                session.add(OutputRecord(id=str(uuid4()), job_id=job.id, case_id=case_id, output_type=output_type, payload=value.model_dump(mode="json")))
            job.status = "completed"
            job.current_stage = "completed"
            job.completed_at = _now()
            job.error_code = None
            job.error_message = None
            session.commit()
            logger.info("pipeline_completed case_id=%s job_id=%s mode=%s", case_id, job_id, adapters.mode)
        except (ValidationError, OutputContractError):
            session.rollback()
            _record_stage(session, job, job.current_stage or "output_validation", "failed", _now(), "invalid_output")
            _failed(session, job, job.current_stage or "output_validation", "invalid_output")
        except TimeoutError:
            session.rollback()
            _record_stage(session, job, job.current_stage or "processing", "failed", _now(), "timeout")
            _failed(session, job, job.current_stage or "processing", "timeout")
        except Exception:
            session.rollback()
            _record_stage(session, job, job.current_stage or "processing", "failed", _now(), "adapter_failed")
            _failed(session, job, job.current_stage or "processing", "adapter_failed")


def _validate_sources(records, valid_ids: set[str]) -> None:
    for item in records:
        if any(source_id not in valid_ids for source_id in item.source_evidence_ids):
            raise OutputContractError("Adapter output references evidence outside this case")
