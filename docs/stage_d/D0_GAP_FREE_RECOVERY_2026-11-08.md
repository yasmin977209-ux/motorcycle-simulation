# D0 Gap-Free Recovery Review — 2026-11-08

## الحكم الحالي

**Status:** `BLOCKED / MISSING_EVIDENCE`

**D0 is not PASS_GAP_FREE.** The historical disposition `PASS_SCOPED_WITH_LIMITATIONS` is retained; this review does not rewrite it. The new exact-SHA audit deliberately fails closed when required original evidence is absent.

- Repository: `yasmin977209-ux/motorcycle-simulation`
- Working branch: `tmp/d1-rebuild-20261101`
- Code/tested HEAD: `beb1b83656bfdd15206427a7e4ce1575d654e588`
- Protected `main` (read-only): `01a6f79eedc522bb734ed9c5ea31beee581f2468`
- Prior accepted C2 checkpoint: `41b481d88ddc0013c4103aaa08fc1c495aa0b2ae`
- Governing reference: v2.4.0, decision `D-2026-10-30-REFERENCE-V2.4.0`, `APPROVED_BY_OWNER`; reference SHA-256 remains `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`.
- Active prompt library: [REV7](PROJECT_PROMPT_LIBRARY_AR_2026-11-07_REV7.md), Git blob `57c08771cdff93faeb0e808490d3660e7051edda`.

## Changes made — technical fail-closed repair only

Commits on the working branch:

1. `03d0aa8c8b6c798b466f907d5f649e9307d61197` — first implementation of D0 fail-closed checks.
2. `beb1b83656bfdd15206427a7e4ce1575d654e588` — corrected the workflow heredoc and required every expected metadata hash to match.

Files changed:
- `scripts/audit_preservation_artifact.py` — Git blob `35b5cc21336c89952ac1214bb50d43e1c38e3d28`.
- `.github/workflows/d0-preservation-integrity-audit.yml` — Git blob `8702569ff81d07b4ff845299cc8f667cf47799b4`.
- `tests/test_audit_preservation_artifact.py` — Git blob `a1f80e3bb8c063bb019537ed75380e24511a40dd`.

The repair:
- enforces `--require-source-metadata` instead of silently accepting missing metadata;
- requires every expected metadata SHA-256 to match an actual source metadata file;
- checks the five normative accounting fields in each required `daily_snapshots.parquet`;
- marks missing required Parquet fields as `MISSING_EVIDENCE`;
- fails the aggregate workflow when any required artifact is blocked.

Six fail-closed unit tests passed in D0 prepare job `128560533348` on `beb1b83656bfdd15206427a7e4ce1575d654e588`.

The first D0 run on `03d0aa8...` (Run [42424715515](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42424715515)) exposed a shell heredoc terminator defect after the six tests passed (`PY: command not found`). This was corrected in `beb1b836...`; the first run remains in history and is not used as the final D0 result.

## Exact D0 audit result

Run [42424755294](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42424755294), tested SHA `beb1b83656bfdd15206427a7e4ce1575d654e588`:

| Measure | Result |
|---|---:|
| Expected artifact reports | 27 |
| Reports received | 27 |
| `PASS_SCOPED` artifact audits | 7 |
| `BLOCKED` artifact audits | 20 |
| Missing reports | 0 |
| Aggregate classification | `BLOCKED` |

- Aggregate job: `128560779663`, conclusion `failure`.
- Aggregate Artifact: `13595092311`, 2,380 bytes; GitHub API digest `sha256:34752606bf00e052b043cf085ab83966260d5c592800b30cfb9089179e27e9ef`.
- The 20 blocked jobs correspond to the 20 original S6 scenario Artifacts from source Run `40731224990`.
- The seven `PASS_SCOPED` audits are additional preservation inputs; their limited result does not establish D0 gap-free.
- For the S6 source archives, the audit jobs produced reports only after the downloaded ZIP bytes matched the expected size/SHA-256 and outer ZIP CRC/restore passed. Their classification remained `BLOCKED` because the required original metadata/Parquet evidence was missing. Representative job logs show `metadata_sha256=MISSING_EVIDENCE` and `parquet_status=MISSING_EVIDENCE`.

## D0 requirement traceability / blockers

| Requirement | Evidence observed | Status | Why it prevents gap-free |
|---|---|---|---|
| Original S6 identity | Run `40731224990`; execution commit `a23ba71f48487f3ebead99bc30039b14ef9b7609`; source SHA `da1a9ea9b5cd789c944de3f07b08395bb67c49e7`; cohort `s6-v23-da1a9ea9`; seed `20270101`; 20 scenarios; Trial IDs 1..2400 per scenario | VERIFIED_LIVE for run metadata; source records remain scoped | Identity is pinned, but identity alone does not provide absent ledger contents |
| Exact GitHub source ZIP bytes | 20/20 source jobs produced audit reports; raw SHA-256 pin, ZIP CRC and restore passed | PASS_SCOPED | Container integrity does not prove the required records/columns exist |
| `source_run_metadata.sha256` | Aggregate manifest records null; source metadata hash audit returns `MISSING_EVIDENCE` | MISSING_EVIDENCE | Required source metadata cannot be verified or reconstructed |
| Full Parquet schema/coverage | New D0 audit checks required Parquet members and required accounting fields; 20 S6 artifact audits blocked | MISSING_EVIDENCE | Complete expected schema/row/partition coverage is not established |
| Original daily ledgers for all 48,000 Trials | Existing source audits report the stored daily projection is reduced and original full daily/accounting ledgers are absent | MISSING_EVIDENCE | A replay or representative sample cannot substitute for original historical ledgers |
| Five full-balance fields | `Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Total_Assets` are absent from the persisted S6 daily projection | MISSING_EVIDENCE | Full balance-sheet reconciliation cannot be proven |
| Independent permanent copies and restore | OneDrive inventory showed size/metadata matches only; raw-byte readback previously returned `403 Database Is Read Only`; independent second durable failure domain and restore remain unproven | BLOCKED | Metadata equality is not raw-byte identity or a successful restore |

### Independent historical corroboration

The live `docs/post_d/E2_ACCOUNTING_EVIDENCE_AUDIT.md` records:
- 48,000 S6 Trial rows/fingerprints checked;
- 98,323,918 daily rows checked for the limited `Net_Equity == Capital + Retained_Earnings` identity, with zero mismatches;
- `full_balance_sheet_status=MISSING_EVIDENCE` and the five fields listed above;
- Golden accounting audit `40784902124` had `rows_recomputed=0` and `daily_balance_reconciliation=MISSING_EVIDENCE_FOR_INDEPENDENT_RECHECK`;
- Full Logging covers 105 representative keys only, not all 48K Trial/day records.

The repository tree has no original S6 48K daily-ledger Parquet/SQLite/CSV payload committed as source files. The available `docs/evidence/s6_n300_source_run_metadata.json` is an N=300 source and is not interchangeable with the S6 N=2400 identity. Stage 12/13 accounting data and C100 remain separate identities and are not substituted.

## Exact-head downstream checks

On the same `beb1b83656bfdd15206427a7e4ce1575d654e588`:
- D1-D2 Run [42424755307](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42424755307): `success`.
- D3 Run [42424755281](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42424755281): `success`.
- D6 Run [42424755247](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42424755247): `pending` at handoff. No waiting/retry is claimed.

D1-D2/D3 success does not bypass D0's entry gate. The D0 result is `BLOCKED`; therefore D1/D2 cannot be treated as authorized progression for gap-free stage closure.

## What is needed to unblock D0

1. The **original, immutable S6 daily accounting ledger source** for all 48,000 Trial identities and required daily records, from the original producing run/source lineage—not a replay, rebuilt approximation, representative logging package, or Stage 12/13 dataset.
2. The original `source_run_metadata` file and its independently verifiable SHA-256, bound to the same source SHA/cohort/seed/run.
3. Original Parquet/SQLite partitions or equivalent source artifacts that expose the five required balance fields and permit full schema, row-count, null, duplicate, partition, identity and lineage reconciliation.
4. A supported raw-byte readback and restore route for the preserved originals, plus the required independent durable retention evidence.

If those original records were never produced or preserved, D0 cannot become `PASS_GAP_FREE` under the current REV7/v2.4.0 requirements. Any change to the governing acceptance requirement is an owner-only decision; no such change is assumed here.

## Safety / actions not taken

No Trial, Simulation, Monte Carlo, N expansion, N=4800, backfill, zero-fill, inferred accounting value, source/cohort/seed/Trial identity change, historical Artifact mutation, `main` write, merge, force-push, Release or final-acceptance declaration was performed.

**Final D0 verdict for this recovery attempt: `BLOCKED / MISSING_EVIDENCE`.**
