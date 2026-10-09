# CP-C R4 — Excel artifact coverage

Date: 2026-10-10. Read-only pre-change review for a temporary Stage 13 artifact-coverage workflow. No simulation reruns; no engine, tests, RNG, reference, or state.json changes.

| Item | main | stage3b-preserved | Reference | Judgment |
|---|---|---|---|---|
| Excel builder | `scripts/excel_builder.py` exists on main, blob `eace6fb37aadae9f703bca206581e4249a823c09`; expects per-scenario trial-results Parquet, daily distribution Parquet, and representative payloads. | Builder is absent on the diagnostic branch. | §§15.2–15.4: 185 worksheets; §§18.1–18.2: complete per-scenario outputs and representative payloads. | DEVIATION: current input schema must be checked before reuse. |
| Historic workbook | Stage 9A artifact 11507380986: 185 sheets, zero Excel errors, XLSX SHA `0fb325fc9e196a534ba8ab7484dcfd0541cefd3a2ca37c3b6f930e3215f62f6d`, but only 9005 trials and dataset SHA `892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6`. | No comparable output artifact. | §18.1 requires the correct dataset; an older workbook does not evidence CP-C for 11005 trials. | DEVIATION: cannot reuse as current deliverable. |
| Current dataset | Stage12: 25 Parquets, 11005 trials, 22546465 daily rows; source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`; seed 20270101; aggregate SHA `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`. Daily accounting fields only. | No matching Stage12 dataset. | §§14.5–14.7 require representatives selected on Final_Net_Project_Equity with full daily payloads; §§18.1–18.2 require inventory, partner memo, guarantees, contracts and detailed accounting. | Potential structural blocker: prove full-payload coverage of any newly selected trials before Excel PASS. |
| Proposed helper workflow | New, exact branch pin only; no wildcard, workflow_dispatch, self-dispatch or simulation trial execution. | Diagnostic workflows not copied. | Project trigger and no-replay policy. | MATCH if it is read-only and fails closed when details are missing. |

## Classification
- MATCH: historic workbook was valid for its own 9005-trial dataset.
- DEVIATION: historic workbook identity differs from current 11005-trial identity.
- VIOLATION: none found in pre-change review.
- No existing builder modification, no trial rerun and no state.json update.

Decision: proceed only with a narrow read-only preflight to test whether required representative details for the 11005-trial dataset are available; do not claim Excel PASS absent evidence.