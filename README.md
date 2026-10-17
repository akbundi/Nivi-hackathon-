# AI Reality Investigator — Phase 1

A small end-to-end starter for creating an investigation case, uploading photo/PDF evidence, and viewing source-linked mock processing results.

## What works

- FastAPI API with versioned (`schema_version: "1.0"`) response contracts.
- Case creation and evidence upload/retrieval.
- Original files stored under `data/uploads/`; structured records stored in a database.
- Evidence metadata includes original filename, media type, byte size, SHA-256, and upload time.
- A conservative mock observation and upload event link back to the evidence record. The mock does not claim to analyze the file's contents.
- Timeline and findings endpoints (empty findings until an investigation module is integrated).
- Browser UI served by the API for creating a case, uploading a file, and inspecting evidence, observations, and timeline.
- SQLite is the zero-setup local default. Set `DATABASE_URL` to PostgreSQL for the shared/team environment.

## Run locally

Requires Python 3.11+.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. API docs are at <http://127.0.0.1:8000/docs>.

For a local PostgreSQL instance, `docker compose up -d db`, then set `DATABASE_URL=postgresql+psycopg://investigator:investigator@localhost:5432/investigator` in `.env` before starting the API. The database and upload directory are configurable with `DATABASE_URL` and `STORAGE_DIR`.

## API

- `POST /api/v1/cases` — create a case (`{"title":"...","description":"..."}`).
- `POST /api/v1/cases/{case_id}/evidence` — multipart upload (`file`). Accepts JPEG, PNG, WebP, and PDF, up to 20 MiB.
- `GET /api/v1/cases/{case_id}/evidence` — evidence metadata and mock observations.
- `GET /api/v1/cases/{case_id}/timeline` — chronological upload events with evidence links.
- `GET /api/v1/cases/{case_id}/findings` — findings (empty in this phase).
- `GET /api/v1/evidence/{evidence_id}/file` — inspect/download the original file.
- `GET /health` — service and schema status.

Successful JSON API responses and structured errors include `schema_version`. Errors use `{ "schema_version": "1.0", "error": { "code": "...", "message": "..." } }`; validation errors may also include `fields`. Uploads are stored with generated names; the submitted filename is retained as metadata. The database records file checksums and original-file references.

## Data contract and ownership

The initial contract is in `app/schemas.py`. `Case` owns a set of `Evidence`; each `Observation` and `Event` references its source evidence by ID. `Finding` is defined for the API boundary but not generated in this vertical slice. The mock observation only states that a file was received and identifies its type; it is not an interpretation of image or PDF contents. Replace `process_upload_mock` with the M2 processor when its output contract is ready.

## Configuration

Copy `.env.example` to `.env` and adjust values as needed. The local default database is `sqlite:///./data/investigator.db`; uploaded originals default to `./data/uploads`. Set `MAX_UPLOAD_BYTES` to change the upload limit.

This is a development skeleton: it has no authentication or case-level access control and should not be exposed publicly without those controls.
