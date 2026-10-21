# R4 — P16 representative-sheet row access complexity — 2026-10-21

## 1. Scope

This R4 records a second, closely related performance defect discovered in the logs for Run `39567081092`, Job `119111824431`, and authorizes one narrow change in `scripts/excel_builder_p16.py` on the provisional P16 branch. The goal is to remove repeated worksheet-dimension scans while preserving every value, style, comment, number format, and row-count contract.

No edits to tests/workflows/main, source data, identities, business rules, historical outputs, or production trials are included. A CI run triggered by the code commit remains a provisional validation run; it does not grant delivery acceptance or Release.

## 2. Evidence

- Repository: `yasmin977209-ux/motorcycle-simulation`.
- `main` HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- P16 candidate HEAD before this change: `48c92f3ad48e77130a5bd479b13a7b5344953bb6`.
- Relevant source blob before this change: `4a82e54810a2cbc1c1c83a11ac3fb307443c1bdc`.
- The previous performance R4 changed `ws.max_row` reads to an incremental `current_row` counter. The source still iterates `for cell in ws[row_num]` for every appended row.
- Run `39567081092` log has 25/25 scenario-artifact acquisitions completed, 17/25 representative scenarios completed and then step cancellation. The durations increased from roughly 10 minutes for the first representative scenario to 36.96 minutes for scenario 17. Scenario 18 extraction finished in about 1.07 seconds before cancellation. Disk remained near 90 GB free.
- Under OpenPyXL indexing semantics, `ws[row_num]` without explicit column bounds must determine the worksheet's maximum column. Worksheet dimension properties are computed from stored cells; resolving row slices repeatedly over a growing multi-million-cell worksheet can repeatedly scan its cell map. This is a code-level diagnosis consistent with, but not by itself a profiler trace proving, the logged slowdown.

## 3. R4 change table

| Element | Current state | Evidence | Defect class | Minimal change | Authorization | Acceptance criterion | Risk |
|---|---|---|---|---|---|---|---|
| Row styling loop | `for cell in ws[row_num]` repeatedly slices a growing worksheet with implicit column bounds for each appended record. | `scripts/excel_builder_p16.py` append helper, blob `4a82e54810a2cbc1c1c83a11ac3fb307443c1bdc`; Run `39567081092` progress timings. | `K_CODE` | Iterate a fixed range `1..len(headers)` and retrieve each cell with `ws.cell(row=row_num, column=col_idx)`; retain the same alignment, column-based formats, and date format. | User's explicit full delegation for engineering repair; limited to candidate implementation. | Same exact written cell values/order, comments and formats; deterministic regression suite passes; future run proceeds materially faster, completes 25 scenarios, saves and independently reads back two 185-sheet workbooks plus all five text deliverables and records per-file hashes/provenance. | Incorrect fixed bounds could omit styling; row-width guard and existing tests plus workbook readback detect the risk. This optimization alone does not prove all remaining builder stages fit the 360-minute bound. |

## 4. Change boundaries

Only replace the implicit row slice inside `append_row`. Do not change schemas, cell values, roles, payload validation, output names, source selection, artifact IDs, SOURCE_SHA, seed/RNG, trial IDs, cohort, Parquet, or acceptance rules. Keep the existing incremental `current_row` counter and `rows_written=current_row - start_row`.

## 5. Verification

- Check diff contains only the targeted iteration change.
- Read back the exact file/blob after writing.
- The next automatically triggered v4 run, if one is created, must execute on the exact new HEAD; its deterministic regressions and full artifact must be inspected under the one-read-per-Run policy.
- Until verified: status `PARTIAL`; delivery `NOT_ACCEPTED`; Release `BLOCKED / NOT_AUTHORIZED`.
