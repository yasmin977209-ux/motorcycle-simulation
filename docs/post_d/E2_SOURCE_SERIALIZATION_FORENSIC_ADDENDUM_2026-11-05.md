# E2 Source-Serialization Forensic Addendum — 2026-11-05

## 1. Scope and authority
- Repository: `yasmin977209-ux/motorcycle-simulation`; working branch: `tmp/d1-rebuild-20261101`.
- Review baseline HEAD: `ed9b67f49dfeb80f27be9b7150d9ed37c1cfc68e`; main HEAD: `01a6f79eedc522bb734ed9c5ea31beee581f2468`.
- Read-only forensic tracing of the original S6 daily accounting persistence path. No simulation, replay, Trial, Monte Carlo, backfill, zero-fill, identity change, historical Artifact/manifest mutation, or workflow dispatch.
- The live REV2 prompt library §11 was read. It permits search/reuse of original preserved S6 evidence, but requires missing fields to remain `MISSING_EVIDENCE` if not recoverable; inferred/backfilled accounting and new Trials require separate owner approval.
- Governing reference v2.4.0 and owner decision `D-2026-10-30-REFERENCE-V2.4.0` were re-read. The accounting contract requires full daily `Assets == Equity`; no proxy or alternate calculation is permitted.

## 2. Exact S6 identity and preserved evidence
| Field | Exact value |
|---|---|
| Source run | `40731224990` |
| Source execution commit | `a23ba71f48487f3ebead99bc30039b14ef9b7609` |
| Source SHA | `da1a9ea9b5cd789c944de3f07b08395bb67c49e7` |
| Cohort | `s6-v23-da1a9ea9` |
| MASTER_SEED | `20270101` |
| Scenarios | 20 stochastic scenarios |
| Trial IDs | 1..2400 per scenario |
| Total Trial rows | 48,000 |

GitHub Actions metadata listed 20 unexpired scenario Artifacts for Run 40731224990 at the time of review. The parent workflow conclusion remains `failure`; the 20 scenario jobs individually succeeded. This distinction is preserved.

## 3. Producer-path proof
The following source files were fetched from GitHub at exact source execution commit `a23ba71f48487f3ebead99bc30039b14ef9b7609`:

1. [`monte_carlo.py`](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/a23ba71f48487f3ebead99bc30039b14ef9b7609/monte_carlo.py#L78-L112) — `_daily_snapshot` explicitly returns a limited dictionary: date, Trial ID, Cash, partner reinvestment balances, Capital, Retained Earnings, Net Equity, bike/claim counts and close date. It does **not** include any of the five full-balance fields.
2. [`monte_carlo.py`](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/a23ba71f48487f3ebead99bc30039b14ef9b7609/monte_carlo.py#L195-L232) — `run_single_trial` defines `capture_day`, appends only `_daily_snapshot(...)`, and passes that callback as `on_day_end`.
3. [`daily_engine.py`](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/a23ba71f48487f3ebead99bc30039b14ef9b7609/daily_engine.py#L1038-L1040) — the engine calculates `assert_balance_sheet_balanced` and appends the full snapshot to in-memory `project.daily_balance_checks`. [The daily callback is invoked separately](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/a23ba71f48487f3ebead99bc30039b14ef9b7609/daily_engine.py#L1129-L1146).
4. [`accounting.py`](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/a23ba71f48487f3ebead99bc30039b14ef9b7609/accounting.py#L124-L157) — `balance_sheet_snapshot` computes `Accounts_Receivable`, `Guarantee_Claim_Receivable`, `Gross_Bike_Assets`, `Accumulated_Depreciation`, and `Total_Assets`. This proves calculation logic exists; it does not prove those values were serialized into S6 artifacts.
5. [`scripts/s6_first_checkpoint.py`](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/a23ba71f48487f3ebead99bc30039b14ef9b7609/scripts/s6_first_checkpoint.py#L128-L131) — `snapshot_record` copies the reduced row and adds scenario/source/cohort/schema metadata only.
6. [`scripts/s6_first_checkpoint.py`](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/a23ba71f48487f3ebead99bc30039b14ef9b7609/scripts/s6_first_checkpoint.py#L453-L470) — the writer constructs `daily_rows` from those captured slices and writes them to `daily_snapshots.parquet`. The scenario output set contains trial summary, reduced daily snapshots, daily distribution, provenance and manifest; no separate full daily-balance ledger is emitted by this writer.
7. [`s6-n600-checkpoint.yml`](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/a23ba71f48487f3ebead99bc30039b14ef9b7609/.github/workflows/s6-n600-checkpoint.yml#L168-L181) — the scenario directory is uploaded as the per-scenario Artifact.

**Root cause:** the engine computes a full balance snapshot in memory, but the persisted S6 daily artifact is built from a separate reduced callback projection. The five fields are dropped at serialization, before Parquet persistence.

## 4. Independent corroboration
- [Run 40787081064](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40787081064), tested SHA `ef6f25bc2b5dd718f9623f75fc4dffbc0f52ace3`: 98,323,918 persisted daily rows checked for `Net_Equity == Capital + Retained_Earnings`; zero mismatches. The audit explicitly reports all five fields missing, `full_balance_sheet_status=MISSING_EVIDENCE`, and `acceptance=NOT_GRANTED`.
- [Run 40761382163](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40761382163), tested SHA `cb139583b04f43e19c3e6b9df2faa4a6e01bb5e7`: 48,000 Trial rows and 2,086,550 daily distribution rows; Trial fingerprints and aggregate digest matched, but independent daily-balance recheck remained missing.
- [Run 40784902124](https://github.com/yasmin977209-ux/motorcycle-simulation/motorcycle-simulation/actions/runs/40784902124), tested SHA `e7527b42ed30a26a857c5b25064f5419d0dc6c14`: daily accounting audit failed closed; 48,000 fingerprints matched, but `rows_recomputed=0`.
- [Run 41098699740](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41098699740): 105 representative keys only (100 S6 + 5 C100); not the original 48K per-Trial daily ledgers.
- Stage 12/13 and C100 are separate lineages and are not substitutes.

## 5. Disposition
| Item | Disposition |
|---|---|
| `Accounts_Receivable` | `MISSING_EVIDENCE` |
| `Accumulated_Depreciation` | `MISSING_EVIDENCE` |
| `Gross_Bike_Assets` | `MISSING_EVIDENCE` |
| `Guarantee_Claim_Receivable` | `MISSING_EVIDENCE` |
| `Total_Assets` | `MISSING_EVIDENCE` |
| Financial Gate A | `PASS_SCOPED` only |
| Production Gate A | `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS` |
| E2 | `PASS_SCOPED` — read-only audit plus serialization diagnosis |
| Project | `T2_INTERIM / NOT_FINAL_BLOCKED` |

The original-artifact search path is closed **for the inspected S6 producer and persisted daily-snapshot contract**. The historical accounting gap itself is **not closed**. The five fields are not zero and have not been inferred.

## 6. Exact next decision — no implied authorization
A deterministic replay is the only identified computational route to produce full per-day balance evidence for the exact existing S6 trial scope. It would be a new execution, not original preserved evidence. It must use the exact scope and identities in §2 and original execution code revision above; compare all 48,000 Trial fingerprints and all overlapping stored daily fields/dates to immutable original artifacts; require complete daily Trial coverage and `Assets == Equity` for every row; and fail closed on any mismatch. New replay output must be labelled `REPLAY_RECONSTRUCTED_NOT_ORIGINAL_PRESERVED`. No original Artifact or manifest may be overwritten.

**Owner decision required:** explicitly authorize this exact deterministic replay reconstruction, or choose to preserve the gap. This addendum is not authorization to run it.

## 7. Session execution declaration
- No workflow was dispatched.
- No Trial, Simulation, Monte Carlo, replay, N expansion, backfill or zero-fill occurred.
- No source/cohort/seed/Trial identity was changed.
- No historical Artifact or manifest was modified.
- No main write, merge, force-push or Release occurred.
- E3 remains not started.
