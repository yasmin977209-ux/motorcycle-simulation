# D2 — Exact Financial Calculations and Number Registry Audit

**Status:** `REPORTED_ONLY_LOCAL / T2_INTERIM / NOT_FINAL_BLOCKED`  
**Registry:** local `results/number_registry.json`  
**Size:** 22,781,475 bytes  
**SHA-256:** `53ece080e0eeea1feefbdac3727997deece17670bff4ac8539ea01562a12af73`

## Audit summary
| Measure | Count |
|---|---:|
| Numeric entries | 13,954 |
| Artifact-backed VERIFIED_LOCAL | 13,946 |
| Documentary REPORTED_ONLY | 8 |
| Unavailable evidence records | 10 |
| Missing source digest fields in pinned input | 1 |
| Duplicate number_id | 0 |
| Python float values | 0 |

All 13,954 IDs are unique. The local audit report states that it rechecks integer numerator/denominator, exact-value round trip, display value, source digest and locator, source type, cohort boundaries, and recursive float exclusion. Eight documentary entries have no artifact/run ID by nature, but carry repository document SHA-256, Git blob SHA-1 and line locators. Ten unavailable items also retain explicit source anchors.

## Exact arithmetic
- int for integer counts and financial sums.
- Fraction for means, ratios and linear quantiles.
- Decimal precision 50 for financial display, followed by `quantize(Decimal("0.01"), ROUND_HALF_EVEN)`; denominator 1 is emitted as an integer.
- No float is accepted in financial calculation or serialized registry values.
- Report-generation API `require_registered_number_ids()` rejects any numeric ID not present in the registry.

## Gate states
- Gate A financial fingerprint: 80/80 pairs, 90,000 comparisons, 0 mismatches — `PASS_SCOPED`, documentary REPORTED_ONLY.
- Gate A production: `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`.
- Gate B N=2400: 10 PASS / 10 FAIL — `FAIL_SCOPED`.
- Stability: 0/60 — `NOT_CONVERGED`.
- N=4800: `NOT_EXECUTED`.
- Full Logging: `PASS_SCOPED` for 105 representative keys only.
- C100: 5 unique keys, separate deterministic-reuse cohort; not pooled into S6.

## Unavailable evidence
Ten items remain unavailable: historical 48K daily ledger; Parquet schema/rows for trials_summary and daily_distribution; value-level representative revalidation; five missing historical accounting fields; and null source_run_metadata.sha256. No backfill, zero-fill, inferred value or cohort mixing was used.

## Verification
- Local tests: 27 passed, as reported locally (`REPORTED_ONLY`).
- compileall: reported local success (`REPORTED_ONLY`).
- All three pinned ZIP SHA-256/size/CRC/path checks: reported local success (`REPORTED_ONLY`).
- Exact-head GitHub workflow: NOT_RUN.
- No reports/workbooks have been generated; future report numbers must resolve through the registry.

D2 local implementation and audit claims remain `REPORTED_ONLY`; no repository D2 gate is open. D1 repository source publication/exact-head validation remains blocked; no D3/D4, Excel, Word or ZIP generation is authorized yet.


## D2 live registry build — 2026-11-01

- D2 disposition: PASS_SCOPED_WITH_LIMITATIONS, subject to exact-head validation in Run 41326515357.
- Registry: 2640 entries; 1000 daily series; 2086550 addressable daily points.
- Daily Distribution source rows validated: 2086550; aggregate checkpoint values: 960.
- Historical local count 13,954 remains REPORTED_ONLY and is not the live registry count.
- Preserved: Full Logging 105 representatives only; statuses NOT_VERIFIED; C100 Golden NOT_RUN; Gate A financial PASS_SCOPED; production NOT_DECLARED; Gate B FAIL_SCOPED; Stability NOT_CONVERGED; N=4800 NOT_EXECUTED; five accounting fields MISSING_EVIDENCE.
- No Trial, Simulation, Monte Carlo, N expansion, historical backfill or zero-fill was performed.

## Exact-head correction — 2026-11-01 (append-only)

- The preceding live-build paragraph cites Run 41326515357. That run built and committed the registry and verified Raw bytes, but the overall workflow ended non-success because the runner clean-tree check included temporary untracked ZIP files. It is not the definitive successful exact-head run.
- Final exact-head workflow: [Run 41326662869](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41326662869) — `SUCCESS`.
- Registry-containing and exact-head-validated commit: `96a07b52485733115cf93875440ea99369a94fdb` on `tmp/d1-rebuild-20261101`; `main` remained `c6e54349a5e94f65d5aa9f83141f225d777bb474`.
- Registry: 2,640 explicit entries (960 Aggregate checkpoint values + 1,680 representative Full Logging metric values); 1,000 daily series; 2,086,550 addressable Daily Distribution points.
- S6 and C100 remain separate. Full Logging remains 105 representatives only and normalized statuses remain `NOT_VERIFIED`; C100 Golden revalidation remains `NOT_RUN`.
- The five historical accounting fields remain `MISSING_EVIDENCE`; production Gate A remains `NOT_DECLARED`; Gate B remains `FAIL_SCOPED`; Stability remains `NOT_CONVERGED`; N=4800 remains `NOT_EXECUTED`.
- Evidence triple: https://github.com/yasmin977209-ux/motorcycle-simulation/blob/96a07b52485733115cf93875440ea99369a94fdb/results/number_registry.json ; SHA-256 `b271cb638c89f6ff14e22e1cfbf5f4d7acc803e00a89eef7ff716ed386b89e3e`; Git blob SHA-1 `81e8c7cedcec1e75f86f00a198d93c82f1c4e99b`; 24,136,918 bytes.
- No new Trial, Simulation, Monte Carlo, N expansion, backfill or zero-fill was performed. D3 has not been started.


## Current D2 status correction — 2026-11-01

- Current canonical status: PASS_SCOPED_WITH_LIMITATIONS, proven by the successful exact-head D2 workflow in Run 41328486239.
- The opening REPORTED_ONLY_LOCAL header and 13,954-entry count above are retained as historical local audit context only; they are not the current repository registry.
- Current repository registry: 2,640 entries (960 aggregate checkpoint values + 1,680 numeric values for 105 representative Full Logging keys), 1,000 daily series and 2,086,550 addressable daily points.
- Every daily point now has a deterministic D2D number_id scheme and a callable resolve_number lookup that returns its exact value and source provenance.
- Historical report contents were retained inside docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.json under historical_local_report; no historical result was silently deleted.
