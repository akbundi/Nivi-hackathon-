"""Storage contract for local or future object-storage implementations."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class EvidenceStorage(Protocol):
    """Generated-key storage. ``path`` may materialize a remote object locally."""

    def put(self, data: bytes) -> str: ...

    def read(self, key: str) -> bytes: ...

    def path(self, key: str) -> Path: ...

    def delete(self, key: str) -> None: ...
