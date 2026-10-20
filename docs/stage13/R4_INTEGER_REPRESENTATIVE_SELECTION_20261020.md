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
