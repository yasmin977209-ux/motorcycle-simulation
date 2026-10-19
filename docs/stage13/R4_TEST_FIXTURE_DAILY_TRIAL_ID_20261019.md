# R4 — synthetic Stage 13 daily-row trial_id fixture correction proposal

**Date:** 2026-10-19  
**Status:** R4 complete; test modification and follow-up workflow run are **PENDING EXPLICIT OWNER APPROVAL**. No test file changed.

## R4 matrix

| Element | Current | Governing source / exact text | Ruling |
|---|---|---|---|
| Candidate identity | Branch `tmp/cp-stage13-excel-compat-20261017`; HEAD before this R4 `598488c2530c120d0f71fdf86322d3c7594b8145`; assembler blob `71e05034bafb551aea2949adc94013e8bb23d239`; test blob `976ebc8365db7f2380f15317c677990e34a1269c` | Live candidate read-back | Candidate only; main untouched |
| Validator contract | Every representative daily row must be a dict, `type(daily_row.get("trial_id")) is int`, and the ID must equal the selected expected ID | `scripts/stage13_assemble.py`, `_validate_representatives`, lines 1333–1339 at source blob `71e05034bafb551aea2949adc94013e8bb23d239` | Valid contract for real representative payloads |
| Synthetic fixture | `tests/test_stage13_assembler.py::daily_rows(trial)` builds two daily records but omits `trial_id` from both | Test blob `976ebc8365db7f2380f15317c677990e34a1269c`, lines 59–81 | `K_TEST / SYNTHETIC_FIXTURE_CONTRACT_DRIFT` |
| Exact runtime evidence | Run `39299680243`, tested SHA `027e452e3af5a27de9f465b96c00255efa46e4f2`; pytest: `2 failed, 9 passed, 1 warning in 0.47s`. Literal error: `REPRESENTATIVE_DAILY_TRIAL_MISMATCH: C100_G100/P10` | Job `118221265867`; artifact `12209789284` was downloaded and inspected | Failed result preserved; no PASS |
| Real-payload cross-check | A read-only stream of a real `C050_G000` P10 JSON showed integer `trial_id=131` on daily rows | ZIP `f575044fb6a50cb5ed71d6303c40bd77841a6d38b633c105e560a4731e0a94f9`, inner TAR `19878404d3cb0f7c91dd69e7cd09a79b5267b96b5b91ed0f7bb24d37b4c6e892` | Supports fixture defect classification; not complete runtime acceptance |

## Minimal proposed test-only change

In `daily_rows(trial)`, add `"trial_id": int(trial["trial_id"])` to each of the two returned daily-row dictionaries. Do not change the production validator, model code, canonical data, representative assignments, Parquet, seed/RNG, sampling, cohort, reference, manifest, main, or state.

## Acceptance criteria if approved

1. Read back the one-file test diff and verify only the two synthetic daily fixture dictionaries gain the parent trial ID.
2. Recreate the same scoped, read-only workflow on the exact candidate branch with `contents: read`, push/path restrictions, synthetic fixture and demo workbook only, no `workflow_dispatch`.
3. Run the focused tests and strict-type checks against the corrected fixture; require all selected tests to pass, produce a synthetic 185-sheet workbook, inspect its 185 sheets, five role labels, zero formula/error cells, workbook SHA-256, pytest log, scope JSON and uploaded artifact.
4. Inspect the new Run/artifact at its exact SHA; then remove the temporary workflow and verify its absence. Preserve Run `39299680243` as historical failure.
5. This establishes synthetic authoring/runtime behavior only, not canonical Stage 13 acceptance or project completion.

**Authorization boundary:** existing owner scope `docs/stage13/OWNER_SCOPE_AUTHORIZATION_20261017.md` blob `c0b8e5c509ef5ccc2c747504adfab89d2c3c0ee4` authorized a temporary synthetic-only workflow, not modification of test files. The proposed fixture edit therefore remains pending explicit owner approval. No test/workflow change was made in this R4 report.
