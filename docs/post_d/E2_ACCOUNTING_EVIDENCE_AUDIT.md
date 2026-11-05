# E2 — Accounting Evidence Audit and Production Gate A

- Date: 2026-11-05
- Repository: `yasmin977209-ux/motorcycle-simulation`
- Branch: `tmp/d1-rebuild-20261101`
- Baseline HEAD: `561d5b0cb1b87f83c365c2bf3b1dee5ef120be07`
- main HEAD at start: `01a6f79eedc522bb734ed9c5ea31beee581f2468`
- Status: `PASS_SCOPED` — read-only historical evidence audit; Production Gate A remains `NOT_DECLARED`.
- Project: `T2_INTERIM / NOT_FINAL_BLOCKED`
- Next stage: E3 is not started by this E2 execution.

## 1. Authority and limits

Executed from the live E2 prompt in `docs/stage_d/PROJECT_PROMPT_LIBRARY_AR_2026-11-01.md` §11. E0 and E1 outputs were read from the active branch; E1 owner-decision register explicitly permits searching/reusing original preserved evidence, but prohibits inferred/backfilled accounting and any new Trials/Simulation/Monte Carlo/N expansion without separate approval.

The governing reference v2.4.0 was fetched from GitHub Raw at baseline HEAD. Its SHA-256 is `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`, size 401,397 bytes, Git blob `9fe43bfbb2cbfd2bb7f7010866e7469506d22c33`. Owner decision `D-2026-10-30-REFERENCE-V2.4.0` is `APPROVED_BY_OWNER`. Historical execution reference v2.3 remains `e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f`; it is not substituted for v2.4.0.

Reference §0.12 requires `Assets == Equity` at the end of every day, for every Trial and every scenario, after all daily postings. §10.4 defines:
```text
Net_Bike_Assets = Gross_Bike_Assets - Accumulated_Depreciation
Total_Assets = Cash + Accounts_Receivable + Guarantee_Claim_Receivable + Net_Bike_Assets
Total_Equity = Capital + Retained_Earnings
Liabilities = 0
Total_Assets == Total_Equity
```
No alternative calculation or proxy was adopted.

No code, reference, business rule, threshold, source/cohort/seed/Trial identity, Artifact, or historical manifest was changed. No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, main write, merge, force-push, Release, or final-acceptance declaration occurred. No new workflow was run in this E2 session; prior runs below are cited only at their exact historical tested SHAs.

## 2. S6 historical cohort and 48,000-Trial scope

The source evidence identifies the S6 v2.3 stochastic cohort as:

| Identity | Value |
|---|---|
| Source run | `40731224990` |
| Source-run HEAD | `a23ba71f48487f3ebead99bc30039b14ef9b7609` |
| Source SHA | `da1a9ea9b5cd789c944de3f07b08395bb67c49e7` |
| Cohort | `s6-v23-da1a9ea9` |
| MASTER_SEED | `20270101` |
| Stochastic scenarios | 20 |
| Trial IDs per scenario | 1..2400 |
| Total | 48,000 Trial rows |

GitHub Actions Run [40731224990](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40731224990) has parent conclusion `failure`; its 20 scenario jobs individually concluded `success`, and GitHub lists 20 unexpired scenario Artifacts. Do not relabel the parent run as success. The 20 immutable scenario Artifacts are retained under their exact Artifact IDs in the JSON register; metadata showed expiry on 2026-11-27. Their ZIP bytes were not downloaded/read by this E2 session.

The read-only independent source-vs-aggregate audit [Run 40761382163](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40761382163), tested at `cb139583b04f43e19c3e6b9df2faa4a6e01bb5e7`, downloaded all 20 source Artifacts and reported:
- `trial_rows=48000`
- `daily_distribution_rows=2086550`
- financial Trial fingerprints recomputed; row-by-row canonical digest match `true`
- `daily_balance_independent_recheck=MISSING_EVIDENCE_FOR_INDEPENDENT_RECHECK`
- source-run metadata gap `MISSING_EVIDENCE_SOURCE_RUN_METADATA_FILE_NOT_PINNED`
- overall `PASS_SCOPED`, not production accounting acceptance.

The aggregate replay [Run 40773412377](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40773412377), tested at `4f2f2cc16d0cb5125262088704febccbae6f50ed`, is an evidence-only aggregation of immutable artifacts (not a simulation). Artifact 12852969854 is recorded as 9,357,996 bytes, SHA-256 `ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54`. The D2 audit records its daily-distribution member as 4,881,090 bytes and SHA-256 `9619fc94e371da073a622f8f0fcd28786caf79fac47697cca2bfadbb469e4903`. This aggregate contains trial summaries and daily quantile distribution, not the full per-Trial daily balance ledger needed to independently prove the five missing balance-sheet fields.

## 3. Direct finding: the five fields are absent from the 48K daily projection

The historical read-only audit workflow `.github/workflows/s6-n2400-daily-equity-identity-audit.yml` downloads all 20 source scenario Artifacts from Run 40731224990 and runs `scripts/audit_s6_n2400_daily_equity_identity.py`.

The corresponding successful audit [Run 40787081064](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40787081064), tested at `ef6f25bc2b5dd718f9623f75fc4dffbc0f52ace3`, has Job `123162847082`. Its GitHub job log reports:
- 98,323,918 daily rows seen and checked for the limited equity identity;
- 98,323,918 rows checked;
- zero `Net_Equity == Capital + Retained_Earnings` mismatches;
- `full_balance_sheet_status=MISSING_EVIDENCE`;
- exact missing fields:
  `Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Total_Assets`;
- `acceptance=NOT_GRANTED`.

The audit source explicitly describes the persisted `daily_snapshots.parquet` as a reduced projection. It checks only the partial equity identity and reports the five full-balance fields missing. This is strong evidence of absence in that stored daily projection, not evidence that those values are zero or recoverable by algebra.

A separate exact Golden/daily-accounting audit [Run 40784902124](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40784902124), tested at `e7527b42ed30a26a857c5b25064f5419d0dc6c14`, failed. Its log reports 48,000 exact financial fingerprints matched, but `rows_recomputed=0`, `daily_balance_reconciliation=MISSING_EVIDENCE_FOR_INDEPENDENT_RECHECK`, and the workflow failed its required independent daily-balance assertion. This failure is retained; fingerprint parity is not promoted to accounting proof.

## 4. Financial Gate A versus Production Gate A

The independent Golden/projection review [Run 40795998745](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40795998745), tested at `a5573eb1891ed2c56b01f6c9b3ccfe9619a08358`, reports a read-only financial fingerprint scope:
- 48,000 exact financial fingerprint matches;
- 90,000 fingerprint comparisons across 80/80 scenario/checkpoint pairs;
- zero mismatches;
- `simulation_trials_run=false`;
- `gate_a_production_checkpoint_status=NOT_DECLARED_BY_THIS_APPROVAL`;
- `full_balance_sheet_status=MISSING_EVIDENCE`.

Therefore:
- Financial Gate A remains `PASS_SCOPED` only.
- Production Gate A remains `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`.
- The independent fingerprint/Golden comparison does not prove a daily Assets==Equity balance for every Trial/day/scenario.

## 5. Full Logging — representative scope only

Run [41098699740](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41098699740), tested at `e3c2098df9fc5dbc126eb1e77ad35c493ff3ac70`, completed the representative logging job. Its job log reports:
- 125 role assignments;
- 20 duplicate role assignments;
- 105 unique representative keys completed;
- zero representative key failures;
- S6 representative keys: 100;
- C100 representative keys: 5;
- `historical_48000_trial_daily_artifacts=MISSING_EVIDENCE_NOT_AUDITED_OR_MODIFIED`.

The S6 representative cohort `s6-v23-da1a9ea9` and C100 cohort `c100-v23-s4-20261026-965281d5` remain separate. The 105 logs are not the original 48,000-Trial daily artifacts. The representative workflow re-created detailed logs for selected representatives; it did not inspect/repair the historical 48K daily projection. Its Artifact 12998778418 metadata is 310,827,203 bytes, SHA-256 `403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb`, currently listed unexpired. ZIP bytes were not re-read in this E2 session.

The D2 live audit still records `full_logging_normalized_status=NOT_VERIFIED_105_OF_105`. `scripts/s6_manifest_resolver.py` leaves normalized status `NOT_VERIFIED` when independent expected byte sizes are missing, with reason `INDEPENDENT_EXPECTED_BYTE_SIZES_MISSING`. The representative logging success does not close that provenance gap or establish 48K coverage.

## 6. Daily accounting / budget test disposition

| Required check | E2 finding |
|---|---|
| `Net_Equity == Capital + Retained_Earnings` for 48K daily rows | `PASS_SCOPED`: 98,323,918 rows; 0 mismatches in Run 40787081064 |
| Full `Assets == Equity` per day / Trial / scenario | `MISSING_EVIDENCE`: five balance-sheet fields absent from persisted daily projection |
| Accounts Receivable roll-forward for all 48K | `MISSING_EVIDENCE` |
| Gross Bike Assets / Accumulated Depreciation roll-forward for all 48K | `MISSING_EVIDENCE` |
| Guarantee Claim Receivable and Total Assets daily reconciliation | `MISSING_EVIDENCE` |
| Complete event/contract/claim/asset accounting source rows for all 48K | `MISSING_EVIDENCE`; representative logs only |
| Daily operating budget / all daily posting components across every 48K Trial | `MISSING_EVIDENCE`; no complete original per-Trial daily ledger was verified |
| Representative daily accounting logs | `PASS_SCOPED` for 105 representative keys only; artifact bytes not independently re-read in this session |

No daily value was derived from another field. The five missing values were not inferred, zero-filled, or backfilled.

## 7. Stage 12/13 separation

`docs/stage12/accounting_data_contract.json` describes a different dataset identity: `source_sha=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, `MASTER_SEED=20270101`, 11,005 trials and 22,546,465 daily rows. It is not the S6 48,000-Trial cohort (`source_sha=da1a9ea9...`, `cohort_id=s6-v23-da1a9ea9`). Its balances or rows are not imported, substituted, or used to infer missing S6 history. C100 remains a separate cohort as well.

## 8. Evidence classifications and limitations

- `VERIFIED_LIVE`: current branch refs; v2.4.0 Raw bytes and digest; E0/E1 source documents and source-code files listed in the machine-readable report; GitHub Actions run/job metadata and job logs read directly.
- `PASS_SCOPED`: historical S6 daily Net Equity identity check; financial fingerprint comparisons; representative Full Logging only.
- `MISSING_EVIDENCE`: full daily balance sheet across 48K; all five named fields; complete 48K accounting roll-forwards/events; all-Trial daily operating budget; independent expected byte sizes for 105 normalized manifest keys.
- `NOT_RUN`: new E2 workflow or new trial execution in this session; no new full-balance reconstruction was attempted.
- `NOT_DECLARED`: Production Gate A.

The historical Actions runs were tested at their own recorded SHAs, not the E2 baseline HEAD. Their results are not represented as tests of the current working branch.

## 9. Conclusion and next action

E2 completed its read-only evidence audit within the available preserved evidence: `PASS_SCOPED`. It did **not** close Production Gate A. The original 48K daily projection is reduced and omits the five required balance-sheet fields; representative Full Logging does not fill the gap.

The only safe next action is to continue locating original, preserved, identity-matching S6 accounting source records or unexpired immutable artifacts that actually contain the five fields and all required daily posting rows. If none exist, keep the five fields `MISSING_EVIDENCE` and present the owner-decision memo. No backfill or inference is performed. E3 has not started.
