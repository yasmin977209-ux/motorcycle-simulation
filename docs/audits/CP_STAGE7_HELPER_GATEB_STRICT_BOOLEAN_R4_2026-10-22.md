# R4 — Strict Boolean guard for the production Stage 7 Gate B helper — 2026-10-22

## Scope (one bounded CP)

- Repository: `yasmin977209-ux/motorcycle-simulation`.
- Base/main HEAD read before the change: `7621ddefe6c971e9eb231eb2a987519c86a2cb51`.
- Candidate branch: `tmp/cp-stage7-helper-bool-gate-20261022`.
- Defect class: `K_CODE + K_TEST`.
- Existing implementation in `scripts/stage7_stability.py::evaluate_gate_b` uses `bool(current_metrics[name]["stable"])`; Python treats non-empty strings such as `"False"` as truthy.
- The production `.github/workflows/stage7-full-run.yml` imports and calls this helper directly, so the already-merged strict guard in `run_batch.evaluate_gate_b` did not cover this second call path.

## R4 decision and minimum change

- Replace implicit coercion with an exact `type(value) is bool` check, failing closed with a clear `ValueError` for strings, numbers, null/missing values, containers, and other non-Boolean values.
- Add deterministic regression coverage to `tests/test_stage7_authoring.py` for valid Boolean evidence and invalid values including `"False"`, 0, 1, and missing/null evidence.
- Add one candidate-only, read-only verification workflow that checks out exactly `github.sha`, compiles the helper, and runs only the focused authoring test. Do not edit or dispatch the production workflow.
- No statistical threshold, stopping rule, Gate A behavior, confidence-sequence method, source SHA, seed/RNG, cohort, trial ID, Parquet, Golden manifest, or historic artifact changes.

## Acceptance criteria

1. Exact-SHA CI succeeds for the candidate.
2. `True`/ `False` actual Booleans retain their meanings.
3. `"False"`, numeric, null/missing, and other non-Boolean values fail closed.
4. Current `main` remains unchanged; no production Stage 7, Monte Carlo, Trial, Checkpoint, release, merge, or data generation is run.
5. Post-write read-back records the exact code/test/workflow blobs and CI Run ID.

## Risks / exclusions

- This fixes a second Boolean-coercion path only. It does not establish overall Gate B, the §2.5 seven-metric stability decision, a sequential/anytime confidence guarantee, Gate A provider coverage, or final delivery acceptance.
- Keep the branch isolated until its CI and read-back evidence are checked. No merge or release is authorized by this CP.
