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
