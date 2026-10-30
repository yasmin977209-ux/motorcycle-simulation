# D0_INPUT_AUDIT — Stage D S6 Input Verification and Preflight

**Decision:** `D0_COMPLETE / PASS_SCOPED_WITH_LIMITATIONS`  
**Delivery classification:** `T2_INTERIM / NOT_FINAL_BLOCKED`  
**Audit date:** 2026-10-30/31 (GitHub live recheck; historical local artifact checks are explicitly identified)  
**Repository:** `yasmin977209-ux/motorcycle-simulation`  
**Authorized branch:** `tmp/cp-v240-stage-d-s6-deliverables-20261030`  
**Pre-audit HEAD:** `67763f3156c00db5beaa568d8b78a055c5a8f968`

## 1. Executive decision

D0 input inventory and preflight are complete using the previously completed byte-level artifact verification and the recorded Stage C audit, with a fresh GitHub live recheck of the Stage D branch, main, continuity document, owner decision, and Stage D Actions runs.

The immutable inputs are identified and their archive SHA-256 values, sizes, and ZIP integrity checks were previously recomputed from downloaded bytes and matched. The Stage C full-logging audit establishes the representative dataset and its bounds. The aggregate does **not** contain all per-trial detailed ledgers for all 48,000 S6 trials; it contains aggregate/statistical datasets. Detailed daily/event/accounting records are available for the 105 selected unique representative keys only.

Therefore D0 is complete as an **input audit**, but it does not certify complete production-detail coverage. D1 may proceed only with source-bounded behavior: use aggregate statistics where present, use the 105 representative logs only as representative evidence, and preserve `MISSING_EVIDENCE` for any unprovided scenario/trial detail. No missing values may be synthesized or backfilled. This D0 result does not authorize simulation, Trials, N=4800, final acceptance, or Stage 13 reuse.

## 2. Live GitHub state

| Item | Live value | Status |
|---|---|---|
| main HEAD | `c6e54349a5e94f65d5aa9f83141f225d777bb474` | VERIFIED_LIVE |
| Stage B branch | `tmp/cp-v240-decision-and-validators-20261030` | VERIFIED_LIVE |
| Stage B HEAD | `a8d7e933cf9a3986c08bc49b7a10f39f0bd498d2` | VERIFIED_LIVE |
| Stage C branch | `tmp/cp-v240-stage-c-rep-full-logging-20261030` | VERIFIED_LIVE |
| Stage C HEAD | `42389fe4ef5df1b2412339b78660c75845cca09d` | VERIFIED_LIVE |
| Stage D branch | `tmp/cp-v240-stage-d-s6-deliverables-20261030` | VERIFIED_LIVE |
| Stage D pre-audit HEAD | `67763f3156c00db5beaa568d8b78a055c5a8f968` | VERIFIED_LIVE |
| Stage D workflow runs | 0 | VERIFIED_LIVE |
| Stage D in-progress runs | 0 (no Stage D runs exist) | VERIFIED_LIVE |
| main modified by D0 | No | VERIFIED_LIVE |

The current branch has no Stage D Builder, number registry, Excel deliverables, DOCX reports, or Stage D audit implementation at the pre-audit HEAD. No local Git working-tree status is claimed.

### Continuity and owner decision

- `docs/PROJECT_CONTINUITY.md` Git blob SHA-1: `a08cc8498350d40912ddd4506870b3a3dff22edf` — VERIFIED_LIVE.
- Recorded SHA-256 of continuity content: `787d90a4cc47376a00ea535bc1da98ec5495013b0d224143e2c417447bb21746` — REPORTED_ONLY as a byte-level value; not recomputed during this live API read.
- Owner decision: `D-2026-10-30-REFERENCE-V2.4.0`, `APPROVED_BY_OWNER`, effective 2026-10-30.
- Decision file blob SHA-1: `58f89bc016523f1350345428b4a224ac42a8b130` — VERIFIED_LIVE.
- Governing v2.4.0 SHA-256: `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`.
- Preserve `K_SPEC / DOCUMENT_STATUS_CONFLICT`: explicit owner decision says approved, while approval template/cover still shows pending.
- v2.3 remains S6 historical execution reference; v2.3.1 remains `CLOSED_UNAPPROVED_CANDIDATE`. Stage 12/13 lineage is not an S6 source.

## 3. Immutable artifact inventory

The three artifacts below were downloaded and checked in the prior byte-level audit. Their actual SHA-256 values matched the expected values; ZIP CRC/integrity tests passed and extraction succeeded. These local checks are recorded as `VERIFIED_LOCAL (prior audit)`, not represented as newly recomputed during the current API-only recheck.

| Input | Artifact / Run | Size (bytes) | Expected and previously computed SHA-256 | ZIP integrity |
|---|---:|---:|---|---|
| S6 N=2400 aggregate | 12852969854 / 40773412377 | 9,357,996 | `ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54` | PASS — VERIFIED_LOCAL (prior audit) |
| Full Logging | 12998778418 / 41098699740 | 310,827,203 | `403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb` | PASS — VERIFIED_LOCAL (prior audit) |
| C100 deterministic reuse | 12630457193 / 40263424595 | 361,733 | `c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79` | PASS — VERIFIED_LOCAL (prior audit) |

The earlier archive inspection confirmed successful ZIP reading/extraction and the archive/member checks recorded in the previous audit. Individual duplicate-name/path-traversal scan output is not separately retained in the continuity evidence; do not claim a new path-safety scan from the current API read. Re-run that defensive scan in the isolated D1 input reader before extraction to a writable destination.

### Aggregate archive members

The N=2400 aggregate ZIP contains seven members:

| Member | Size (bytes) | SHA-256 |
|---|---:|---|
| `manifest.json` | 63,828 | `9ad19a904a21d4f8d4426ef913dde95d69b8227f9cb2414c477281421cef4798` |
| `c100_reuse.json` | 804 | `4bc87f0492a1e668249df0f44d3c6ebcb58b55465ac21b1fc4415bd3eceab3bc` |
| `daily_distribution.parquet` | 4,881,090 | `9619fc94e371da073a622f8f0fcd28786caf79fac47697cca2bfadbb469e4903` |
| `trials_summary.parquet` | 4,578,172 | `66c8c4530073dba14e4082eb13ab492d304fa6841e3db08ae6c38509de66d522` |
| `number_registry.json` | 320,474 | `6a8fbb9aa249fa8dc678b14317b44eefdc26cd0e1b96633a9915721e2399d0e9` |
| `stability_history.json` | 805,106 | `549db3a6aab8519d701e9351d3e997f30dc19831c15b7e1dffe4a1fddb5c1ba9` |
| `statistical_evaluation.json` | 810,178 | `37ab2c98530c98015eced5e8cc4bb4e8735862e6a5fb23fa28fb36f4fd9f9864` |

These member hashes were computed from extracted bytes in the previous audit. The aggregate manifest declares 20 random S6 scenarios and five C100 deterministic scenarios; `source_run_metadata.sha256` is null, so the source-run metadata hash remains `MISSING_EVIDENCE`.

## 4. Source, cohort, seed and separation

| Population | SOURCE_SHA | cohort_id | Seed / classification | Status |
|---|---|---|---|---|
| S6 random cohort | `da1a9ea9b5cd789c944de3f07b08395bb67c49e7` | `s6-v23-da1a9ea9` | MASTER_SEED=20270101 | VERIFIED in aggregate and Stage C evidence |
| C100 reused cohort | `965281d52441cd0d4b744e211c9f68ee4cdc3753` | `c100-v23-s4-20261026-965281d5` | `CROSS_COHORT_DETERMINISTIC_REUSE` | VERIFIED in C100 reuse evidence |
| Historical Stage 12/13 | `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b` | historical lineage | not an S6 input | MUST REMAIN SEPARATE |

C100 records also identify five scenarios, 300 trials per scenario, `n_unique_paths=1`, `rerun=false`, and `REUSED_READ_ONLY`. Preserve original C100 source/cohort identity in every derived record and disclose the cross-cohort classification. Do not count C100 as random S6 production evidence.

## 5. Reconciled counts and schemas

The final Stage C run `41098699740` tested SHA `e3c2098df9fc5dbc126eb1e77ad35c493ff3ac70` and completed successfully. It established:

| Measure | Verified value |
|---|---:|
| Role assignments | 125 |
| Unique (scenario_id, trial_id) keys | 105 |
| Unique S6 keys | 100 |
| Unique C100 keys | 5 |
| Duplicate role assignments | 20 |
| Daily rows in representative Full Logging | 216,253 |
| Event rows | 24,545,842 |
| Roll-forward checks | 1,297,518 |
| Representative trial manifests / sidecar audits | 105 / 105 |
| Fingerprint matches | 105 / 105 |
| Balance mismatches | 0 |
| Roll-forward mismatches | 0 |

The 125 assignments are not 125 unique trials. Deduplication is by `(scenario_id, trial_id)`.

The 216,253 daily rows were checked in the prior Stage C audit: all had `s6-daily-balance-v1`, all 14 required accounting fields were present/non-null, dates were continuous, and both Partner1 and Partner2 balances were present. The 105 sidecar audits reported 30,170 asset rows, 93,902 claim rows, 117,639 contract rows, 117,639 guarantor rows, 117,639 tenant rows, and 9,543 receivable rows.

Stage C tests: `43 passed, 1 skipped` for S6 validators/path identity and `7 passed` for acceptance tests 127,159,160,161,174,180,181. These are Stage C results only. Stage D required tests 175,176,179,180,181,182,183,186 remain `NOT_RUN` as a Stage D suite.

## 6. Trial manifest reconciliation

The evidence is consistent for representative full logging, but the original status fields disagree:

| Layer | Count | Recorded status | Meaning |
|---|---:|---|---|
| Original `trial_manifest.json` | 105 | `WRITTEN_PENDING_POST_WRITE_AUDIT` | Preserved original pre-audit status |
| `post_write_audit.json` sidecars | 105 | PASS | Independent post-write integrity/accounting audit |
| Root `representative_full_logging_manifest.json` | 1 | `PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING` | Root-level scoped result |
| Trial fingerprint comparison | 105 | 105/105 match | Identity/content match for selected keys |

The root manifest SHA-256 is `4c98ff56f5af27fa5e259153d56fe1015b34c834e6a924b7af2e5d15af557fdd`. The 105 sidecar audits passed; trial fingerprints and source/audit hashes matched the root manifest in the prior audit. Individual per-file SHA values remain in the immutable root manifest and sidecars; do not rewrite them or overwrite original trial manifest statuses.

**Read-only normalized status for derived Stage D views:** `PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING`, only where the specific key has a passing sidecar, root-manifest membership, source identity match, and fingerprint match. This is a derived interpretation; it does not mutate the original manifest. Preserve `K_SPEC / TRIAL_MANIFEST_STATUS_CONFLICT` as an audit issue.

## 7. Scenario data availability matrix

The N=2400 aggregate contains aggregate/statistical and distribution data, not every per-trial daily snapshot and detailed ledger for all 48,000 S6 trials. The 20 scenario-specific source artifacts existed separately in the original source run lineage; they are not silently assumed to be embedded in the three authorized inputs. Stage C Full Logging contains only the 105 selected unique representative keys.

| Sheet family | Available evidence | Safe production boundary | Missing / prohibited |
|---|---|---|---|
| STATS | Aggregate summary, statistical evaluation, stability history, number registry | Aggregate-derived statistics, with source and checkpoint labels | Do not imply full raw-trial ledger coverage |
| DAILY | Daily distribution aggregate; representative daily rows for 105 unique keys | Clearly labeled aggregate distribution and/or representative-key daily views | All-trial daily ledgers for 48,000 trials are not present in the authorized inputs |
| ASSETS | Representative full-logging asset rows (30,170) | Selected representative keys only | Do not extrapolate to all trials |
| ACCTG | 14 accounting fields on 216,253 representative daily rows | Selected representative keys only; exact integer/Fraction/Decimal handling | Historical full 48K accounting proof remains missing |
| PARTNER | Both partner balances present on representative daily rows | Selected representative keys only | No unsupported population-wide inference |
| GUARANTEE | Representative claim/guarantor rows (claims 93,902; guarantors 117,639) | Selected representative keys only | No full-population guarantee ledger |
| CONTRACTS | Representative contract rows (117,639) | Selected representative keys only | No full-population contract ledger |

The following five historical accounting fields needed for full balance reconstruction remain missing for the historical 48,000-trial population: `Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, and `Total_Assets`. Do not backfill them. The representative 105-key logs do not close this 48K evidence gap.

## 8. Preserved conflicts and undefined items

| ID | Classification | D0 disposition |
|---|---|---|
| DOCUMENT_STATUS_CONFLICT | K_SPEC | Preserve owner decision and pending cover/template discrepancy |
| HISTORICAL_REFERENCE_HASH_CONFLICT | K_SPEC | Preserve both historical values until original reference bytes are reviewed; no cross-lineage substitution |
| TRIAL_MANIFEST_STATUS_CONFLICT | K_SPEC | Preserve originals; derived read-only normalized status only under complete per-key evidence |
| S6-CODE-ID-MAPPING | K_SPEC | Stage D explicitly names S6-CODE-08; do not invent S6-CODE-09/10 |
| Stage 9C PARTIAL vs later historical Reaudit PASS | CONFLICTED lineage | Keep in historical Stage 12 lineage; no S6 promotion |
| Aggregate `source_run_metadata.sha256=null` | MISSING_EVIDENCE | Keep null; do not reconstruct by guess |
| Historical 48K accounting fields | MISSING_EVIDENCE | No backfill |
| Full per-trial detail beyond 105 representative keys | MISSING_EVIDENCE | No extrapolation |

## 9. D0 gate and D1 boundary

**D0 audit result:** `COMPLETE / PASS_SCOPED_WITH_LIMITATIONS`.

The input identities and archive digests match the previously downloaded byte-level evidence; archive extraction and CRC integrity passed; S6/C100 identities are separated; representative Full Logging schemas and counts are established; manifest conflict is explicitly reconciled in a read-only derived view; and the exact boundary between aggregate, representative, and missing data is documented.

**D1 may begin only under these constraints:**
1. Build an independent S6 Builder/Adapter; do not import Stage 13 selection or assembly logic.
2. Consume only the three pinned immutable artifacts.
3. Before extracting any ZIP to disk, perform a defensive member-name check (absolute paths, `..`, backslashes, duplicate normalized paths, symlinks) and verify every member hash against its trusted manifest.
4. Keep S6 and C100 in separate source/cohort namespaces.
5. Use aggregate-level data for aggregate statistics; use detailed ledgers only for the 105 representative keys and label them representative.
6. Represent unsupported fields/sheets as `MISSING_EVIDENCE`; never replace them with zero, inferred values, Stage 12/13 data, or synthetic records.
7. Preserve `Fraction` for exact calculations and `Decimal(ROUND_HALF_EVEN)` for display; no financial float.
8. Keep every output `T2_INTERIM / NOT_FINAL_BLOCKED`.

No D1 code, deliverables, tests, simulation, trial, Monte Carlo, N=4800, PR, merge, release, or main-branch change was performed as part of D0.

## 10. Status vocabulary

- `VERIFIED_LIVE`: direct current GitHub API read.
- `VERIFIED_LOCAL (prior audit)`: byte-level verification recorded in the immediately preceding project audit; not recomputed in the current API-only recheck.
- `REPORTED_ONLY`: historical claim not independently repeated.
- `MISSING_EVIDENCE`: required evidence absent from authorized inputs.
- `CONFLICTED`: contradictory source statuses preserved.
- `BLOCKED`: prevents a specific broader claim, not necessarily the bounded D0 audit itself.
- `PASS_SCOPED_WITH_LIMITATIONS`: bounded preflight completion; not project acceptance.

**Final D0 disposition:** `D0_COMPLETE / PASS_SCOPED_WITH_LIMITATIONS`; overall project and delivery remain `T2_INTERIM / NOT_FINAL_BLOCKED`.
