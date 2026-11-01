"""Fail-closed D3 orchestration guard.

The previous source-download pipeline was disabled after identifying that its
pinned source artifacts predate the project cutoff (2026-10-31). Do not invoke
any archive reader until eligible post-cutoff artifacts are verified live.
"""
from __future__ import annotations

import sys

def main() -> None:
    raise SystemExit(
        "BLOCKED_MISSING_EVIDENCE: no D3 source artifacts dated 2026-10-31 or later "
        "have been verified. The prior pre-cutoff pipeline was cancelled and its "
        "unpublished workspace outputs must not be used."
    )

if __name__ == "__main__":
    main()
