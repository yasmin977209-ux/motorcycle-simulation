# R4 — Stage 9C status reconciliation without overwriting historical report — 2026-10-22

## Scope

- Base/main HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- Candidate branch: `tmp/cp-stage9c-status-reconciliation-20261022`.
- Classification: `K_DOC / EVIDENCE RECONCILIATION ONLY`.
- Existing historical report: `docs/stage9c/STAGE9C_REPORT.md`, base blob `81fb79720988cfe261fa6d8d29371e616f9f9850`.
- Canonical state source: `state.json`, base blob `2178260bb18efeb81437486f13b6d10cf5e85936`, which records `full_stage9c_status=PASS` based on `Stage9C_reaudit_C1_to_C6` since 2026-10-12.
- Merged evidence record: PR #38, merge commit `74b103cd782c9e75e210a090c94fbcb4b01844c4`; its scope is read-only reassessment of the canonical 9,005-trial Stage 9A cohort against the existing Stage 12 ledger.

## Reconciliation objective

The historic Stage 9C report retains its then-current `PARTIAL` verdict. State records a later evidence-only `PASS` for gates C-1..C-6. This candidate adds a separate dated addendum recording that chronology and exact evidence; it must not rewrite/delete the old verdict or upgrade any separate gate/delivery status.

## Binding evidence reported in current main state

- Source SHA: `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`; master seed `20270101`.
- Cohort: 25 scenarios, 9,005 canonical trials (20 non-C100 scenarios at trial IDs 1..450 plus five C100 scenarios at trial ID 1).
- Exact trial hashes: 9,005/9,005 matched, zero mismatches; 25/25 scenario reports and 20/20 aggregate gates passed.
- Stage 12 is a verified 11,005-trial superset with 22,546,465 daily rows; the canonical Stage 9A subset comprises 18,449,224 existing rows. The roll-forward report checks 22,546,465 rows with zero violations; closure/balance report checks 22,546,465 with zero violations.
- CP-D exact XLSX gate: 500/500 comparisons, zero mismatches, 185 worksheets, zero formula cells and zero Excel-error cells. This evidence remains separately scoped to numeric precision.
- The old broad raw-pytest diagnostic Run `38164248220` remains `11 failed, 338 passed, 1 skipped, 1 warning`; it is out-of-inventory evidence and is not relabelled as repository-wide PASS.

## Explicit non-claims and exclusions

This addendum does not certify the entire test suite, production Gate A provider, Gate B overall final stability, Stage 11 topology, Stage 13 assembly, C050_G000 manifest provenance, missing Partner 1/2 MaxCase daily memo balances, or the seven-file final delivery. It creates no new trial evidence, does not rerun simulation/checkpoints, and changes no source SHA, seed/RNG, trial IDs, cohort, historical data, Parquet, manifest, workbook or state.

The historical `STAGE9C_REPORT.md` is not edited. No automated status promotion occurs. Main remains unchanged until a separately reviewed merge.

## Acceptance

- New file has dated chronology: historical PARTIAL remains as the prior assessment; later PASS is bounded to C-1..C-6 evidence re-audit.
- Exact reported values above reconcile to current main state and merged PR #38 evidence.
- No unreferenced or invented measurements are added.

## Status

`PENDING_STATIC_READBACK`. This is documentation reconciliation only, not overall project acceptance.
