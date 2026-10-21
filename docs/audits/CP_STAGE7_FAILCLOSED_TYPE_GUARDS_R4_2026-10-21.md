# R4 — Stage 7 fail-closed input type guards — 2026-10-21

## CP scope

- Repository: `yasmin977209-ux/motorcycle-simulation`
- Base `main` HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`
- Candidate branch: `tmp/cp-stage7-failclosed-type-guards-20261021`
- Classification: `K_CODE`
- Scope: reject malformed statistical-history checkpoint N values and malformed Gate B `stable` values rather than silently normalizing them.
- Out of scope: CI thresholds/formula, stop policy, source SHA, seed/RNG, trial IDs, cohort, Golden coverage, historical data, tests/workflows, `state.json`, main, release, production runs.

## Evidence and authority

1. `scripts/stage7_stability.py` at base blob `468b96b7b592a1ddd55cd4440962775632ab55a1` converts `item["n"]` with `int(raw_n)`. This silently truncates non-integral numeric inputs such as `300.9` to `300`, and treats booleans as integers.
2. `run_batch.py` at base blob `0418ddea818c194a5b582df94778fa5f13a3ecc4` converts Gate B's `stable` with `bool(...)`. Python treats the non-empty string `"False"` as true, so malformed evidence can be promoted to a passing Boolean.
3. Effective decision `D-2026-10-10-01` in `docs/governance/DECISIONS_LOG.md` requires the approved doubling schedule and records checkpoint history. This CP does not alter that schedule or its statistical criteria; it only rejects invalid input types instead of coercing them.
4. The relevant R4 and source were read from live `main`. No candidate or production artifact is used as a golden reference.

## Minimal change

- In `filter_statistical_history`, require `type(raw_n) is int` before checkpoint classification. Reject strings, floats (including `300.0` and `300.9`), booleans, and missing values with the existing fail-closed `ValueError` contract.
- In `evaluate_gate_b`, require each `stable` field to be an actual `bool`. Raise a clear `ValueError` for `"False"`, `0/1`, `None`, or other malformed values. Valid true/false inputs keep their prior meaning.
- Do not change the separate CI near-zero formula here because the exact branch condition needs a direct mapping to the authoritative wording before changing it.

## Acceptance criteria

1. Existing integer history N values such as `300, 600, 1200, 2400` are retained as checkpoints.
2. A well-typed legacy intermediate integer N can still be classified/discarded per the current schedule.
3. `300.9`, `300.0`, `"300"`, `True`, `None`, and missing N fail closed.
4. Gate B accepts only `True`/`False` values and rejects `"False"`, `0`, `1`, and `None`.
5. No test file, workflow, production run, historical artifact, source identity, or policy threshold is changed.

## Verification plan and limits

Run a temporary, uncommitted Python harness against the candidate source for the cases above, plus compile checks. Because project governance explicitly separates test/workflow edits from code-only CPs, this CP will not add or edit repository test files or workflows. This local harness is `PASS_SCOPED_LOCAL` only; it is not GitHub CI, a full pytest pass, or production acceptance.

## Disposition

The change is authorized only as a bounded technical fail-closed guard under the current technical delegation. It does not unblock Gate A, clear `SOURCE_SHA_DRIFT`, establish stability, authorize new trials/checkpoints, or accept Stage 13/P16 delivery.
