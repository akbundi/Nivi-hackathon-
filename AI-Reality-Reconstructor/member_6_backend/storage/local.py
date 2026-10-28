"""Safe local storage for immutable original evidence bytes."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from ..config import settings
from .interface import EvidenceStorage


class LocalEvidenceStorage(EvidenceStorage):
    def __init__(self, root: Path | None = None):
        self.root = (root or settings.storage_dir).resolve()

    def put(self, data: bytes) -> str:
        key = f"{uuid4().hex[:2]}/{uuid4().hex}.blob"
        target = self._path_for(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(data)
        return key

    def read(self, key: str) -> bytes:
        return self._path_for(key).read_bytes()

    def path(self, key: str) -> Path:
        return self._path_for(key)

    def delete(self, key: str) -> None:
        path = self._path_for(key)
        path.unlink(missing_ok=True)

    def _path_for(self, key: str) -> Path:
        candidate = (self.root / key).resolve()
        if not candidate.is_relative_to(self.root) or Path(key).is_absolute():
            raise ValueError("Unsafe storage key")
        return candidate


storage = LocalEvidenceStorage()
