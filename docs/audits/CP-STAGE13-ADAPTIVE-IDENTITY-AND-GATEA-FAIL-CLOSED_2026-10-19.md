# CP-STAGE13-ADAPTIVE-IDENTITY-AND-GATEA-FAIL-CLOSED — 2026-10-19

## Disposition

**Candidate-only code/test corrections saved and read back; runtime validation remains `PENDING/BLOCKED`.** Two Stage 13 adaptive-assembler fail-closed gaps were isolated and corrected on a temporary candidate branch. Neither change runs simulation trials or changes model data. No workflow was modified or triggered.

## Live identities

- Candidate branch: `tmp/cp-stage13-excel-compat-20261017`
- Candidate HEAD after the edits: `4fa2c633162b0134a48cfc2ccbf2b6b948108ae0`
- Base/main HEAD: `647c19826b90d8224ce73ef9b90c306a45e03fb0`
- Compare: 14 commits ahead, 0 behind; ten changed paths in the candidate branch.
- Candidate assembler blob: `7561f73340ac45b0f4ab71b677c33b771eac008b`
- Candidate assembler-test blob: `f707dc9af12f01ca705b225f4a34df570f85210d`
- R4 before-change record for scenario/parameter identity binding: [R4_adaptive_scenario_parameter_binding_20261019.md](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/tmp/cp-stage13-excel-compat-20261017/docs/stage13/R4_adaptive_scenario_parameter_binding_20261019.md), read-back blob `d2d68345db2895cb6c66e4f6c25d641c154c98a0`.
- R4 before-change record for Gate A checkpoint history: [R4_adaptive_gatea_history_fail_closed_20261019.md](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/tmp/cp-stage13-excel-compat-20261017/docs/stage13/R4_adaptive_gatea_history_fail_closed_20261019.md), read-back blob `551c79e0f4fb961755ef6d59033b2cfc2217b853`.

## R4 finding A — row parameter identity

The adaptive validator previously validated a row's exact TrialResult field schema and recomputed its SHA-256 digest, then validated scenario coverage and the ordered digest map. It did not also prove that the row's `collection_probability` and `recovery_rate_pct` values encode the scenario key. A row could therefore have an internally valid digest and aggregate map while pairing, for example, a `C085_G100` key with different parameter values. This was classified `K_CODE`; it is not evidence of production data corruption.

**Candidate-only correction:** for every adaptive row, derive the expected collection probability from the scenario's three-digit C field and recovery percentage from its three-digit G field. Reject booleans, nonnumeric/nonfinite or unequal probabilities, and recovery values that are not non-boolean integers equal to the scenario's G field. Stable error: `ADAPTIVE_TRIAL_SCENARIO_PARAMETER_MISMATCH: <scenario>:<trial_id>`.

Two parameterized synthetic cases mutate the C or G parameter, recompute the row digest, and also recompute both aggregate ordered-map digests. They assert that semantic scenario/parameter mismatch is still rejected, rather than relying on a stale hash to trigger rejection. Existing per-trial schema/digest checks were retained.

## R4 finding B — Gate A history fail-closed

The adaptive validator allowed `PASS`, `FAIL`, `PENDING`, and `BLOCKED` as checkpoint statuses and did not prevent an earlier non-PASS Gate A point from being followed by a passing final checkpoint. That disagrees with the approved policy and the main Stage 7 orchestration's fail-closed behavior: a Gate A status other than `PASS` blocks/fails that scenario and stops further trial blocks. The governing `D-2026-10-10-01` states: “Gate A يطابق المرجع/الذهبي”. Classification: `K_CODE`; no claim is made that production history actually exhibits this pattern.

**Candidate-only correction:** every adaptive checkpoint after the N=300 coverage-only point must have `gate_a_status == "PASS"`. Otherwise the assembler raises `ADAPTIVE_GATE_A_CHECKPOINT_NOT_PASS: <scenario>:<N>:<status>` before permitting a later checkpoint to establish a stable cohort. Three synthetic test cases cover prior `BLOCKED`, `FAIL`, and `PENDING` at N=600 followed by an otherwise passing N=1200 final checkpoint. Gate B, seven-metric §2.5, P50 continuation rules, evidence-reference structure, cohort/source identity, and output acceptance checks were not changed. This does not introduce or connect a Gate A provider.

## Change sequence and read-back

- Scenario/parameter R4 committed before code edit: `2d77e35845b3ea9babcb60fe896af9d5958485c8`.
- Parameter binding implementation: commit `19abcfcfdc9abe0c76783afb4b8d867dd1eb8407`, assembler blob `5db91022eb7a6c70d721d024e69081a99d6351ea`.
- Parameter mismatch regression cases: commit `5e0d028627c7f81035ea65f9804b756725725656`; a double-escaped newline in its aggregate-map fixture was detected by immediate read-back and corrected in commit `b371170d139a54ae037f3e5173ec07e3fbb5daf7`, leaving test blob `9ebd609f4822d03011c58a98841f254ac7a81d42`.
- Gate A R4 committed before its implementation edit: `f6770a8c7eb949c0b7367b725d14eec28ab777f9`.
- Gate A fail-closed implementation: commit `e1b5b101b66584c983a1ff24f3eace1148da3194`, assembler blob `7561f73340ac45b0f4ab71b677c33b771eac008b`.
- Gate A chronology regressions: commit `4fa2c633162b0134a48cfc2ccbf2b6b948108ae0`, test blob `f707dc9af12f01ca705b225f4a34df570f85210d`.
- Final read-back at candidate HEAD confirmed both R4 records, both code changes, and synthetic test sources are present. Source/read-back inspection only; no tests were executed.

## Test-workflow authorization boundary

The candidate's `OWNER_SCOPE_AUTHORIZATION_20261017.md` describes a temporary read-only test workflow authorized for this branch, but `R4_clean_main_excel_compat_20261017.md` says prior workflow approval was pinned to a different branch and is not reused. Those live candidate documents conflict, and the governing session policy says branch prose saying “APPROVED BY OWNER” is not by itself proof of owner approval. This CP therefore did **not** create, change, or trigger a Workflow. Exact-head pytest and workbook generation remain `PENDING/BLOCKED`; the historic synthetic Run `38995349182` tested an earlier SHA and is not evidence for this current candidate.

## Protected-state boundary and next action

- Main remains `647c19826b90d8224ce73ef9b90c306a45e03fb0`; `main/state.json` remains blob `2178260bb18efeb81437486f13b6d10cf5e85936`, stage `12-CLOSED`, `FINAL_DELIVERY_BLOCKERS_OPEN`, pinned `SOURCE_SHA=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`.
- Gate A production provider remains missing; SOURCE_SHA drift, undefined Stage 11 topology, absence of the Stage 13 assembler on main, and final seven-file delivery/report reconciliation remain blockers.
- No Workflow, `main`, state, reference, source/seed/RNG, sampling/threshold/cohort/trial identity, historical data, production trial, workbook, merge, PR closure, or Release changed.
- Next permitted action: resolve the conflicting exact-branch test workflow authorization through an explicit owner instruction or approved non-workflow execution path; then run the focused synthetic suite on the exact then-current candidate SHA and inspect the physical synthetic workbook/artifact. Do not promote this candidate's changes to `main` or call project delivery accepted.
