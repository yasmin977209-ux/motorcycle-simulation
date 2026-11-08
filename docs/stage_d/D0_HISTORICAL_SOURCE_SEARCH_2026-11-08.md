# D0 Historical Source Search — 2026-11-08

## Executive result

**D0 remains `BLOCKED / MISSING_EVIDENCE`; no `PASS_GAP_FREE` verdict is justified.**

The search found the original S6 N=2400 execution artifacts, but did **not** find the original full daily accounting ledgers, a verifiable original `source_run_metadata.sha256`, or the five missing full-balance fields. Therefore the historical source is **partially recoverable, not complete**. This is not evidence that no such records exist anywhere; it means they were not found in the accessible repository, GitHub Actions artifacts, OneDrive rescue folder, or Dropbox rescue folder examined here.

## Live Git state

- Repository: `yasmin977209-ux/motorcycle-simulation`
- Branch: `tmp/d1-rebuild-20261101`
- Search starting HEAD: `bcca6c20de63b4bd4d8abfea4e86c66a42e89f4a`
- `main`: `01a6f79eedc522bb734ed9c5ea31beee581f2468` (read-only; unchanged)
- Prior D0 exact-SHA audit: Run [42424755294](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42424755294), tested SHA `beb1b83656bfdd15206427a7e4ce1575d654e588`, 27 reports; 7 `PASS_SCOPED`, 20 `BLOCKED`; aggregate `BLOCKED`.

## Search scope and findings

### 1. GitHub repository tree and code search

- Inspected the complete recursive tree at the starting HEAD: 667 entries, `truncated=false`.
- Located D0 validators, S6 schema/path validators, aggregate/replay audit scripts, evidence registers, the 2026-11-06 original-artifact inventory, and the E2 accounting evidence audit.
- No original all-48K daily-ledger Parquet/SQLite/CSV source file or full original source metadata file was found in the repository tree.
- Search terms included `daily ledger`, `daily snapshots`, `S6 full accounting`, `trial daily accounting`, `S6 N=2400 ledger`, `source_run_metadata`, and the five required accounting fields. Search results surfaced contract/code references, not a missing original ledger payload.
- `docs/evidence/s6_n300_source_run_metadata.json` is an N=300 source and is not interchangeable with the S6 N=2400 identity.

### 2. Original S6 execution artifacts — GitHub Actions

Original run [40731224990](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40731224990) still exposes 20 scenario artifacts (individually successful source jobs in the historical audit), total **1,531,244,201 bytes**. The exact artifact IDs, names and sizes are listed below. Their expiration dates currently fall between 2026-11-27 17:23:02Z and 18:57:55Z.

| Artifact ID | Original scenario archive | Bytes | OneDrive observation |
|---:|---|---:|---|
| 12842976168 | `s6-n2400-C050_G070-40731224990.zip` | 97,639,363 | OneDrive exact-size match |
| 12842638708 | `s6-n2400-C050_G000-40731224990.zip` | 94,849,558 | OneDrive exact-size match |
| 12842495430 | `s6-n2400-C050_G030-40731224990.zip` | 97,589,544 | OneDrive exact-size match |
| 12842099758 | `s6-n2400-C050_G050-40731224990.zip` | 96,741,246 | OneDrive exact-size match |
| 12840482357 | `s6-n2400-C030_G070-40731224990.zip` | 54,426,987 | OneDrive exact-size match |
| 12840360793 | `s6-n2400-C030_G050-40731224990.zip` | 52,997,909 | OneDrive exact-size match |
| 12840210926 | `s6-n2400-C030_G030-40731224990.zip` | 51,887,261 | OneDrive exact-size match |
| 12839945046 | `s6-n2400-C070-G100-40731224990.zip` | 82,683,835 | OneDrive exact-size match |
| 12839875625 | `s6-n2400-C085_G000-40731224990.zip` | 74,384,364 | OneDrive exact-size match |
| 12839361726 | `s6-n2400-C070_G070-40731224990.zip` | 82,776,281 | OneDrive exact-size match |
| 12839102296 | `s6-n2400-C085_G050-40731224990.zip` | 74,384,698 | OneDrive exact-size match |
| 12839062393 | `s6-n2400-C070_G000-40731224990.zip` | 82,775,948 | OneDrive exact-size match |
| 12839053751 | `s6-n2400-C030_G000-40731224990.zip` | 48,678,427 | OneDrive exact-size match |
| 12838992458 | `s6-n2400-C085-G100-40731224990.zip` | 74,297,741 | OneDrive exact-size match |
| 12838987686 | `s6-n2400-C070_G050-40731224990.zip` | 82,776,739 | OneDrive exact-size match |
| 12838354545 | `s6-n2400-C085_G070-40731224990.zip` | 74,384,935 | OneDrive exact-size match |
| 12838339633 | `s6-n2400-C085_G030-40731224990.zip` | 74,384,375 | OneDrive exact-size match |
| 12838242824 | `s6-n2400-C050-G100-40731224990.zip` | 95,527,693 | OneDrive exact-size match |
| 12838164871 | `s6-n2400-C070_G030-40731224990.zip` | 82,776,343 | OneDrive exact-size match |
| 12836747552 | `s6-n2400-C030-G100-40731224990.zip` | 55,280,954 | OneDrive exact-size match |

Other related source-lineage artifacts found:
- Aggregate run [40773412377](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40773412377): Artifact `12852969854`, 9,357,996 bytes. The preserved aggregate has `daily_distribution.parquet` and `trials_summary.parquet`, but its manifest records `source_run_metadata.sha256=null`; it is not the missing full daily accounting ledger.
- Independent artifact audit run [40761382163](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40761382163): Artifact `12850320049`, 8,731 bytes. It audits the existing source artifacts; it does not add the missing ledger payload.
- Golden accounting audit run [40784902124](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40784902124): Artifact `12859860023`, 12,420 bytes; recorded `rows_recomputed=0` and `daily_balance_reconciliation=MISSING_EVIDENCE_FOR_INDEPENDENT_RECHECK`.
- Daily equity identity audit run [40787081064](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40787081064): Artifact `12859837254`, 5,883 bytes; checks the limited `Net_Equity == Capital + Retained_Earnings` identity, not full balance-sheet coverage.
- Representative Full Logging run [41098699740](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41098699740): Artifact `12998778418`, 310,827,203 bytes; 105 representative keys only, not all 48,000 Trial/day ledgers.
- E2 run [41958935113](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41958935113) has 20 scenario replay artifacts plus an aggregate. These are **replay reconstructions**, not the original S6 source; they cannot be relabelled as original historical evidence.

### 3. OneDrive rescue folder

Live listing of `Motorcycle-Simulation-Rescue-2026-11-05` returned 85 immediate items, including all 20 original S6 scenario archive filenames. All **20/20 sizes exactly match** the corresponding GitHub artifact metadata; aggregate artifact `12852969854` is also present at 9,357,996 bytes.

This establishes presence and size agreement only. The previously attempted OneDrive raw-byte fetch returned `403 Database Is Read Only`; no independent SHA-256 of OneDrive bytes or restore test is claimed. OneDrive metadata/size is not proof that the object bytes equal the original GitHub artifact bytes.

### 4. Dropbox rescue folder

Live listing of `/Motorcycle-Simulation-Rescue-2026-11-05` returned nine immediate items plus the secondary mirror folder. It contains the D0 aggregate, representative Full Logging, C100 and D0/D4/D6 rescue packages, but **none of the 20 original S6 N=2400 scenario archives**. The secondary mirror is within the same Dropbox failure domain and is not independent storage.

## What the recovered source does and does not prove

The 20 original S6 archives are genuine historical source artifacts for the scenario outputs and remain downloadable from GitHub Actions until their stated expiry dates. The D0 exact-SHA audit already downloaded and inspected all 20; the ZIP SHA-256/CRC/restore checks passed, but every one of the 20 was blocked for required source metadata and/or complete Parquet accounting evidence. Representative logs report `metadata_sha256=MISSING_EVIDENCE` and `parquet_status=MISSING_EVIDENCE`.

The missing original elements remain:
- full daily accounting ledger coverage for all 48,000 S6 Trial identities;
- original `source_run_metadata` with a non-null, independently verifiable SHA-256 tied to the original run/source/cohort/seed;
- the following five historical full-balance fields:
  - `Accounts_Receivable`
  - `Accumulated_Depreciation`
  - `Gross_Bike_Assets`
  - `Guarantee_Claim_Receivable`
  - `Total_Assets`
- complete original Parquet schema, row-count, null, duplicate, partition and lineage evidence;
- raw-byte readback and restore from the independent durable copies.

## Why no alternative historical data was generated

The search did find the original S6 scenario archives; therefore the condition “no historical source at all” is not met. More importantly, the original archives are incomplete for the D0 acceptance contract. Generating synthetic values, inferring the five balances, zero-filling, replaying, or relabelling E2 reconstruction as original would create a different dataset, not recover the missing historical facts.

Under REV7 and the owner-approved v2.4.0 rules, backfill/inference and any substitution of replay/synthetic data for original historical evidence require a separately defined owner decision and cannot silently change D0's acceptance contract. A synthetic dataset, if separately authorized for testing, must have a new explicit synthetic identity and remain segregated; it cannot establish this historical D0 as `PASS_GAP_FREE`.

## Next safe action

1. Before expiry, preserve the 20 original GitHub ZIP artifacts in an independently accessible storage path with raw-byte readback and restore; current OneDrive copies are only metadata/size-matched.
2. Search the original producing environment/storage for the original daily accounting ledger and source metadata, keyed to run `40731224990`, execution commit `a23ba71f48487f3ebead99bc30039b14ef9b7609`, source SHA `da1a9ea9b5cd789c944de3f07b08395bb67c49e7`, cohort `s6-v23-da1a9ea9`, and MASTER_SEED `20270101`.
3. If those records never existed or cannot be recovered, retain D0 as blocked. Any proposal for a separately identified synthetic validation dataset must not be represented as original S6 or as a gap-free D0 closure.

## Actions not taken

No new Trial, Simulation, Monte Carlo, N expansion, N=4800, backfill, zero-fill, inferred accounting, SOURCE_SHA/cohort/MASTER_SEED/Trial identity change, historical Artifact mutation, main write, merge, force-push, Release or final-acceptance declaration was performed.


## 2026-11-08 — Archive recovery addendum (correction and deeper verification)

The earlier search correctly distinguished the N300 metadata file from the N2400 metadata requirement, but the original 60 scenario archives and upstream lineage have now been downloaded and independently checked. All 60 scenario ZIPs and three related aggregate ZIPs (63 total) match GitHub Actions API SHA-256 digests, pass ZIP CRC/member reads, and pass extracted-bundle restore/re-hash. The N300 metadata file is verified at [exact GitHub commit](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/a23ba71f48487f3ebead99bc30039b14ef9b7609/docs/evidence/s6_n300_source_run_metadata.json): SHA-256 `a52657b0b5ffe281500a1c028f5396b9c91e3932267816d0e5c0069927c420a4`, Git blob `a93b5c7d4337d5297dad61793bb862cb5fa4a8a3`, size 33,467 bytes. It remains N300-scoped and does not replace the N2400 metadata object, whose related aggregate manifest still records `source_run_metadata.sha256=null`.

Parquet footer inspection across all 20 scenario archives at each of N300, N1200 and N2400 confirms that `daily_snapshots.parquet` is extensive (12,291,768 / 49,162,656 / 98,323,918 rows respectively) but the stored projection excludes all five required balance fields. The exact N2400 execution writer `monte_carlo.py::_daily_snapshot` (a23ba71, lines 78–112) corroborates the omission. Thus the original archives are recoverable, but the complete historical accounting ledger is not present in these archives. D0 remains `BLOCKED / MISSING_EVIDENCE`.

Recovery report: [S6 Archive Recovery Report](S6_ARCHIVE_RECOVERY_REPORT_2026-11-08.md). Detailed 63-artifact inventory: [S6 Archive Recovery Manifest](S6_ARCHIVE_RECOVERY_MANIFEST_2026-11-08.json). Durable remote upload is still pending exact Dropbox destination/filename confirmation; no claim of permanent retention is made.
