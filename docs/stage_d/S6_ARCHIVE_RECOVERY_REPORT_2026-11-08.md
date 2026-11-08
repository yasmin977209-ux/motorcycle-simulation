# S6 Original Archive Recovery and Daily-Snapshot Schema Audit — 2026-11-08

## Executive verdict

- **Original artifact recovery:** `PASS_SCOPED` for acquisition, SHA-256 comparison, ZIP validation, member verification, and local restore of the 63 preserved archives.
- **Original complete accounting ledger:** `MISSING_EVIDENCE`.
- **D0:** remains `BLOCKED / MISSING_EVIDENCE`; no basis for `PASS_GAP_FREE`.
- **Independent durable remote retention:** not yet proven. A verified local bundle exists; Dropbox upload awaits confirmation of the exact destination and filename.

This report records a deeper follow-up to the earlier historical-source search. It does not change the D0 gate or any historical artifact.

## Exact source identity

- N=2400 Run: [40731224990](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40731224990)
- Execution commit / `head_sha`: `a23ba71f48487f3ebead99bc30039b14ef9b7609`
- `SOURCE_SHA`: `da1a9ea9b5cd789c944de3f07b08395bb67c49e7`
- `cohort_id`: `s6-v23-da1a9ea9`
- `MASTER_SEED`: `20270101`

The upstream lineage was also recovered:
- N=300 source Run [40574326793](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40574326793), execution commit `da1a9ea9b5cd789c944de3f07b08395bb67c49e7`.
- N=1200 checkpoint Run [40596643263](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40596643263), execution commit `2f77566e6c999a3af87d8aed49649dfd6ebb68ca`.
- Related N=2400 status-reconciled aggregate Run [40773412377](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40773412377), Artifact `12852969854`, execution commit `4f2f2cc16d0cb5125262088704febccbae6f50ed`.

## Artifact preservation and restore evidence

Downloaded 60 original scenario archives (20 each for N=300, N=1200 and N=2400) and three related aggregate archives. The detailed inventory records exact Artifact IDs, names, sizes, GitHub API digests and expiry timestamps in [S6 Archive Recovery Manifest](S6_ARCHIVE_RECOVERY_MANIFEST_2026-11-08.json).

Validation performed against the downloaded bytes:
- GitHub Actions artifact SHA-256 digest comparison: **63/63 match**.
- ZIP CRC and complete member read: **63/63 pass**.
- Scenario identity and declared internal member SHA-256/size checks: **60/60 pass**.
- Aggregate manifest-declared internal member SHA-256/size checks: **3/3 pass**.
- A 2,532,321,280-byte TAR bundle was created, extracted into a separate restore directory, and every restored ZIP was rehashed: **63/63 pass**.

Local bundle:
- `S6_SOURCE_ARCHIVE_RECOVERY_2026-11-08.tar`
- size: `2,532,321,280` bytes
- SHA-256: `b09d2e5e152fe3df66672d2099107bbbf807cf02c4bff7030b1e232ccf22f64d`
- classification: `VERIFIED_LOCAL`, not yet a durable remote copy.

The earliest expiry in the lineage is among the N=300 scenario artifacts on **2026-11-10**. N=1200 artifacts expire on 2026-11-26; N=2400 artifacts expire on 2026-11-27. All 63 were downloaded before those expiries.

## What the Parquet files actually contain

The 20 `daily_snapshots.parquet` files in each checkpoint were inspected through their Parquet footer/schema metadata. The field set is the same at N=300, N=1200 and N=2400:

`date`, `trial_id`, `Cash`, `Partner1_Reinvestment_Balance`, `Partner2_Reinvestment_Balance`, `Capital`, `Retained_Earnings`, `Net_Equity`, `Active_Bikes`, `Owned_Transferred_Bikes`, `Pending_Claims`, `Final_Close_Date`, `scenario_id`, `source_sha`, `cohort_id`, `schema_version`.

Total daily-snapshot rows across the 20 scenarios:
- N=300: **12,291,768** rows.
- N=1200: **49,162,656** rows.
- N=2400: **98,323,918** rows.

Despite the large row counts, these are not full balance-sheet ledgers. All five protected historical fields are absent from the stored schema:
- `Accounts_Receivable`
- `Accumulated_Depreciation`
- `Gross_Bike_Assets`
- `Guarantee_Claim_Receivable`
- `Total_Assets`

This is corroborated by the execution source itself: [`monte_carlo.py` at the exact N=2400 execution commit, lines 78–112](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/a23ba71f48487f3ebead99bc30039b14ef9b7609/monte_carlo.py#L78-L112). Its `_daily_snapshot` writer explicitly emits the limited projection above and does not write the five protected fields. Therefore the missing values cannot be recovered from these Parquet files by relabeling them or inferring them from `Net_Equity`.

## Source metadata findings

A related metadata record does exist:
- [`docs/evidence/s6_n300_source_run_metadata.json`](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/a23ba71f48487f3ebead99bc30039b14ef9b7609/docs/evidence/s6_n300_source_run_metadata.json)
- Scope: original N=300 source Run `40574326793`, not the N=2400 source-run metadata object.
- Git blob SHA-1: `a93b5c7d4337d5297dad61793bb862cb5fa4a8a3`
- SHA-256 of fetched UTF-8 bytes: `a52657b0b5ffe281500a1c028f5396b9c91e3932267816d0e5c0069927c420a4`
- size: `33,467` bytes
- containing commit: `a23ba71f48487f3ebead99bc30039b14ef9b7609`

This file documents the N=300 source run and job-log hashes. It is not interchangeable with N=2400 metadata. The N=2400 status-reconciled aggregate manifest still records `source_run_metadata.sha256: null`.

## External retention status

- Dropbox is the owner-approved provider, with existing rescue folder `/Motorcycle-Simulation-Rescue-2026-11-05`.
- The folder is live and readable. Proposed unique archive filename: `S6_SOURCE_ARCHIVE_RECOVERY_2026-11-08.tar`.
- Upload has not been attempted because the Dropbox upload workflow requires explicit confirmation of the exact path, filename and content summary.
- The earlier OneDrive attempt collided with an existing filename (`409 nameAlreadyExists`); a previous raw readback returned `403 Database Is Read Only`. Neither result proves that the existing OneDrive copy matches the newly downloaded GitHub bytes.
- A second independent durable failure domain and byte-level readback/restore are still unproven.

## Gate and safety disposition

D0 remains `BLOCKED / MISSING_EVIDENCE`. The original S6 archives are now locally recoverable, but they do not contain the five full-balance fields, and N=2400 `source_run_metadata.sha256` remains null. The 98,323,918 daily snapshot rows do not substitute for the missing all-48K full accounting records.

No new Trials, Simulation, Monte Carlo, N expansion, N=4800, backfill, zero-fill, inferred accounting values, identity changes, historical artifact replacement, main write, merge, Release or final-acceptance declaration occurred.

## Next actions

1. Obtain owner confirmation for upload to the approved Dropbox rescue folder using the proposed exact filename and TAR content.
2. Upload, download the stored bytes again, compare SHA-256 and size, and run a restore test from Dropbox.
3. Prove a second genuinely independent durable copy with raw-byte readback and restore.
4. Continue searching only for original source records and metadata tied to the exact identity. If they were never captured/preserved, D0 cannot be promoted under the current requirements.
