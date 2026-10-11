# R4 — Stage 9C canonical 20-point Parquet vs _STATS audit

Date: 2026-10-11
Scope: read-only verification of the historical full Stage 9A 9,005-trial dataset and its published workbook. No simulation/trial execution and no edits to historical results, metadata, fingerprints, engine, RNG, or state.json.

## Three-source review before creating the audit workflow

| Item | Current main | stage3b-preserved | Binding reference / approved decisions / actual source | Judgment |
|---|---|---|---|---|
| Stage 9C status | main at 94b6ea49715c9f845be83b6f106b26c253bf0506 records Stage 9C as PARTIAL and its 20-point Parquet/_STATS comparison as NOT EXECUTED in docs/stage9c/STAGE9C_REPORT.md (blob 81fb79720988cfe261fa6d8d29371e616f9f9850). | HEAD 2e3aa381d833fe430d2aec42e98dd0d29918c3bf is diagnostic only and is not authoritative for current Stage 9C execution. | The current user explicitly directs execution of Stage 9C's independent 20-point gate using its actual scope. | DEVIATION — run-backed full-scope evidence is missing from main. |
| Gate metric/statistic semantics | No complete canonical 9,005-result audit workflow exists on main. | No code is copied from this branch. | docs/stage13/20point_gate_definition.json at 648b5315da1ef46146226d7982020a88c4905dcb (blob 972acc6033f956a48e9b0feb02741a63b952cff3) defines the comparison semantics: four metrics (Final_Net_Project_Equity, Partner1_Final_Entitlement, Partner2_Final_Entitlement, Final_Cash) × MIN/P10/P50/P90/MAX; linear NumPy quantiles; exact numeric equality. Its own cohort is IDs 26–50 / 625 rows, not the canonical Stage 9C scope. | MATCH for metric/statistic semantics; DEVIATION for scope. The current task explicitly requires the canonical Stage 9C scope, so this workflow applies the same comparison mechanics to 9,005 historical trial results and does not claim the 625-trial sample as full scope. |
| Historical data and workbook | docs/stage9c/STAGE9C_REPORT.md identifies Stage 7 source SHA f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b, Run 37225915321, Stage 9A workbook SHA 0fb325fc9e196a534ba8ab7484dcfd0541cefd3a2ca37c3b6f930e3215f62f6d, manifest 892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6, and states the full Stage 9C 20-point gate was not executed. | No substitute source identity is inferred from the preserved branch. | Existing enrichment packages come from Runs 37655041728 / 37662891608, are identified as Stage 7 run 37225915321, and are read-only inputs. Published final workbook artifact is Run 37671448546 / artifact 11507380986. | MATCH if all live package metadata, 9,005 unique result rows, workbook hash, 185 sheets, zero errors/formulas, and 500 exact cells independently verify. |
| Workflow/trigger | Available main workflows do not provide this independent full-scope validator; the existing Stage 13 20-point runner is tied to its diagnostic 625-trial cohort. | Diagnostic workflows are not copied. | Project controls require exact branch pinning, job-level timeout, no workflow_dispatch in the approved path, no self-dispatch, and no historical trial replay. The existing wildcard stage4-verify-* does not match this branch name. | DEVIATION — a dedicated pinned, read-only validation workflow is required; no simulation command is included. |

## Controlled execution plan

1. A single workflow is pinned to tmp/stage9c-20point-full-20261011 with push-only trigger, read-only contents/actions permissions, and a 30-minute job timeout.
2. It downloads only already-published artifacts and independently reads the canonical workbook and trial_results.parquet files. It executes no engine, trial, pytest, or workflow_dispatch.
3. For each scenario it checks scenario/source/run/seed identity, required trial IDs, row count, duplicate keys, required metric fields and available fingerprint provenance.
4. It recalculates MIN, P10, P50, P90 and MAX for all four named metrics, then compares the corresponding <scenario>_STATS cells with exact numeric equality and no tolerance.
5. PASS requires all 25 scenarios, 9,005 unique (scenario_id, trial_id) pairs, 185 sheets, no Excel error or formula cells, the exact published workbook hash, and all 500 comparisons passing.
6. This validation does not imply Gate A or Gate B, does not make changes to the old Stage 9C partial decision records, and does not edit canonical dataset identity. Current instruction authorizes running this independent gate despite the older report's NOT EXECUTED status.



## Execution correction record — 2026-10-11

Run 38160869693 initially stopped with HTTP 401 from a malformed GH_TOKEN expression. After correcting the token, Run 38160958608 successfully opened the published workbook and verified its exact SHA-256, 185 sheets, all 25 _STATS sheets, zero Excel error cells, and zero formula cells. It did not reach the comparisons because the validator incorrectly required dataset_identity.json. Inspection of the published Stage 9A artifact showed its actual identity schema is scenario_metadata.json plus trial_fingerprints.json; dataset_identity.json is not included. This is an audit-harness schema assumption, not evidence of a data defect. The validator now uses the published metadata/fingerprint files, checks their source/run/scenario/count/parameter identity, and documents the master seed from the producing Stage 7 workflow and source constant.

## Verified Stage 9C 20-point gate result — Run 38161359034

**Run:** https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/38161359034  
**Audit branch head tested:** `aebc1bae6b14e00b6f5f4855a1ba7d8c00f25a2d`  
**Evidence artifact:** `stage9c-canonical-20point-gate-evidence`, artifact ID `11709953624`, SHA-256 `67214a348093240908fbfa211befc66710129c96070cf064e181caf32bfca9fa`.

| Gate | Result | Evidence |
|---|---|---|
| Published workbook SHA-256 | PASS | Actual `0fb325fc9e196a534ba8ab7484dcfd0541cefd3a2ca37c3b6f930e3215f62f6d` equals the published expected SHA |
| 185 worksheets / 25 `_STATS` sheets | PASS | Independently reopened workbook |
| Excel error cells / formula cells | PASS | 0 / 0 |
| 25 scenario packages and identity checks | PASS | 25/25 scenario packages |
| Result rows and key uniqueness | PASS | 9,005 rows; 9,005 unique `(scenario_id, trial_id)` pairs |
| Point coverage | PASS | 500/500 numeric comparisons produced |
| Exact equality of all points | **FAIL** | 499/500 match; one exact mismatch below |

### Exact mismatch (verbatim numeric values)

- Scenario: `C030_G030`
- Worksheet metric: `Final_Cash`
- Statistic: `P90`
- Parquet recalculation using `numpy.quantile(values, 0.90, method="linear")`: `13185720.000000002`
- Stored `C030_G030_STATS` value: `13185720`
- Difference: `0.000000002` (shown for diagnosis only; **no tolerance is applied**).
- Classification: **K_CODE** — the published XLSX cell does not preserve the exact statistic required by the approved gate. The workflow does not round the comparison or suppress this point.
- Impact: Stage 9C remains **FAIL**, not PASS. No historical trial or dataset was changed.

The historical builder source at commit `5e25a94743f44554093934c57404c0b168e69651` uses `numpy.quantile(..., method="linear")` for statistics, and the Stage 9A Run `37671448546` used NumPy `2.4.6`, the same installed version shown in the audit workflow. The precise write/serialization point that reduces this one statistic to the stored XLSX number still requires isolation. The gate definition remains unchanged. Do not add epsilon/tolerance, round the recomputation, or alter historical Parquet to obtain PASS.

**Next allowed step:** isolate the exported numeric-cell serialization discrepancy under R4 and regenerate a separate workbook from unchanged source data only if the correction can preserve the exact gate definition and all existing workbook constraints; rerun the complete independent 500-point gate. Gate A/Gate B remain separate.

