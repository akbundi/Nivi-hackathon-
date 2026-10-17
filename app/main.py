import hashlib
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import Base, engine, get_db
from app.models import CaseRecord, EvidenceRecord, EventRecord, FindingRecord, ObservationRecord, utc_now
from app.schemas import (
    CaseCreate,
    CaseOut,
    EvidenceListOut,
    EvidenceOut,
    FindingOut,
    FindingsOut,
    HealthOut,
    ObservationOut,
    TimelineEventOut,
    TimelineOut,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("reality_investigator")

MEDIA_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        error = detail
    else:
        error = {"code": "http_error", "message": str(detail)}
    return JSONResponse(
        status_code=exc.status_code,
        content={"schema_version": "1.0", "error": error},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "schema_version": "1.0",
            "error": {"code": "invalid_request", "message": "Request validation failed", "fields": jsonable_encoder(exc.errors())},
        },
    )


def require_case(db: Session, case_id: str) -> CaseRecord:
    case = db.get(CaseRecord, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail={"code": "case_not_found", "message": "Case not found"})
    return case


def process_upload_mock(evidence: EvidenceRecord) -> ObservationRecord:
    """Return only a claim established by upload metadata, not file contents."""
    return ObservationRecord(
        evidence_id=evidence.id,
        text=f"A {evidence.media_type} file named '{evidence.original_filename}' was uploaded ({evidence.size_bytes} bytes). File contents have not been analyzed.",
        epistemic_status="observed",
    )


@app.get("/health", response_model=HealthOut)
def health():
    return {"status": "ok"}


@app.post("/api/v1/cases", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)):
    case = CaseRecord(title=payload.title, description=payload.description)
    db.add(case)
    db.commit()
    db.refresh(case)
    logger.info("case_created case_id=%s", case.id)
    return case


@app.get("/api/v1/cases/{case_id}", response_model=CaseOut)
def get_case(case_id: str, db: Session = Depends(get_db)):
    return require_case(db, case_id)


@app.post("/api/v1/cases/{case_id}/evidence", response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
async def upload_evidence(case_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    case = require_case(db, case_id)
    submitted_filename = (file.filename or "upload").replace("\\", "/")
    filename = Path(submitted_filename).name[:255] or "upload"
    media_type = (file.content_type or "").lower()
    if media_type not in settings.allowed_media_types:
        raise HTTPException(status_code=415, detail={"code": "unsupported_media_type", "message": "Upload a JPEG, PNG, WebP, or PDF file"})

    content = await file.read(settings.max_upload_bytes + 1)
    if not content:
        raise HTTPException(status_code=400, detail={"code": "empty_file", "message": "The uploaded file is empty"})
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail={"code": "file_too_large", "message": f"Maximum upload size is {settings.max_upload_bytes} bytes"})

    # Verify basic signatures so a misleading Content-Type is not enough to accept arbitrary data.
    signatures = {
        "image/jpeg": content.startswith(b"\xff\xd8\xff"),
        "image/png": content.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP",
        "application/pdf": content.startswith(b"%PDF-"),
    }
    if not signatures.get(media_type, False):
        raise HTTPException(status_code=415, detail={"code": "file_signature_mismatch", "message": "File contents do not match the declared media type"})

    evidence_id = str(uuid4())
    # Derive the stored extension from the validated media type, not the
    # user-controlled filename.
    storage_key = f"{evidence_id}{MEDIA_TYPE_EXTENSIONS[media_type]}"
    path = settings.storage_dir / storage_key
    try:
        path.write_bytes(content)
        evidence = EvidenceRecord(
            id=evidence_id,
            case_id=case.id,
            original_filename=filename,
            media_type=media_type,
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
            storage_key=storage_key,
            processing_status="completed_mock",
        )
        db.add(evidence)
        db.flush()
        db.add(process_upload_mock(evidence))
        db.add(EventRecord(
            case_id=case.id,
            evidence_id=evidence.id,
            label=f"Evidence uploaded: {filename}",
            occurred_at=utc_now(),
            time_basis="upload_time",
            epistemic_status="observed",
        ))
        db.refresh(evidence)
        db.commit()
    except Exception:
        db.rollback()
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.exception("evidence_file_cleanup_failed storage_key=%s", storage_key)
        logger.exception("evidence_upload_failed case_id=%s", case.id)
        raise HTTPException(status_code=500, detail={"code": "upload_failed", "message": "Could not store uploaded evidence"})
    logger.info("evidence_uploaded case_id=%s evidence_id=%s size_bytes=%s", case.id, evidence.id, evidence.size_bytes)
    return evidence_response(evidence)


def evidence_response(item: EvidenceRecord) -> dict:
    return {
        "id": item.id,
        "case_id": item.case_id,
        "original_filename": item.original_filename,
        "media_type": item.media_type,
        "size_bytes": item.size_bytes,
        "sha256": item.sha256,
        "uploaded_at": item.uploaded_at,
        "processing_status": item.processing_status,
        "file_url": f"/api/v1/evidence/{item.id}/file",
        "observations": [
            {
                "id": observation.id,
                "evidence_id": observation.evidence_id,
                "text": observation.text,
                "epistemic_status": observation.epistemic_status,
                "created_at": observation.created_at,
            }
            for observation in item.observations
        ],
    }


@app.get("/api/v1/cases/{case_id}/evidence", response_model=EvidenceListOut)
def list_evidence(case_id: str, db: Session = Depends(get_db)):
    require_case(db, case_id)
    items = db.scalars(
        select(EvidenceRecord).where(EvidenceRecord.case_id == case_id)
        .options(selectinload(EvidenceRecord.observations)).order_by(EvidenceRecord.uploaded_at.desc())
    ).all()
    return {"items": [evidence_response(item) for item in items]}


@app.get("/api/v1/evidence/{evidence_id}/file")
def get_evidence_file(evidence_id: str, db: Session = Depends(get_db)):
    item = db.get(EvidenceRecord, evidence_id)
    if item is None:
        raise HTTPException(status_code=404, detail={"code": "evidence_not_found", "message": "Evidence not found"})
    path = settings.storage_dir / item.storage_key
    if not path.is_file():
        raise HTTPException(status_code=404, detail={"code": "file_missing", "message": "Stored evidence file is missing"})
    return FileResponse(
        path,
        media_type=item.media_type,
        filename=item.original_filename,
        content_disposition_type="inline",
    )


@app.get("/api/v1/cases/{case_id}/timeline", response_model=TimelineOut)
def get_timeline(case_id: str, db: Session = Depends(get_db)):
    require_case(db, case_id)
    events = db.scalars(select(EventRecord).where(EventRecord.case_id == case_id).order_by(EventRecord.occurred_at.asc())).all()
    return {"items": events}


@app.get("/api/v1/cases/{case_id}/findings", response_model=FindingsOut)
def get_findings(case_id: str, db: Session = Depends(get_db)):
    require_case(db, case_id)
    findings = db.scalars(select(FindingRecord).where(FindingRecord.case_id == case_id)).all()
    return {"items": [FindingOut(id=item.id, finding_type=item.finding_type, text=item.text, epistemic_status=item.epistemic_status, evidence_ids=[]) for item in findings]}


app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="frontend")
