# CP — Stage 13 synthetic fixture correction: exact-SHA runtime PASS

**Date:** 2026-10-19  
**Status:** `SYNTHETIC_RUNTIME_PASS / CANONICAL_STAGE13_STILL_BLOCKED`

## 1. Approved change

The user's explicit approval covered only the synthetic fixture and a temporary read-only workflow.

- Candidate branch: `tmp/cp-stage13-excel-compat-20261017`.
- Test file: `tests/test_stage13_assembler.py`.
- Previous blob: `976ebc8365db7f2380f15317c677990e34a1269c`.
- New blob: `eb0d7bfa8e0c4760ae168d6787239978a8230f2a`.
- Exactly two synthetic daily-row dictionaries in `daily_rows(trial)` gained `"trial_id": int(trial["trial_id"])`. No other test content was changed in that commit.
- Candidate source under test: `scripts/stage13_assemble.py` blob `71e05034bafb551aea2949adc94013e8bb23d239`, including strict exact-int validation for summary and daily `trial_id`.

## 2. Exact run and result

- GitHub Actions Run: `39304530551`.
- Tested commit: `a94ded2da52086be645bc57179c9dc54224ef8f0`.
- Job: `118238027008` (`synthetic-verify`).
- Final Run conclusion: `success`; all nine workflow steps completed successfully.
- Exact pytest output: `11 passed, 1 warning in 0.95s`.
- Warning retained: `scripts/stage13_assemble.py:311: DeprecationWarning: invalid escape sequence '\\ '`.
- Run URL: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39304530551

This result supersedes neither nor deletes the historical failed Run `39299680243` (`2 failed, 9 passed, 1 warning`); both remain in the history.

## 3. Artifact independently downloaded and inspected

- Artifact ID: `12212817086`.
- Name: `stage13-synthetic-compat-a94ded2da52086be645bc57179c9dc54224ef8f0`.
- ZIP size: `47,489` bytes.
- ZIP SHA-256: `264046ab52fde22de24450ad549d2ca3b71721cb7fd311171600918a0777f246`, matching the GitHub API digest.
- ZIP members and SHA-256:
  - `stage13_synthetic_demo.xlsx`: 135,847 bytes; `5fa59bd2a5c82d631e05eb3c75d97679db3fddadd94a75424220c26ac6cc9282`
  - `synthetic_audit.json`: 1,644 bytes; `f22058ae60227a085bfb6dbf43a65e62bf488e446a4eccd94bcc2e454b5ded88`
  - `pytest.log`: 510 bytes; `ec43f7231dfac0ba3edc3a74c5ebbbd1246427e70bbd4884101cbd82351787a4`
  - `scope-metadata.json`: 610 bytes; `5ea9083908fd3f1b9eb15fb9f612202d11a7bf16402d8742473db46b0bf722cc`

### Independent workbook inspection

The downloaded workbook was opened separately with `openpyxl`, not accepted solely from the workflow's JSON assertions.

| Check | Observed result |
|---|---|
| Worksheet count | 185 |
| Unique worksheet names | 185 |
| Representative summary rows | 25 |
| Representative scenarios | 5 (`C100_G000`, `C100_G030`, `C100_G050`, `C100_G070`, `C100_G100`) |
| Role labels | `P10`, `P50`, `P90`, `Loss Case`, `Max Case` |
| Formula/error cells | 0 |
| Workbook SHA-256 | `5fa59bd2a5c82d631e05eb3c75d97679db3fddadd94a75424220c26ac6cc9282` |
| Workbook size | 135,847 bytes |

The strict-type audit independently recorded rejection of `bool`, `float`, and `str` values for both summary and daily `trial_id` (six negative cases). Scope metadata confirms synthetic fixture only: no canonical or historical payload read, no Monte Carlo, Trial, Checkpoint, seed/RNG/sampling or source-identity change, and no main/merge/release action.

This proves bounded synthetic authoring/runtime behavior on the exact tested commit only. It does not prove the canonical dataset's full 185-sheet workbook, daily accounting reconciliation, real MaxCase payload completeness, or overall Stage 13 acceptance.

## 4. Temporary workflow cleanup and branch boundary

- The temporary workflow blob `c0be07252d34b9f77c744df49c178e8d9709f488` was deleted after inspecting the exact run and artifact.
- Cleanup commit: `c21b295cb3c421708e90e1f114a36d1c36b9e5dd`.
- Read-back confirmed the temporary workflow file is absent from the candidate branch.
- Candidate branch retains the approved fixture change and R4 document. It was not merged.
- `main` remains HEAD `7c41ac64c4b599f4e1d6a50be055f82cdd87a7b5`; `state.json` blob remains `2178260bb18efeb81437486f13b6d10cf5e85936`; stage/status remains `12-CLOSED / FINAL_DELIVERY_BLOCKERS_OPEN`.
- PR #46 remains open, draft, and unmerged.
- No source-of-truth data, Parquet, trial ID, cohort, seed/RNG, sampling policy, reference, state, release, or delivery file was modified.

## 5. Remaining blockers

1. Distinct MaxCase still lacks a verified full daily payload in the inspected official/enriched packages. No trial replay or fabricated daily rows were performed.
2. C050_G000 manifest provenance correction is candidate-only and does not unblock the missing MaxCase payload.
3. Stage 10 JSON newline fix still has only isolated-function validation, not exact-SHA repository runtime validation.
4. Historical failed Runs are preserved.
5. No canonical production workbook or final seven-file delivery was generated or accepted.

Overall project status remains `FINAL_DELIVERY_BLOCKERS_OPEN`.
