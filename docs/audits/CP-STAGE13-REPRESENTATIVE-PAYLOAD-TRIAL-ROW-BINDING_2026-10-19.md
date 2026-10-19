# CP-STAGE13-REPRESENTATIVE-PAYLOAD-TRIAL-ROW-BINDING — read-only R4 — 2026-10-19

## Disposition

**Static contract gap found; no code or tests changed.** The candidate validator proves that a representative payload uses the selected Trial ID and has non-empty daily rows, but it does not bind the payload's summary values to the corresponding trial-results row. This is a potential cross-sheet data consistency defect, not evidence that any official artifact is corrupted.

## Live identity

- Candidate branch: `tmp/cp-stage13-excel-compat-20261017`
- Candidate HEAD: `adfc04dd5a2b633c64515a0b4e4f7ae7b5ca1156`
- Current main HEAD: `7c41ac64c4b599f4e1d6a50be055f82cdd87a7b5`
- Candidate compares as diverged from current main, 22 ahead / 2 behind; no rebase or merge.
- Candidate assembler blob: `4cb4632fe787c92ee87190769bbbf05b65b61416`
- Candidate assembler-test blob: `976ebc8365db7f2380f15317c677990e34a1269c`
- The actual inspected source TAR/ZIP and all-25 source-package audit are recorded separately; all 25 enriched archives contain four representative roles (P10/P50/P90/Loss), no MaxCase.

## R4

| Element | Current state | Governing decision / exact source | Ruling |
|---|---|---|---|
| Representative payload binding | `_validate_representatives` calls `select_representative_trial_ids`, checks role assignment equality, checks `payload["summary"]["trial_id"]` equals the selected ID, and checks `payload["daily"]` is non-empty. It does not compare other summary fields to the selected row from `trials_by_scenario`. | Candidate `scripts/stage13_assemble.py` blob above, lines 1279–1309. D-2026-10-10-03 in main `docs/governance/DECISIONS_LOG.md` defines the representative roles and IDs by trial result fields; D-2026-10-10-04 requires canonical Excel assembly from the supplied dataset. | `K_CODE`: a payload with a correct `trial_id` but changed `final_cash`, `final_net_project_equity`, or partner entitlement can pass this validator, while trial statistics are computed from `trial_results.parquet`. |
| Workbook use | `write_daily_sheet` and `write_acctg_sheet` consume representative daily rows; `write_partner_sheet` uses the representative summary's final partner entitlements. The representative summary therefore crosses into workbook output independently of trial-row statistics. | Candidate assembler blobs/functions `write_scenario_detail`, `write_daily_sheet`, `write_acctg_sheet`, `write_partner_sheet`; no output workbook was generated in this review. | Static inspection proves separate code paths consume related values, not an actual mismatch in the historic artifact. |
| Proposed minimal correction | For each selected representative, compare every shared TrialResult field in its summary against the selected `trials_by_scenario` row; fail closed on absent/mismatched fields. Additionally validate representative daily rows have the matching `trial_id`, ordered contiguous dates, and terminal fields consistent with available summary fields (`final_cash`↔`Cash`, `final_net_project_equity`↔`Net_Equity`, `cumulative_project_profit`↔`Cumulative_Project_Profit`, `operating_net_profit`↔`Operating_Net_Profit`, `final_close_date`↔`date`). Avoid mapping partner entitlements to unrelated reinvestment-balance columns. | R4 only; candidate code/test scope. | Safe minimal direction; exact field/type/null behavior must be pinned by synthetic fixtures before accepting a correction. |
| Validation boundary | Existing workflow authorization records conflict over whether the temporary Stage13 test workflow may be reused on this exact branch. | `OWNER_SCOPE_AUTHORIZATION_20261017.md` vs `R4_clean_main_excel_compat_20261017.md` on the candidate branch. | No test edit or Workflow change is performed here. Obtain a clean, explicit authorization for the exact test execution/change scope or an already-approved non-workflow route. |

## Acceptance criteria for any later approved correction

1. A matched payload and selected trial row pass.
2. Mutating a summary financial field while preserving `trial_id` is rejected.
3. A daily row with a wrong `trial_id`, non-contiguous/reordered date, or terminal-value disagreement is rejected.
4. Canonical source identity/fingerprint validation, representative role selection/tie-breaking and all cohort IDs remain unchanged.
5. No source, seed/RNG, sampling/threshold/cohort/Trial ID, historic data, main/state, Workflow, production output, merge or Release changes.

## Current blocker and boundary

The source contract independently remains blocked because the normative five-role requirement includes MaxCase but all 25 current official enriched archives contain only four roles. This report neither relabels another role nor derives a missing payload. No tests, workbook, CLI, Workflow, Monte Carlo, Trial or Checkpoint was executed; no project data or protected branch was changed.
