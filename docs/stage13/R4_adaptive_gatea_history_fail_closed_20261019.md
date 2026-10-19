# R4 — Stage 13 adaptive Gate A history fail-closed

- Date: 2026-10-19
- CP: `CP-STAGE13-ADAPTIVE-GATEA-HISTORY-FAIL-CLOSED`
- Candidate branch: `tmp/cp-stage13-excel-compat-20261017`
- Candidate HEAD before change: `b371170d139a54ae037f3e5173ec07e3fbb5daf7`
- Required base/main HEAD: `647c19826b90d8224ce73ef9b90c306a45e03fb0`
- Normative reference SHA-256: `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`
- Current candidate blobs before change: assembler `5db91022eb7a6c70d721d024e69081a99d6351ea`; tests `9ebd609f4822d03011c58a98841f254ac7a81d42`.

## R4 — before change

| Item | Current state | Governing source/decision and branch | Controlling text | Ruling |
|---|---|---|---|---|
| Historical Gate A statuses in adaptive history | `_validate_adaptive_cohort` accepts `PASS`, `FAIL`, `PENDING`, and `BLOCKED` as structurally valid checkpoint statuses. For a non-final checkpoint, it rejects `overall_status=SCENARIO_STABLE`, or rejects when all gates pass but stopping is not forced by the P50 continuation rule; it does not reject an earlier Gate A `FAIL/BLOCKED/PENDING` before a later final PASS. | Main `docs/governance/DECISIONS_LOG.md`, D-2026-10-10-01; candidate branch `tmp/cp-stage13-excel-compat-20261017`. Main Stage 7 orchestration at `647c19826b90d8224ce73ef9b90c306a45e03fb0` also records the operative fail-closed behavior. | D-2026-10-10-01: “Gate A يطابق المرجع/الذهبي.” Stage 7 orchestrator: when the latest Gate A status is not `PASS`, set `final_status` to `blocked` or `failed`, persist the state, print `GATE_A_PREFLIGHT_BLOCKED=...`, and refuse additional trials. The checkpoint loop also breaks on Gate A `BLOCKED/FAIL`. | `K_CODE`: the Stage 13 validator can accept a cohort history that contradicts the Gate A stop rule used to create the cohort. This is a fail-closed history-validation gap, not evidence that production data actually contains such a history. |
| Evidence and business rules | Assembler validates that submitted checkpoint refs/digests are populated and the ordered map matches, but it does not fetch external Gate A evidence. | Existing Stage 13 adaptive R4 contract and this CP boundary. | The assembler validates submitted evidence structure and binding; it does not itself prove a production Gate A provider or create Gate A acceptance. | Preserve the existing interface. This CP will not invent or connect a golden provider. |

## Minimal correction

Reject any adaptive checkpoint whose `gate_a_status` is not exactly `PASS` before accepting any later checkpoint in that scenario. Keep the existing status-schema check and all Gate B, seven-metric, P50 continuation, source/cohort, per-trial digest, and ordered-map rules intact.

Add synthetic parametrized regressions for an earlier N=600 checkpoint marked `BLOCKED` or `FAIL`, followed by an otherwise passing final checkpoint at N=1200. Those crafted histories currently expose the gap because the final passing point can cause the cohort to be accepted despite the earlier Gate A stop. No simulation is run; the fixtures remain synthetic and test-only.

## Acceptance criteria

1. An adaptive history with Gate A `BLOCKED`, `FAIL`, or `PENDING` at any checkpoint is rejected before any later final PASS can legitimize it.
2. Existing valid synthetic adaptive history still passes the validator; other gate criteria and thresholds remain unchanged.
3. Error is a stable, explicit Stage 13 validation code identifying scenario and checkpoint N.
4. No Workflow/test workflow, `main`, `state.json`, source SHA, master seed/RNG, sampling policy, threshold, cohort ID, historic Parquet/data, production trial, merge or Release changes.
5. Exact-head pytest remains `PENDING/BLOCKED` because the live candidate records disagree over whether the temporary test Workflow authorization applies to this branch. Do not edit/create/trigger a Workflow to work around that conflict.

## Execution status before change

This R4 was written and read back before the implementation/test edits. The CP is limited to fail-closed assembler validation and synthetic regression coverage on the candidate branch.
