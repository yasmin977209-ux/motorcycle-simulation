# R4 — Stage 9C exact XLSX statistic serialization fix

Date: 2026-10-11  
Scope: preserve exact floating-point results in the four approved `_STATS` metrics and the five mandated statistics without changing the quantile calculation, tolerances, historic Parquet, trial identities, or workbook layout.

## Three-source review before production-code change

| Item | Current main | stage3b-preserved | Binding reference / approved decision / source | Judgment |
|---|---|---|---|---|
| Excel statistics calculation | `scripts/excel_builder.py` blob `eace6fb37aadae9f703bca206581e4249a823c09`; `metric_stats` calls `numpy.quantile(vals, q, method="linear")`, casts quantiles to Python floats, and `write_table` passes those floats to openpyxl. | HEAD `2e3aa381d833fe430d2aec42e98dd0d29918c3bf` has no `scripts/excel_builder.py`; no implementation is copied from the diagnostic branch. | Published Stage 9A build Run `37671448546` used NumPy 2.4.6 and openpyxl 3.1.5. The authoritative `STAGE9C_20_POINT_PARQUET_VS_STATS_V2` definition uses the same NumPy linear quantile and requires exact numeric equality with no tolerance. | MATCH on quantile formula; DEVIATION on exact exported numeric value. |
| Reproduced point-level discrepancy | Run `38161359034` confirms 499/500 matches. The one mismatch is `C030_G030 / Final_Cash / P90`: recomputation `13185720.000000002`, stored XLSX value `13185720`. | No relevant source; do not infer behavior. | Exact value required by the gate; no rounding or tolerance is allowed. | **K_CODE:** exported numeric cell loses low-order digits required by the gate. |
| Narrow write path | `py_value` preserves Python float; `write_table` hands it to openpyxl; `wb.save` serializes XLSX. openpyxl 3.1.5's `safe_string` applies `"%.16g" % value`; evaluating it with `13185720.000000002` yields `13185720`. | No implementation available. | The numeric cell must preserve the exact result while remaining numeric and independently readable. | The defect is in XLSX serialization, not the trial metric, input data, or statistical definition. |
| Allowed correction | No changes on main before this R4. | No changes/copy. | Preserve only gate-relevant numeric cells in the OOXML package using the round-trip representation `repr(float_value)` when openpyxl's serialized representation would change the value. The gate formula and strict comparator remain unchanged. | Proposed **K_CODE** fix, bounded to the four named metric rows and MIN/MAX/P10/P50/P90 cells on each `_STATS` sheet. |
| Data and workbook safeguards | Main keeps source data and workbook generation separate from simulation. | Diagnostic only. | Historical Parquet, per-trial outputs, metadata, dataset/global fingerprints, and source identity are immutable. Workbook must remain 185 sheets, with zero formulas and zero Excel error cells. | No engine, RNG, trial, or dataset change permitted. |

## Implementation / acceptance plan

1. Add a post-save OOXML serializer correction to `scripts/excel_builder.py`. It patches only the relevant cells in `*_STATS` sheets and only when openpyxl's `%.16g` serialization would change the underlying Python float. The patched OOXML numeric lexical value is `repr(value)`, which round-trips to the same binary float; no epsilon/tolerance, quantile change, or rounding is introduced.
2. Run a synthetic regression probe using the reproducing value `13185720.000000002`: write a workbook, apply the correction, reopen with openpyxl, assert exact Python numeric equality and numeric cell type.
3. Run the existing acceptance/regression/path test inventory on an isolated exact-trigger branch. Test 158 remains excluded per the approved inventory; tests are not changed.
4. Rebuild a separate workbook from the already-published Stage 9A data artifacts, without running simulations. Re-run the complete 500-point Stage 9C gate, plus sheet/error/formula and identity checks. The original published workbook and Parquet artifacts remain immutable.
5. No merge to main unless each required gate and the exact 500-point comparison passes. If openpyxl/Excel readers fail to preserve the target numeric value, reject the proposed fix and retain the Stage 9C FAIL result.

## Status before implementation

- Base main SHA: `94b6ea49715c9f845be83b6f106b26c253bf0506`
- `stage3b-preserved` SHA: `2e3aa381d833fe430d2aec42e98dd0d29918c3bf`
- Gate definition: `docs/stage13/20point_gate_definition.json` at audited blob `972acc6033f956a48e9b0feb02741a63b952cff3`.
- Gate run: `38161359034`; Stage 9C remains FAIL until the full correction workflow supplies new exact evidence.
- D-2026-10-10-01 is normative for Gate A/B; this export fix is independent and does not satisfy Gate A/B.
