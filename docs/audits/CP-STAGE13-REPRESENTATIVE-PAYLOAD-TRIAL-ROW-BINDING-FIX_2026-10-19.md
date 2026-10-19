# CP-STAGE13-REPRESENTATIVE-PAYLOAD-TRIAL-ROW-BINDING — candidate source correction — 2026-10-19

## Result

The candidate assembler received a code-only fail-closed correction for the R4 finding in the earlier read-only report. The test file and all Workflows remain unchanged. **Runtime validation remains pending**, because the exact-branch test execution authority conflict is unresolved.

## Identities

- Candidate branch: `tmp/cp-stage13-excel-compat-20261017`
- Candidate HEAD after change: `52a7c3b9a4151ab26968b55287e518c590426ba6`
- Current main HEAD: `7c41ac64c4b599f4e1d6a50be055f82cdd87a7b5`
- Candidate comparison: diverged, 23 ahead / 2 behind; no rebase/merge.
- Candidate assembler blob: `8bb785606bc268cd1ad8671518bfa96e3d009794`
- Candidate tests blob unchanged: `976ebc8365db7f2380f15317c677990e34a1269c`
- R4 before the change: [CP-STAGE13-REPRESENTATIVE-PAYLOAD-TRIAL-ROW-BINDING_2026-10-19.md](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/tmp/cp-session-continuity-20261017/docs/audits/CP-STAGE13-REPRESENTATIVE-PAYLOAD-TRIAL-ROW-BINDING_2026-10-19.md), blob `b7ae1fc8fc31102e7753c7931e1ce9e2a3eb956f`.

## Code-only correction

1. Builds a Trial-ID lookup from the validated scenario result rows. For each selected P10/P50/P90/Loss/Max Case role, the payload summary must have exactly the same field set as its selected source row and all field values must match. Boolean values are not allowed to pass merely because Python treats booleans as integers. Stable errors include `REPRESENTATIVE_SUMMARY_SCHEMA_MISMATCH` and `REPRESENTATIVE_SUMMARY_TRIAL_RESULT_MISMATCH`.
2. Requires every daily row to be an object carrying the same selected `trial_id`; otherwise `REPRESENTATIVE_DAILY_TRIAL_MISMATCH`.
3. For non-demo data modes, verifies each daily date is valid ISO and the dates advance by exactly one day, then binds the terminal `Cash`, `Net_Equity`, `Cumulative_Project_Profit`, and `Operating_Net_Profit` to the summary values. When `final_close_date` is provided, the last daily row's `date` must match it.
4. Demo mode remains a short synthetic presentation path: it still requires the summary/source result row to match and daily Trial IDs to match, but does not impose real-ledger continuity or terminal-accounting checks on the deliberately abbreviated demo rows.

## Verification and blockers

Read-back confirms the complete validator update at the new assembler blob and confirms the test blob is unchanged. No pytest, AST test of the repository source, YAML parse, Workflow, CLI, workbook generation, Monte Carlo, Trial or Checkpoint ran. No statement of PASS is made.

Stage13 canonical assembly remains blocked by the separately confirmed source-contract mismatch: all 25 official enriched archives contain only P10/P50/P90/Loss daily payloads, whereas normative D-2026-10-10-03 requires the fifth Max Case payload. This change does not invent, relabel or reconstruct a missing role. Gate A provider and other main blockers remain open.

No main/state/reference/workflow/test/data/source SHA/seed/RNG/policy/cohort/Trial ID changes, merge or Release. Main remains `7c41ac64c4b599f4e1d6a50be055f82cdd87a7b5`; main state remains blob `2178260bb18efeb81437486f13b6d10cf5e85936`, `12-CLOSED / FINAL_DELIVERY_BLOCKERS_OPEN`.
