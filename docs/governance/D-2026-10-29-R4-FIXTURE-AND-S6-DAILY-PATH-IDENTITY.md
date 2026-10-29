# R4 fixture deviation and S6 daily balance/path-identity contract

**Date:** 2026-10-29  
**Status:** OWNER-DIRECTED IMPLEMENTATION DECISION; NOT PRODUCTION ACCEPTANCE  
**Protected refs:** `main` remains read-only; changes limited to the R4 and S6 temporary branches.

## R4 governance deviation and fixture policy

The prior R4 workflow's inline builder called `monte_carlo.run_single_trial("C100_G100", 1, master_seed=20270101)` and sequential/parallel `C070_G100` trial IDs `1..3`. Both `push` and `pull_request` triggered the same SHA, Runs `40798707550` and `40798713596`. Both ran `517 passed, 1 skipped, 1 warning`, but neither retained `results_stage5` as an artifact.

The revised candidate removes trial-building, keeps one PR trigger plus manual dispatch and a concurrency guard, refuses unreviewed fixture files, and excludes tests 127, 159, 160 and 161 while the immutable bundle is missing. Those tests are `NOT_EXECUTED / MISSING_EVIDENCE`, not passes. Fixtures can only come from a retained immutable approved artifact with source Run/artifact/digests/tested SHA/source/cohort/schema/seed/trial-range provenance. No completed Trial may be replayed to create fixtures; in-memory synthetic rows are allowed only for pure validator tests and are never production/Golden inputs.

## Daily accounting schema and invariant

The daily row contract is `s6-daily-balance-v1`, separate from model schema `v2.3` and manifest schema `s6-first-checkpoint-v2`. Persist rows after day-end M1–M17 from `constants.PROJECT_START_DATE` through final close. All monetary/accounting fields are strict integers. Every row checks:
- `Net_Bike_Assets = Gross_Bike_Assets - Accumulated_Depreciation`;
- `Total_Assets = Cash + Accounts_Receivable + Guarantee_Claim_Receivable + Net_Bike_Assets`;
- `Total_Equity = Capital + Retained_Earnings = Net_Equity`;
- `Liabilities = 0`;
- `Total_Assets == Total_Equity`, `Balance_Difference == 0`.

Exact row fields plus source/cohort/scenario/schema identity, integer fields, date continuity and terminal-close marker are validated. A schema alteration requires version bump/review.

## Path fingerprint and identity

The **content-path fingerprint** hashes canonical daily content ordered by date and excludes trial/scenario/source/cohort/model-schema identity keys so equal trajectories count once; it retains the daily-balance schema version. The distinct **identity-bound fingerprint** hashes an envelope containing that content hash plus SOURCE_SHA, cohort, MASTER_SEED, RNG stream (`Cxxx` collection-level), scenario/trial IDs, model/daily schema, start date, row count and date span. Financial TrialResult fingerprint, RNG checksum/draw count/checksum fingerprint, content path and identity-bound map are never substitutes.

## Historical S6 status

The old S6 N2400 daily snapshots omit five required fields: `Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Total_Assets`. They remain immutable and cannot be inferred. Resume/base loaders reject v1 manifests before any new Trial; historical aggregate rows remain visible but full balance/path identity is `MISSING_EVIDENCE`. Mixed legacy/v2 manifests are rejected. Current config remains N=2400 / IDs 1201..2400; no N4800 is authorized, and no RNG/seed/threshold/financial result is changed.

| Item | Execution | Evidence | Disposition |
|---|---|---|---|
| R4 replay correction | Source edit executed; CI pending | Old builder and same-SHA runs verified | No Trial builder; four fixture tests not executed |
| Immutable fixtures | Not executed | MISSING_EVIDENCE | No trusted bundle located |
| New balance/path contract | Implemented; CI pending | Awaiting Actions | Strict post-write balance and dual fingerprints |
| Historical S6 N2400 full balance | Not executed | MISSING_EVIDENCE | No reconstruction/backfill |
| N4800/final acceptance | Not executed | BLOCKED | Source/schema/path preflight and independent Golden required |
