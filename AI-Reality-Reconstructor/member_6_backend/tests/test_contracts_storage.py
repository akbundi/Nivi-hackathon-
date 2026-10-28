from __future__ import annotations

import pytest
from pydantic import ValidationError

from member_6_backend.schemas import Finding
from member_6_backend.storage.local import LocalEvidenceStorage


def test_claims_require_provenance():
    with pytest.raises(ValidationError):
        Finding(id="f1", statement="unsupported", epistemic_status="OBSERVED", source_evidence_ids=[])
    unknown = Finding(id="f2", statement="not established", epistemic_status="UNKNOWN", source_evidence_ids=[])
    assert unknown.epistemic_status == "UNKNOWN"


def test_local_storage_rejects_traversal_and_preserves_bytes(tmp_path):
    backend = LocalEvidenceStorage(tmp_path)
    key = backend.put(b"original")
    assert backend.read(key) == b"original"
    with pytest.raises(ValueError):
        backend.path("../outside")
    backend.delete(key)
    assert not backend.path(key).exists()
