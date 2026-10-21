# R4 — Explicit scope request: persistent Stage 7/Gate B regression tests — 2026-10-21

## Approval required before any test-file write

This document defines the exact test-only work proposed under the current technical delegation. No tests or workflows have been changed by this proposal.

## Repository baseline and isolated code candidates

- Live main HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- Candidate A (strict checkpoint N and Gate B Boolean input types): `tmp/cp-stage7-failclosed-type-guards-20261021`, head `677b42e33dba90f7c590e32e23fa76debd13242e`.
- Candidate B (conditional Gate B CI limit near zero): `tmp/cp-gateb-ci-near-zero-20261021`, head `ebcdeb97c0e1f298d0e5edab0a6e14721f6ad2b8`.
- Existing test file at main: `tests/test_run_batch.py`, Git blob `5bb3b73201137e08d7fbb053e6bd0a5d63e2fc63`.
- The code-only CPs have passed local logic probes only. Neither has a permanent regression test result or GitHub CI result on its candidate head.

## Requested minimal change

Request permission to edit **only** `tests/test_run_batch.py` on each corresponding temporary candidate branch to add deterministic unit/regression coverage for the code changed in that branch. Existing production source code is not changed by this test CP. The two isolated candidate branches remain separate, so each test result is tied to its own tested source SHA.

### Candidate A — strict type guards

Add deterministic tests proving:
1. `filter_statistical_history` retains approved integer doubling checkpoints `300, 600, 1200, 2400`.
2. A valid legacy intermediate integer N is still classified according to the existing schedule.
3. Non-int values `300.9`, `300.0`, `"300"`, `True`, `None`, and a missing `n` raise the fail-closed `ValueError`; in particular, fractional N must not be silently truncated.
4. The `run_batch.evaluate_gate_b` function accepts actual `True`/`False` values and rejects `"False"`, `0`, `1`, and `None` for each required metric's `stable` field.

### Candidate B — near-zero CI limit

Add deterministic tests for the helper/calculation path proving:
1. When `abs(mean) < REFERENCE_EPSILON`, the limit is `CI_ABSOLUTE_EPSILON`.
2. When `abs(mean) >= REFERENCE_EPSILON`, the limit is `CI_RELATIVE_TOLERANCE * abs(mean)`, including a non-near-zero mean of 10 where the limit is 0.1, not 1.
3. A synthetic sample with mean around 10 and half-CI between 0.1 and 1 fails the new strict gate, demonstrating the former `max()` expression would have been more permissive. No production sample or project data is used.

## Execution and acceptance

- First add only the tests to the relevant candidate branch, read back the changed file and branch SHA, then run the focused test file on that exact SHA if the existing, already-present test execution mechanism can be used without editing or adding a workflow.
- Do not create/change a GitHub Actions workflow. If exact-SHA remote CI cannot run without a workflow change, stop and report `NOT_CI_VALIDATED`; do not improvise a workflow.
- Keep each candidate isolated; report test output, code/test Git blob SHAs, and compare against the base.
- Acceptance is limited to regression coverage for these narrow code changes. It does not make Gate A pass, resolve the complete stop policy, implement Confidence Sequences, establish scenario stability, accept P16/Stage 13 delivery, or authorize a production run.

## Explicit exclusions

- No `main` writes, merge, PR creation/closure, release, or state/status promotion.
- No workflow files, other tests, code beyond the specified candidates, source SHA, seed/RNG, Golden/provider, cohort/trial IDs, Parquet, manifests, historical artifacts, or production data changes.
- No simulation, Trial, Checkpoint, full P16 rebuild, or production Stage 7 execution.

## Current status

`PENDING_OWNER_APPROVAL`. This R4 records the exact scope request only; it does not itself authorize the test-file edits.
