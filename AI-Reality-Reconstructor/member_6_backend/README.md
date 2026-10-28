# AI Reality Reconstructor — Member 6 Backend

This package provides the FastAPI integration layer for cases, original evidence files, processing jobs, and the timeline, findings, and scene outputs produced by configured adapters.

## Audit context and contracts

The repository's `shared/` models and JSON schemas, mock/real output JSON files, and Members 2–5 module files were empty when this backend was implemented. The backend therefore defines strict provisional Pydantic contracts in `schemas.py`. These contracts are backend-owned and should be reconciled with shared contracts once those are implemented. No teammate module or real AI adapter is claimed to be integrated.

Mock mode is the default. It records the uploaded evidence as available input and produces empty timeline, findings, and scene collections. It does not invent people, events, timestamps, locations, or conclusions. All output includes an `adapter_mode` value. OBSERVED and INFERRED output entries require evidence provenance, and the pipeline rejects references to evidence outside the case.

## Architecture

- `main.py`: application creation, OpenAPI, CORS, error handling, request IDs, startup.
- `api/routes.py`: thin HTTP endpoints and request validation.
- `database/`: SQLAlchemy records and additive `create_all` initialization.
- `storage/interface.py` and `storage/local.py`: generated-key storage contract and path traversal checks for original evidence bytes. A future object-storage implementation can implement the same interface; it may materialize objects to a local path for adapters that require paths.
- `services/adapters.py`: protocols, deterministic mock adapters, and configured real-adapter factory loading.
- `orchestration/pipeline.py`: persisted stage lifecycle and pipeline entry point `run_case_pipeline(case_id, job_id, options)`.
- `schemas.py`: API and pipeline output contracts until shared schemas exist.
- `deployment/`: backend Docker image and standalone Compose stack.
- `tests/`: backend API, pipeline, and storage tests.

Relational tables hold case/evidence metadata, jobs and stage history, and JSON output payloads. Original evidence bytes are stored separately from database rows. The default local database and evidence directory are under `member_6_backend/data/`; configure paths with environment variables.

## Python local setup

Python 3.12 is the Docker image runtime. The audit machine had Python 3.14.5, but that environment did not have the backend dependencies installed, so package compatibility there was not exercised. A local virtual environment keeps installed packages in the backend directory.

From the repository root in PowerShell:

```powershell
py -3.12 -m venv member_6_backend\.venv
member_6_backend\.venv\Scripts\Activate.ps1
python -m pip install -r member_6_backend\requirements.txt
python -m uvicorn member_6_backend.main:app --reload
```

If Python 3.12 is not installed, install it or use a supported Python version compatible with the listed dependencies. The service defaults to SQLite and mock adapters; no PostgreSQL service or AI key is required for basic local development. OpenAPI is at `http://127.0.0.1:8000/api/v1/docs`.

To select a different local database or storage folder, set `DATABASE_URL` and `STORAGE_DIR` before starting the app. The app does not load `.env` files automatically. In Compose, the API receives `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` as separate values; `config.py` builds a SQLAlchemy `URL` object so special characters in the password are escaped by SQLAlchemy rather than interpolated into a URI.

## Docker Compose

Docker Desktop and Compose must be installed and Docker Desktop must be running. The compose file is independent of the repository root compose file, uses named database and evidence volumes, and connects the API to database hostname `db`.

```powershell
if (-not (Test-Path member_6_backend\.env)) { Copy-Item member_6_backend\.env.example member_6_backend\.env }
notepad member_6_backend\.env
# Set POSTGRES_PASSWORD to a private local password before saving.
docker compose --env-file member_6_backend/.env -f member_6_backend/deployment/docker-compose.yml up --build
```

If the password contains `$`, `#`, spaces, or other Compose `.env` syntax characters, use a single-quoted value in `.env`; Compose removes those quotes and treats the value literally. The backend passes the raw password to `URL.create`, which handles URL escaping.

The API service uses `restart: "no"` in development. A failed database authentication stops the API container once and leaves the failure visible in its logs instead of creating an endless restart loop. PostgreSQL keeps its normal restart behavior. The `db` health check and `depends_on: service_healthy` ensure the API waits for database readiness; they cannot correct a password mismatch.

Stop the services while preserving both named volumes:

```powershell
docker compose --env-file member_6_backend/.env -f member_6_backend/deployment/docker-compose.yml down
```

The service exposes `http://localhost:8000`; readiness waits for PostgreSQL. PostgreSQL persists in the named volume `backend_postgres_data`, and uploaded original evidence persists in `backend_evidence_data`. No host data directory is mounted. The backend-specific `.gitignore` excludes `member_6_backend/.env`; do not commit the populated file. For production, configure secrets securely, restrict CORS, use TLS and authentication at an appropriate gateway, and add managed schema migrations. The current API does not implement user authentication or authorization.

### Existing PostgreSQL volume password recovery

`POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` initialize PostgreSQL only when its data directory is empty. With an existing `backend_postgres_data` volume, changing an environment variable does **not** change the actual PostgreSQL role password. The API's `DB_PASSWORD` must match the password already stored for `reality_app`.

- If you know the current database password, set `POSTGRES_PASSWORD` to that exact value in the Compose environment, then recreate only the API service.
- If you can authenticate to PostgreSQL as `reality_app` or another database administrator, use the interactive `psql` password command below to change the role password. Then put that same value in `POSTGRES_PASSWORD` and recreate only the API service. This changes the role credential without deleting data.
- If you cannot authenticate with any authorized database role, preserve the volume and arrange administrator or backup-based recovery. Do not remove the volume or run `down -v` as a password fix.

Start only PostgreSQL if needed, connect using an authorized role, and enter the `psql` commands interactively. `\password` prompts for the new password without putting it in the command line:

```powershell
docker compose --env-file member_6_backend/.env -f member_6_backend/deployment/docker-compose.yml up -d db
docker compose --env-file member_6_backend/.env -f member_6_backend/deployment/docker-compose.yml exec db psql -U reality_app -d reality_reconstructor
```

At the `psql` prompt:

```text
\password reality_app
\\q
```

After setting the same password in the ignored `member_6_backend/.env` file, recreate only the API and check readiness:

```powershell
docker compose --env-file member_6_backend/.env -f member_6_backend/deployment/docker-compose.yml up -d --no-deps --force-recreate api
Invoke-RestMethod http://localhost:8000/api/v1/health/ready
```

## API

All API routes are under `/api/v1`. Successful JSON responses use a `data` envelope. Errors use an `error` object with a stable `code` and safe message. Pagination returns `items`, `page`, `page_size`, and `total`; page size is capped at 100. Missing resources return 404, unsupported uploads 415, oversized uploads 413, invalid requests 422, active duplicate jobs 409, and database readiness failures 503.

| Method and path | Purpose |
|---|---|
| `GET /health/live` (also `GET /health`) | Liveness check |
| `GET /health/ready` | Database readiness check |
| `POST /cases` | Create a case (`title`, optional `description`) |
| `GET /cases?page=1&page_size=20&search=...` | List and title-filter cases |
| `GET /cases/{case_id}` | Retrieve case |
| `PATCH /cases/{case_id}` | Update title and/or description |
| `DELETE /cases/{case_id}` | Delete case, metadata, jobs, outputs, and evidence files |
| `POST /cases/{case_id}/evidence` | Upload multipart file and optional JSON `metadata` form field |
| `GET /cases/{case_id}/evidence?page=1&page_size=20&content_type=...` | List evidence |
| `GET /evidence/{evidence_id}` | Retrieve evidence metadata |
| `GET /evidence/{evidence_id}/file` | Download original evidence bytes |
| `POST /cases/{case_id}/process` | Queue a case pipeline (202) |
| `GET /cases/{case_id}/status` | Latest job, or `data: null` if none |
| `GET /cases/{case_id}/jobs?page=1&page_size=20` | Paginated job history |
| `GET /jobs/{job_id}` | Job-specific status and stage history |
| `GET /cases/{case_id}/timeline` | Latest completed timeline |
| `GET /cases/{case_id}/findings` | Latest completed investigation findings |
| `GET /cases/{case_id}/scene` | Latest completed scene output |

Interactive OpenAPI documentation is served from `/api/v1/docs` and `/api/v1/redoc`.

### PowerShell examples

```powershell
$case = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/cases `
  -ContentType 'application/json' -Body '{"title":"Example case","description":"Local demo"}'
$caseId = $case.data.id

curl.exe -X POST "http://localhost:8000/api/v1/cases/$caseId/evidence" `
  -F "file=@C:\path\to\evidence.txt" `
  -F 'metadata={"source":"example"}'

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/cases/$caseId/process"
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/cases/$caseId/status"
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/cases/$caseId/timeline"
```

Example queued job response:

```json
{
  "data": {
    "id": "<job-id>", "case_id": "<case-id>", "status": "queued",
    "current_stage": "queued", "adapter_mode": "mock",
    "created_at": "<timestamp>", "started_at": null,
    "completed_at": null, "error": null, "stage_outcomes": []
  }
}
```

## Pipeline and adapters

The pipeline persists `queued → processing → completed` or `queued → processing → failed`, with per-stage timestamps and sanitized error codes. Stages are: validate/load evidence, process evidence, generate timeline, analyze investigation, reconstruct scene, validate contracts/provenance, and persist output records. All four adapters are required for completion; a failed or missing real adapter fails the job.

`ADAPTER_MODE=mock` uses included deterministic adapters. `ADAPTER_MODE=real` requires `REAL_ADAPTER_FACTORY=importable.module:factory_function`. The factory must return an object with `evidence_processor`, `timeline_generator`, `investigation_analyzer`, and `scene_reconstructor` attributes. Each implements the protocol in `services/adapters.py`:

- Evidence processing: `process(case_id, evidence) -> EvidenceProcessingOutput`.
- Timeline: `generate(case_id, evidence, processed) -> TimelineOutput`.
- Investigation: `analyze(case_id, evidence, timeline) -> InvestigationOutput`.
- Scene: `reconstruct(case_id, evidence, timeline, investigation) -> SceneOutput`.

Each `evidence` item contains its ID, original filename, content type, SHA-256 digest, metadata, and storage path. Do not mutate the original bytes. Adapters must return the strict Pydantic output shape, use `adapter_mode="real"`, set the correct case ID, and cite only evidence IDs provided for that case. OBSERVED and INFERRED claims require at least one source ID; UNKNOWN entries may have none. Confidence scores alone are not proof and are not part of the provisional contract.

To register a teammate's implementation, create a factory in an importable Python module and point `REAL_ADAPTER_FACTORY` at it. Members 2–5 currently have no importable implementation, so this integration point is defined but not verified against their eventual code. An absent factory or invocation failure does not fall back to mock mode.

Adapter calls have a configurable per-call timeout (`PROCESSING_TIMEOUT_SECONDS`). Python cannot forcibly terminate a timed-out adapter thread; adapters should use their own network and model timeouts. FastAPI in-process background work can be lost if the API process exits. Persisted job rows do not by themselves recover queued or processing jobs after a crash.

## Database initialization and migrations

Startup calls SQLAlchemy `create_all` to add missing tables; it does not drop tables or reset data. There is no existing migration convention in the repository. `create_all` is suitable for initial local development, but it does not migrate columns on an existing schema. Add Alembic migrations before evolving deployed schemas.

## Testing

Install the backend requirements, then from the repository root run:

```powershell
python -m pytest member_6_backend\tests -q
```

Tests use an isolated in-memory SQLite database and temporary evidence storage; they do not require Docker, model weights, or external AI calls.

## Troubleshooting and limitations

- `docker` not found: install Docker Desktop, start it, then check `docker compose version`.
- Database connection error in Compose: inspect `docker compose ... logs db api`; Compose waits for the database health check and uses service hostname `db`.
- Upload rejected: check extension allowlist and `MAX_UPLOAD_BYTES`.
- Job failed with `adapter_unavailable`: real mode needs a valid factory path and installed adapter module.
- Job failed with `invalid_output`: the adapter output, case ID, epistemic status, or source IDs violated the provisional contract.
- Missing timeline/findings/scene returns 404 until a job completes successfully.
- Active duplicate jobs return 409. The check is process-level and not a distributed lock; deployments with multiple API workers should add a database-level claim mechanism or external queue.
- There is no auth layer, malware scanning, content-based file-type detection, automatic job recovery, object storage, audit-user identity, or real teammate adapter integration yet.
- Shared JSON schemas and fixtures are empty, so these contracts are provisional and may need a coordinated update when those assets are implemented.
