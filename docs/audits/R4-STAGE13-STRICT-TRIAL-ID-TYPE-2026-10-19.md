# R4 — Stage 13 strict representative Trial-ID type validation — 2026-10-19

## Scope and current identity before change

- Candidate branch: `tmp/cp-stage13-excel-compat-20261017`
- Candidate HEAD before change: `52a7c3b9a4151ab26968b55287e518c590426ba6`
- Candidate `scripts/stage13_assemble.py` blob: `8bb785606bc268cd1ad8671518bfa96e3d009794`
- Candidate `tests/test_stage13_assembler.py` blob: `976ebc8365db7f2380f15317c677990e34a1269c`
- Current main HEAD: `7c41ac64c4b599f4e1d6a50be055f82cdd87a7b5`
- Owner scope record: `docs/stage13/OWNER_SCOPE_AUTHORIZATION_20261017.md`, blob `c0b8e5c509ef5ccc2c747504adfab89d2c3c0ee4`. This CP does not modify tests or workflows and does not run the workflow.

## R4 table

| Item | Current | Reference / decision / branch | Controlling requirement | Ruling |
|---|---|---|---|---|
| Representative summary Trial ID type | `_trial_id(summary)` converts with `int(...)`; later equality allows numeric type coercion. | Candidate assembler blob `8bb785606bc268cd1ad8671518bfa96e3d009794`; selected IDs are the exact assigned representative trial IDs. | D-2026-10-10-03 defines the representative roles; each payload must bind to the selected trial row. The project requires exact trial identity and fail-closed validation. | `K_CODE`: values such as `1.0` or `true` can compare equal to integer `1` if the raw type is not checked. |
| Daily row Trial ID type | Current condition is `daily_row.get("trial_id") != expected_id`, which accepts `True == 1` and `1.0 == 1`. | Same candidate blob and validator at lines 1326–1331. | A daily payload row must belong to the selected integer Trial ID; type coercion is not identity proof. | `K_CODE`: reject booleans and non-integer values before equality comparison. |
| Minimal repair | Require `type(summary["trial_id"]) is int` and `type(daily_row["trial_id"]) is int`, then compare to the expected ID. | Candidate branch only; no main change. | Keep the selected IDs, trial rows, data packages, source SHA, seed/RNG, cohort, sampling, and representative assignment unchanged. | Authorized code-only candidate repair. No tests/workflows changed. |
| Verification boundary | Exact candidate head has no recorded Actions run; runtime authorization conflict remains. | No test file or workflow modification is in scope. | Do not claim PASS without exact-head verification. | Static read-back only; runtime validation remains pending. |

## Acceptance criteria

1. Integer Trial IDs equal to the expected selected ID continue to pass.
2. Boolean, float, string, missing, or mismatched Trial IDs fail closed with the existing stable mismatch errors.
3. Summary and daily row identity are checked before any date or terminal-accounting checks.
4. No test, workflow, reference, state, source data, Parquet, trial ID, seed/RNG, sampling policy, cohort, historical artifact, main, or release is modified.

This R4 record was written and read back before the code change. The proposed change is limited to the candidate assembler source file.
