"""FastAPI application entry point."""

from __future__ import annotations

import json
import logging
import re
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api.routes import router
from .config import settings
from .database.session import initialize_database


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }, ensure_ascii=False)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO), handlers=[handler], force=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    initialize_database()
    yield


app = FastAPI(
    title="AI Reality Reconstructor API",
    description=(
        "Backend for case and evidence management and asynchronous processing. "
        "Output contracts distinguish OBSERVED, INFERRED, and UNKNOWN claims; mock outputs make no factual claims."
    ),
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    incoming_id = request.headers.get("X-Request-ID", "")
    request_id = incoming_id if re.fullmatch(r"[A-Za-z0-9._:-]{1,100}", incoming_id) else str(uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        error = detail
    else:
        error = {"code": "http_error", "message": str(detail)}
    return JSONResponse(status_code=exc.status_code, content={"error": error}, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError):
    errors = [{"location": [str(part) for part in item.get("loc", ())], "message": item.get("msg", "Invalid value")} for item in exc.errors()]
    return JSONResponse(status_code=422, content={"error": {"code": "request_validation_failed", "message": "Request validation failed", "details": errors}})


@app.exception_handler(Exception)
async def unexpected_error_handler(_request: Request, exc: Exception):
    logging.getLogger("member_6_backend.api").error("unhandled_request_error type=%s", type(exc).__name__)
    return JSONResponse(status_code=500, content={"error": {"code": "internal_error", "message": "An internal error occurred"}})


app.include_router(router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
def service_info():
    """Provide a small discovery response when a browser visits the host root."""
    return {"data": {
        "service": "AI Reality Reconstructor API",
        "api_base": "/api/v1",
        "health": "/api/v1/health/live",
        "docs": "/api/v1/docs",
    }}
