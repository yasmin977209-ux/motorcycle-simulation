from __future__ import annotations

import pytest

from scripts.verify_source_identity_exception import (
    ALLOWED_ADAPTER_BYTES,
    SourceIdentityExceptionError,
    strip_allowlisted_adapter,
)


def test_allowlisted_adapter_removal_restores_source_exactly():
    pinned = b"def _new_contract():\n    return None\n\n"
    candidate = pinned + ALLOWED_ADAPTER_BYTES
    assert strip_allowlisted_adapter(candidate) == pinned


def test_unrelated_source_change_survives_allowlist_removal_and_is_detectable():
    pinned = b"def _new_contract():\n    return None\n\n"
    candidate = pinned + ALLOWED_ADAPTER_BYTES + b"# unapproved source change\n"
    assert strip_allowlisted_adapter(candidate) != pinned


def test_missing_or_duplicate_adapter_fails_closed():
    with pytest.raises(SourceIdentityExceptionError, match="OCCURRENCE_MISMATCH:0"):
        strip_allowlisted_adapter(b"source without the adapter")
    with pytest.raises(SourceIdentityExceptionError, match="OCCURRENCE_MISMATCH:2"):
        strip_allowlisted_adapter(ALLOWED_ADAPTER_BYTES + ALLOWED_ADAPTER_BYTES)
