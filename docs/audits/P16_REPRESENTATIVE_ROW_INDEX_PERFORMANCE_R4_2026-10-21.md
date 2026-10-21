# R4 — P16 representative-sheet quadratic row indexing — 2026-10-21

## 1. Scope and authorization

This R4 covers one code-only performance correction on `tmp/p16-provisional-outputs-20261021` after inspecting the supplied job URL for Run `39567081092`, Job `119111824431`. The user's continuing instruction was “قم بكلما يلزم”. The change is limited to bookkeeping in the provisional candidate builder; it does not alter business rules, source identity, statistical policy, source/cohort/artifact identities, test definitions, workflow definitions, or `main`.

No existing Run is cancelled or re-run by this R4. A subsequent CI run, if triggered by the candidate code change, remains a provisional build only: no delivery acceptance, merge, or Release is implied.

## 2. Live evidence

- Repository: `yasmin977209-ux/motorcycle-simulation`.
- `main` HEAD remains `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`; the live `main` comparison is identical to this SHA.
- Candidate branch: `tmp/p16-provisional-outputs-20261021`, tested HEAD `b39fb854becf2060872a2249c7c2ccd426d5585b`.
- Code under review: `scripts/excel_builder_p16.py`, blob `c9bdbc99cdecc4752f14c855a44d6df8b2d8a3f2`, function `write_representatives`.
- Run `39567081092`, Job `119111824431`, conclusion `cancelled`; runner setup logged at `2026-10-21T08:08:53.854Z`, and `The operation was canceled` at `2026-10-21T14:09:14.456Z`, after approximately six hours. The loaded workflow specifies `timeout-minutes: 360`. The timestamps and configured limit strongly indicate the job timeout; the literal log line itself is “The operation was canceled.”
- Targeted deterministic regressions passed: `22 passed in 1.06s`.
- All 25 scenario-artifact acquisitions and tar-stream extraction passes completed by `2026-10-21T08:10:02.886Z`; the workbook writer then began. The representative-sheet writer completed 17 of 25 scenarios. It began representative scenario 18, `C050_G050`, at `13:30:30.163Z` and logged extraction completion at `13:30:31.231Z`; no `representative_scenario_complete` was recorded for that scenario before cancellation.
- Scenario 17 (`C050_G070`) reported `elapsed_seconds=2217.482` (~36.96 minutes) from its scenario start to completion. The logged free disk at scenario 18 extraction was about 89.8 GB, so the available evidence does not indicate disk exhaustion as the cause.
- Artifact `12350709424`, `7,764` bytes, SHA-256 `9183afeb9461afccc514c2bea9e05fcd4bbbb0a54aaf16db11269d24f53a4a90`; it is a small evidence bundle, not the seven deliverables. Final-register steps were skipped.

## 3. R4 defect table

| Element | Current state | Governing evidence | Branch and SHA | Controlling code/config | Defect class | Minimal change | Authority | Acceptance criteria | Risks |
|---|---|---|---|---|---|---|---|---|---|
| Per-row index in `write_representatives.append_row` | Calls `ws.max_row` after every appended row. In OpenPyXL, deriving `max_row` scans stored cells; the worksheet grows to many rows and millions of styled cells. The repeated scan is quadratic-style work and is consistent with the sharply increasing scenario duration in the log. | Job `119111824431` progress timings; code blob `c9bdbc99cdecc4752f14c855a44d6df8b2d8a3f2`, lines around `write_representatives` / `append_row`. | `tmp/p16-provisional-outputs-20261021` at `b39fb854becf2060872a2249c7c2ccd426d5585b`. | `row_num = ws.max_row` inside `append_row`; `start_row = ws.max_row`; final `ws.max_row - start_row`. | `K_CODE` | Maintain a local monotonic row counter initialized once after the header. Increment it once per `ws.append`; use that counter for row styling, scenario start rows, and rows-written counts. Preserve cell values, header order, comments, and number formats. | Narrow code repair under the user's “قم بكلما يلزم” continuation instruction; no protected inputs/rules are affected. | Existing targeted regressions pass on the changed SHA; all 25 representative scenarios finish; the builder saves and independently reopens/audits both 185-sheet workbooks and all seven named outputs within the configured limit. Delivery remains NOT_ACCEPTED pending separate acceptance audit. | An off-by-one counter could misplace comments/styles or misreport row counts; the existing regression suite and output read-back must detect this. This change does not by itself guarantee 360 minutes is sufficient for all remaining stages. |

## 4. Change boundaries

Allowed: one implementation-only edit in `scripts/excel_builder_p16.py` to replace repeated worksheet-size scans with constant-time row tracking.

Not included: tests/workflows edits; `main`; state/manifest/source changes; trial generation or Monte Carlo; changes to seed, RNG, trial IDs, cohort, Parquet or historical data; changing business rules or acceptance policy; merge, delivery acceptance, or Release.

## 5. Required verification and status

- Pre-change reproduction evidence: Run `39567081092` stopped during scenario 18 after the configured six-hour limit.
- Repair verification: run the existing P16 deterministic suite on the exact repaired SHA; require a completed builder, exact ordered 185-sheet contract for both workbooks, no formula/error cells where required, explicit pending MaxCase / partner-balance disclosures, all seven expected outputs, and per-output SHA-256 / byte size / provenance manifest.
- Regression: preserve all representative role assignments (P10=131, P50=29, P90=18, LossCase=304 from `Loss.json`, MaxCase trial 60 for C050_G000), source SHA, manifest identity and statistical policy.
- Until successful full artifact read-back and independent audit: `PARTIAL`; delivery `NOT_ACCEPTED`; Release `BLOCKED / NOT_AUTHORIZED`.
