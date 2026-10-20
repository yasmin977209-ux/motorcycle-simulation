# R4 — Integer-exact representative selection

**Date:** 2026-10-20  
**Mode:** Candidate-only code repair; no source/data mutation, production simulation, workflow edit, or test edit.  
**Repository:** `yasmin977209-ux/motorcycle-simulation`  
**Target branch:** `tmp/cp-stage13-integration-20261020`  
**Pre-change branch HEAD:** `9f8c37a517ff566d8f576fb73fb4bcab0389b601` (live compare: identical to branch ref before this CP)  
**Pre-change code blob:** `scripts/stage13_assemble.py` = `f3b944e3d33840831fbe84248e0cb0fb42254b50`  
**Main HEAD at review:** `6a218ebe0fccf210ec18f3552b141afbdd1a49ef` (not modified)  
**Original governing reference SHA-256:** `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`.

## R4 record

| Item | Current state | Reference / decision | Branch and SHA | Governing text | Defect class | Minimum change | Authority | Acceptance | Risk |
|---|---|---|---|---|---|---|---|---|---|
| Representative selection from `Final_Net_Project_Equity` | `select_representative_trial_ids` converts integer monetary values to `float` for quantiles, nearest-value comparisons, and the MaxCase maximum. | Original reference §§14.5–14.6; project financial-integrity rule; live `docs/governance/REFERENCE_AMENDMENTS.md` Amendment-03 and `docs/governance/DECISIONS_LOG.md` D-2026-10-10-03. | Candidate branch `tmp/cp-stage13-integration-20261020`; pre-change HEAD `9f8c37a517ff566d8f576fb73fb4bcab0389b601`; code blob `f3b944e3d33840831fbe84248e0cb0fb42254b50`. | The reference requires nearest-trial selection to the linear P10/P50/P90 quantile and tie-break by smallest `trial_id`; project constraints require monetary values to remain integer-valued. Amendment-03 governs the five roles and MaxCase positive-equity selection. | `K_CODE` | Replace float monetary comparisons with exact integer-rational comparisons mathematically equivalent to `numpy.quantile(..., method="linear")`; reject non-integer financial inputs; retain existing roles, approved LossCase absolute-value rule, MaxCase highest-positive rule, and smallest-`trial_id` tie-breaks. | Candidate-only change authorized under the user’s engineering delegation; no change to `main`, reference, data artifacts, manifest, source identity, cohort, trial IDs, tests, or workflows. | Re-read the exact diff; run the existing branch-pinned focused test workflow at the resulting SHA; verify selection equivalence against the linear-quantile rule on integer cases; inspect the resulting run/artifact once. No final workbook is produced. | Low if exact rational arithmetic preserves linear-quantile ordering; mitigated by pre-change numeric-equivalence checks and the existing focused test suite. |

## Required behavior

- The exact linear-quantile target is represented by an integer numerator and denominator. For `q = q_num/q_den`, compute `h=(n-1)q`, interpolate the two adjacent ordered integer values as a rational, and compare candidate distances by integer cross-multiplication.
- P10/P50/P90 keep the reference’s nearest-trial semantics and smallest-`trial_id` tie-break.
- LossCase retains Amendment-03’s minimum `abs(Final_Net_Project_Equity)` rule; MaxCase retains highest **positive** equity with smallest-`trial_id` tie-break and fails closed when no positive equity exists.
- Reject Boolean, float, string, or other non-integer financial values rather than silently coercing them.
- Only `scripts/stage13_assemble.py` may change in the code commit. No tests or Workflows are modified.

## Pre-change mathematical check

A local, non-production comparison exercised 1,680 deterministic synthetic integer cohorts (sizes 1–39 plus 50, 100, and 550; negative, positive, and duplicate integer values) for P10/P50/P90. The integer-rational comparator selected the same `trial_id` as the current NumPy linear-quantile comparator in every tested case (0 mismatches). This validates the comparison method, not the repository runtime or the source-data cohort.

## Status at R4 creation

**Change not yet applied.** Test, read-back, and candidate acceptance remain pending. This R4 does not clear Gate A, `SOURCE_SHA_DRIFT`, partner memo fields, Stage 11 topology, the C050_G000 provenance conflict, the seven-file package, independent delivery audit, or Release authorization.


## Execution and acceptance evidence — 2026-10-20

The minimum code change was applied after the R4 was recorded.

- Code commit: `5d6b3640176162cf206ba65838d623968fd7cb5c`
- Changed code path: `scripts/stage13_assemble.py` only
- Resulting source blob: `4472547232ffef95d15c864b7bf1128a6f868301`
- Read-back: GitHub read-back content equals the intended replacement; commit diff confirms no tests or Workflow files were changed in that code commit.
- Workflow: [Run 39469781828](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39469781828), exact tested HEAD `5d6b3640176162cf206ba65838d623968fd7cb5c`, branch `tmp/cp-stage13-integration-20261020`, conclusion `success`.
- Artifact: `12286606754`, `stage13-integration-evidence-39469781828`, 5,085 bytes; GitHub API digest and downloaded bytes both SHA-256 `7c999d9e46fbb711244e68c3677b1d71e19a761a96a82bd0747f29fad0cd49aa`.
- Artifact read-back: 9 files; `pytest.log` is exactly `50 passed in 23.17s`; `pytest_exit_code.txt` is `0`; `tested_head_sha.txt` is the SHA above. `pytest.junit.xml` records 50 tests, 0 failures, 0 errors, 0 skipped.
- `code_identity.json` confirms the tested assembler Git blob is `4472547232ffef95d15c864b7bf1128a6f868301`; the reference SHA and pinned source SHA matched the expected values. Run context expressly says synthetic/compatibility tests only, production cohort not loaded, no workbook built, no simulation/trial generated, historical data not modified, `main` not modified, and delivery not accepted.

**Disposition:** `PASS_SCOPED` for the listed focused synthetic/compatibility tests on the exact tested SHA. The later candidate-branch continuity commit is documentation-only; it does not alter the tested code/test blobs. This run is not a full repository pytest result, canonical production cohort acceptance, 185-sheet workbook acceptance, Gate A production PASS, seven-file delivery acceptance, or Release authorization.
