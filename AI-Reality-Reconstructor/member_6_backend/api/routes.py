"""Versioned API endpoints. Routers delegate business rules to services."""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..database.models import CaseRecord, EvidenceRecord, JobRecord, OutputRecord
from ..database.session import get_db
from ..orchestration.pipeline import run_case_pipeline
from ..schemas import CaseCreate, CaseOut, CaseUpdate, EvidenceOut, JobOut
from ..services.cases import to_case_out
from ..services.evidence import safe_display_filename, to_evidence_out
from ..storage.local import storage

logger = logging.getLogger("member_6_backend.api")
router = APIRouter()


def _case_or_404(db: Session, case_id: str) -> CaseRecord:
    record = db.get(CaseRecord, case_id)
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "case_not_found", "message": "Case not found"})
    return record


def _job_out(job: JobRecord) -> JobOut:
    error = None
    if job.error_code:
        error = {"code": job.error_code, "message": job.error_message or "Processing failed."}
    return JobOut(
        id=job.id, case_id=job.case_id, status=job.status, current_stage=job.current_stage,
        adapter_mode=job.adapter_mode, created_at=job.created_at, started_at=job.started_at,
        completed_at=job.completed_at, error=error, stage_outcomes=job.stage_outcomes or [],
    )


@router.get("/health/live", tags=["health"], summary="Check API liveness")
def liveness():
    return {"data": {"status": "ok"}}


@router.get("/health/ready", tags=["health"], summary="Check database readiness")
def readiness(db: Session = Depends(get_db)):
    try:
        db.execute(select(1))
    except SQLAlchemyError as exc:
        logger.warning("readiness_failed dependency=database")
        raise HTTPException(status_code=503, detail={"code": "database_unavailable", "message": "Database is not ready"}) from exc
    return {"data": {"status": "ready", "database": "ready"}}


@router.get("/health", tags=["health"], summary="Check API liveness")
def health_alias():
    return liveness()


@router.post("/cases", status_code=201, tags=["cases"], summary="Create a case")
def create_case(payload: CaseCreate, db: Session = Depends(get_db)):
    now = datetime.now(UTC)
    record = CaseRecord(id=str(uuid4()), title=payload.title.strip(), description=payload.description, created_at=now, updated_at=now)
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"data": to_case_out(record)}


@router.get("/cases", tags=["cases"], summary="List cases")
def list_cases(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=200), db: Session = Depends(get_db),
):
    statement = select(CaseRecord)
    count_statement = select(func.count()).select_from(CaseRecord)
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(CaseRecord.title.ilike(pattern))
        count_statement = count_statement.where(CaseRecord.title.ilike(pattern))
    total = db.scalar(count_statement) or 0
    records = db.scalars(statement.order_by(CaseRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"data": {"items": [to_case_out(item) for item in records], "page": page, "page_size": page_size, "total": total}}


@router.get("/cases/{case_id}", tags=["cases"], summary="Get a case")
def get_case(case_id: str, db: Session = Depends(get_db)):
    return {"data": to_case_out(_case_or_404(db, case_id))}


@router.patch("/cases/{case_id}", tags=["cases"], summary="Update a case")
def update_case(case_id: str, payload: CaseUpdate, db: Session = Depends(get_db)):
    record = _case_or_404(db, case_id)
    changes = payload.model_dump(exclude_unset=True)
    if "title" in changes and changes["title"] is not None:
        record.title = changes["title"].strip()
    if "description" in changes and changes["description"] is not None:
        record.description = changes["description"]
    record.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(record)
    return {"data": to_case_out(record)}


@router.delete("/cases/{case_id}", status_code=204, tags=["cases"], summary="Delete a case and its records")
def delete_case(case_id: str, db: Session = Depends(get_db)):
    record = _case_or_404(db, case_id)
    keys = list(db.scalars(select(EvidenceRecord.storage_key).where(EvidenceRecord.case_id == case_id)))
    for key in keys:
        try:
            storage.delete(key)
        except OSError:
            logger.warning("evidence_delete_failed case_id=%s", case_id)
    db.delete(record)
    db.commit()
    return None


@router.post("/cases/{case_id}/evidence", status_code=201, tags=["evidence"], summary="Upload evidence")
async def upload_evidence(
    case_id: str,
    file: UploadFile = File(..., description="Original source evidence file"),
    metadata: str | None = Form(None, description="Optional JSON object containing source metadata"),
    db: Session = Depends(get_db),
):
    _case_or_404(db, case_id)
    from ..config import settings
    from ..services.evidence import parse_metadata

    filename = safe_display_filename(file.filename or "upload")
    extension = filename.rpartition(".")[2].lower()
    if not extension or extension not in settings.allowed_extensions:
        raise HTTPException(status_code=415, detail={"code": "unsupported_file_type", "message": "File type is not supported"})
    try:
        metadata_value = parse_metadata(metadata)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": "invalid_metadata", "message": str(exc)}) from exc
    content = await file.read(settings.max_upload_bytes + 1)
    if not content:
        raise HTTPException(status_code=422, detail={"code": "empty_file", "message": "Evidence file must not be empty"})
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail={"code": "file_too_large", "message": "Evidence file exceeds the configured size limit"})
    evidence_id = str(uuid4())
    try:
        key = storage.put(content)
        record = EvidenceRecord(
            id=evidence_id, case_id=case_id, filename=filename,
            content_type=file.content_type or "application/octet-stream", size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(), storage_key=key, metadata_json=metadata_value,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception as exc:
        db.rollback()
        if "key" in locals():
            try:
                storage.delete(key)
            except OSError:
                pass
        logger.error("evidence_upload_failed case_id=%s", case_id)
        raise HTTPException(status_code=500, detail={"code": "evidence_storage_failed", "message": "Evidence could not be stored"}) from exc
    return {"data": to_evidence_out(record)}


@router.get("/cases/{case_id}/evidence", tags=["evidence"], summary="List case evidence")
def list_evidence(
    case_id: str, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    content_type: str | None = Query(None, max_length=255), db: Session = Depends(get_db),
):
    _case_or_404(db, case_id)
    statement = select(EvidenceRecord).where(EvidenceRecord.case_id == case_id)
    count_statement = select(func.count()).select_from(EvidenceRecord).where(EvidenceRecord.case_id == case_id)
    if content_type:
        statement = statement.where(EvidenceRecord.content_type == content_type)
        count_statement = count_statement.where(EvidenceRecord.content_type == content_type)
    total = db.scalar(count_statement) or 0
    records = db.scalars(statement.order_by(EvidenceRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"data": {"items": [to_evidence_out(item) for item in records], "page": page, "page_size": page_size, "total": total}}


@router.get("/evidence/{evidence_id}", tags=["evidence"], summary="Get evidence metadata")
def get_evidence(evidence_id: str, db: Session = Depends(get_db)):
    record = db.get(EvidenceRecord, evidence_id)
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "evidence_not_found", "message": "Evidence not found"})
    return {"data": to_evidence_out(record)}


@router.get("/evidence/{evidence_id}/file", tags=["evidence"], summary="Download original evidence bytes")
def get_evidence_file(evidence_id: str, db: Session = Depends(get_db)):
    record = db.get(EvidenceRecord, evidence_id)
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "evidence_not_found", "message": "Evidence not found"})
    path = storage.path(record.storage_key)
    if not path.is_file():
        raise HTTPException(status_code=404, detail={"code": "evidence_file_not_found", "message": "Stored evidence file not found"})
    return FileResponse(path, media_type=record.content_type, filename=record.filename)


@router.post("/cases/{case_id}/process", status_code=202, tags=["processing"], summary="Queue case processing")
def process_case(case_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    _case_or_404(db, case_id)
    evidence = db.scalar(select(func.count()).select_from(EvidenceRecord).where(EvidenceRecord.case_id == case_id)) or 0
    if evidence == 0:
        raise HTTPException(status_code=422, detail={"code": "no_evidence", "message": "Upload eligible evidence before processing"})
    active = db.scalar(select(JobRecord).where(JobRecord.case_id == case_id, JobRecord.status.in_(["queued", "processing"])).order_by(JobRecord.created_at.desc()))
    if active:
        raise HTTPException(status_code=409, detail={"code": "job_already_active", "message": "A processing job is already active for this case"})
    from ..config import settings
    job = JobRecord(id=str(uuid4()), case_id=case_id, status="queued", current_stage="queued", adapter_mode=settings.adapter_mode, stage_outcomes=[])
    db.add(job)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(run_case_pipeline, case_id, job.id, {})
    logger.info("pipeline_queued case_id=%s job_id=%s", case_id, job.id)
    return {"data": _job_out(job)}


@router.get("/cases/{case_id}/status", tags=["processing"], summary="Get latest processing status")
def case_status(case_id: str, db: Session = Depends(get_db)):
    _case_or_404(db, case_id)
    job = db.scalar(select(JobRecord).where(JobRecord.case_id == case_id).order_by(JobRecord.created_at.desc()))
    return {"data": _job_out(job) if job else None}


@router.get("/cases/{case_id}/jobs", tags=["processing"], summary="List processing job history")
def list_jobs(case_id: str, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    _case_or_404(db, case_id)
    total = db.scalar(select(func.count()).select_from(JobRecord).where(JobRecord.case_id == case_id)) or 0
    rows = db.scalars(select(JobRecord).where(JobRecord.case_id == case_id).order_by(JobRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"data": {"items": [_job_out(item) for item in rows], "page": page, "page_size": page_size, "total": total}}


@router.get("/jobs/{job_id}", tags=["processing"], summary="Get processing job status")
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(JobRecord, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail={"code": "job_not_found", "message": "Processing job not found"})
    return {"data": _job_out(job)}


def _latest_output(case_id: str, output_type: str, db: Session):
    result = db.scalar(
        select(OutputRecord)
        .join(JobRecord, OutputRecord.job_id == JobRecord.id)
        .where(OutputRecord.case_id == case_id, OutputRecord.output_type == output_type, JobRecord.status == "completed")
        .order_by(OutputRecord.created_at.desc())
    )
    if result is None:
        raise HTTPException(status_code=404, detail={"code": "output_not_found", "message": f"No completed {output_type} output is available"})
    return {"data": result.payload}


@router.get("/cases/{case_id}/timeline", tags=["outputs"], summary="Get latest case timeline")
def get_timeline(case_id: str, db: Session = Depends(get_db)):
    _case_or_404(db, case_id)
    return _latest_output(case_id, "timeline", db)


@router.get("/cases/{case_id}/findings", tags=["outputs"], summary="Get latest case findings")
def get_findings(case_id: str, db: Session = Depends(get_db)):
    _case_or_404(db, case_id)
    return _latest_output(case_id, "findings", db)


@router.get("/cases/{case_id}/scene", tags=["outputs"], summary="Get latest case scene reconstruction")
def get_scene(case_id: str, db: Session = Depends(get_db)):
    _case_or_404(db, case_id)
    return _latest_output(case_id, "scene", db)
