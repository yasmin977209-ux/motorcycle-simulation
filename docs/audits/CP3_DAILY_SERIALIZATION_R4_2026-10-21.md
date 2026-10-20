# CP3 — DAILY serialization regression + branch-pinned verification workflow — R4

**Date:** 2026-10-21  
**Status before code change:** R4 recorded; implementation/test run pending  
**Base:** live `main` HEAD `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`  
**Target:** `tmp/cp-path3-daily-workflow-20261021` (fresh branch from that exact base)  
**Normative original reference SHA-256:** `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479` (locally recomputed and matched)

## R4 — before production/test/workflow modification

| العنصر | الحالة الحالية | المرجع/القرار | الفرع وSHA | النص الحاكم | تصنيف العيب | التغيير الأدنى | الصلاحية | معيار القبول | المخاطر |
|---|---|---|---|---|---|---|---|---|---|
| DAILY dictionary serialization | `scripts/excel_builder.py::write_daily_sheet` forwards dictionaries directly to `write_table`; that function enumerates each row, so dictionary keys can be emitted instead of cell values. Source blob: `50115a2fea5812727e0e5a8bfbb07e1f853f026b`. | Existing bounded DAILY repair represented by PR #47 and the project’s approved workbook contract; no financial rounding/coercion is introduced. | `main` @ `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`. | Preserve header order, values, dates, nulls, and integer monetary cells through XLSX save/read-back. | `K_CODE` | Materialize each mapping as `[row.get(header) for header in headers]` before calling `write_table`. | Owner expressly directed proceeding with Path 3; code/test/workflow scope limited to this regression. | Focused test writes and reopens XLSX; exact header/value order, row/column counts, date handling, None, integer money, formats, and freeze panes match. | Focused synthetic fixture only; says nothing about an accepted 185-sheet production workbook. |
| Regression coverage | No DAILY serialization regression file exists on `main`; prior candidate test is not accepted as a result on this SHA. | Test the real repository function, not a duplicate implementation. | Same base. | Reproduce the observable mapping-versus-values defect and verify the round-tripped workbook. | `K_TEST` (coverage gap) | Add one focused XLSX round-trip test only. | Covered by explicit Path 3 instruction. | Test passes on the exact new branch SHA. | Do not alter existing tests to accommodate incorrect code. |
| Verification workflow | No DAILY-specific branch-pinned CI workflow on `main`. | Workflow must prove tested SHA; production simulations/trials are out of scope. | Same base. | Read-only token, exact branch filter, check out `github.sha`, compile and focused pytest only. | `WORKFLOW_DEFECT` (missing scoped verification path) | Add a temporary push-only workflow with artifact containing tested SHA, file hashes, dependency/runtime versions, test output and exit status. | Explicit Path 3 instruction authorizes this scoped synthetic verification workflow. | Successful Run on exact final code SHA; artifact contents read back and inspected. | No production Monte Carlo/trial/checkpoint/workbook or data artifacts. |

## Test plan
- **Reproduction:** the pre-fix implementation passes a dictionary to a row writer that iterates row values; the expected regression is that cells contain keys rather than numeric/date payloads.
- **Fix:** `tests/test_excel_daily_serialization.py` against the imported `scripts.excel_builder.write_daily_sheet`.
- **Regression:** reopen the produced XLSX and assert exact ordered values, integer monetary cells, null preservation, date number formats, and freeze panes.
- **Scope guard:** the workflow runs only compile and this focused test. No production data, Parquet, manifest, `SOURCE_SHA`, seed/RNG, sampling, cohort, trial IDs, source code identity, reference, `main`, or delivery files are changed.

This R4 records the proposed minimum before code/test/workflow edits. Any newly discovered rule requiring business interpretation is blocked rather than inferred.
