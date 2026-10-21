# R4 — Stage 9C status reconciliation without overwriting historical report — 2026-10-22

## Scope and baseline

- Current main HEAD at start: `7621ddefe6c971e9eb231eb2a987519c86a2cb51`.
- Candidate branch: `tmp/cp-stage9c-status-reconciliation-current-main-20261022`.
- Classification: `K_DOC / EVIDENCE RECONCILIATION ONLY`.
- Historical report retained unchanged: `docs/stage9c/STAGE9C_REPORT.md`, blob `81fb79720988cfe261fa6d8d29371e616f9f9850`.
- Current main state at start: `state.json` blob `0b7db78b2678aeea3f73f6114e69ab6802806fd3`; `full_stage9c_status=PASS` based on `Stage9C_reaudit_C1_to_C6` since 2026-10-12, merged via PR #38 at `74b103cd782c9e75e210a090c94fbcb4b01844c4`.
- This CP carries forward the already-recorded evidence-only reassessment; it does not make new measurements or rewrite the status stored in state.

## Reconciliation statement

The old Stage 9C report is a historical snapshot whose product verdict remains `PARTIAL`. A separately dated addendum is added at `docs/stage9c/STAGE9C_REAUDIT_C1_C6_ADDENDUM_2026-10-22.md` to preserve the later C-1..C-6 scoped evidence chronology. It must not edit, delete or change any verdict in `STAGE9C_REPORT.md`.

The addendum's conclusion is deliberately scoped to Stage 9C C-1..C-6; it is not a statement that the complete repository pytest suite passed or that the seven-file final delivery is accepted.

## Source-derived evidence to retain

- Canonical source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`; seed `20270101`; 25 scenarios and 9,005 Stage 9A canonical trials.
- Exact TrialResult hashes: 9,005/9,005; zero mismatches; 25/25 scenario reports and 20/20 aggregate gates passed.
- Existing Stage 12 ledger is the 11,005-trial superset with 22,546,465 daily rows; the Stage 9A subset has 18,449,224 existing daily rows.
- Stage 12 roll-forward validation checked 22,546,465 rows with zero violations; closure/balance validation checked 22,546,465 rows with zero violations.
- CP-D numeric-export gate separately passed 500/500 exact XLSX comparisons, 185 worksheets, zero formulas, zero Excel-error cells.
- Historical broad raw-pytest Run `38164248220` remains `11 failed, 338 passed, 1 skipped, 1 warning`; do not relabel it as a full-repository PASS.

## Exclusions and blockers

This is only a documentation write. It does not change `state.json`, source identity, code, tests, workflows, data, manifest, historic workbook, Parquet, seed/RNG, trial/cohort IDs, or any historical report.

Still open: production Gate A provider/coverage, missing Stage 11 topology definition, C050_G000 artifact/run provenance conflict, absent Partner1/Partner2 MaxCase daily memo balances in the 20 non-C100 cases, missing Stage 13 in main until separate review/merge, G2 runtime measurement, and full final delivery assembly/acceptance. The seven-file `FINAL_DELIVERY` remains `NOT_ACCEPTED`.

## Acceptance

- The historical report remains byte-identical.
- The added addendum only documents existing evidence and statuses.
- Candidate `state.json` remains byte-identical to current main.
- The candidate diff contains only this R4 and the new addendum.
- No run, simulation, Trial, Checkpoint, release, or automated state promotion.

## Status

`PENDING_STATIC_READBACK`; branch-only documentation candidate, no merge.
