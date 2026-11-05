# E2 Owner Decision Memo — 2026-11-05

E2 found that the preserved S6 daily projection for the 48,000-Trial cohort lacks five fields: `Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, and `Total_Assets`. The daily Net Equity identity passed in 98,323,918 rows, but the full daily `Assets == Equity` check remains unproven. The representative 105-key Full Logging set does not replace the original 48K daily artifacts.

## Choices
1. **Recover original evidence:** continue searching for immutable, identity-matching S6 records containing the five fields and complete daily postings. No history changes.
2. **Preserve the gap:** keep all five fields `MISSING_EVIDENCE` and Production Gate A `NOT_DECLARED`. This is the recommended fallback.
3. **New replacement dataset:** only by separate explicit owner decision, with a new identity and clear non-historical labeling. It cannot be presented as the original 48K history.

No backfill, inference, zero-fill, Trial run, Monte Carlo, identity change, or historical Artifact/manifest mutation is authorized here. Stage 12/13 data must not be transferred into S6.


## Forensic clarification and exact owner decision still required — 2026-11-05

The follow-up source-path inspection found why the five fields are absent: the original S6 per-day callback `monte_carlo.py::_daily_snapshot` emitted a reduced row. Although the accounting engine calculated the full snapshot in memory, the S6 artifact writer persisted the reduced callback rows as `daily_snapshots.parquet`. The original preserved daily projection therefore cannot recover the omitted values.

**No option below is selected automatically.**

- **Option A — authorize a deterministic replay reconstruction:** authorize a new execution of exactly the existing S6 scope: 20 stochastic scenarios, Trial IDs 1..2400 per scenario (48,000 total), `SOURCE_SHA=da1a9ea9b5cd789c944de3f07b08395bb67c49e7`, `cohort_id=s6-v23-da1a9ea9`, `MASTER_SEED=20270101`, using original execution code revision `a23ba71f48487f3ebead99bc30039b14ef9b7609`. Produce new immutable replay-labelled evidence; do not overwrite or alter historical Artifacts or manifests. Compare all 48,000 Trial fingerprints and every overlapping persisted daily field/date against original artifacts; require complete Trial/day coverage and `Assets == Equity` for every reconstructed daily row. A mismatch blocks acceptance. Label all output `REPLAY_RECONSTRUCTED_NOT_ORIGINAL_PRESERVED`; original history remains unchanged.
- **Option B — preserve the gap:** do not run any replay; retain the five fields as `MISSING_EVIDENCE` and Production Gate A as `NOT_DECLARED`.

Option A is a new Trial/Simulation execution and historical reconstruction. It requires explicit owner authorization; this request is not that authorization. No replay, Trial, Monte Carlo, N expansion, or data mutation has been performed.
