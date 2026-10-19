# CP-R4 — Stage 7 exact-SHA verification and empty-restore fail-closed review — 2026-10-19

## Status
**CURRENT CANDIDATE VERIFICATION PASSED; ADDITIONAL K_CODE HARDENING IDENTIFIED; NO PRODUCTION RUN.**

## Live identities at review
- Candidate branch: `tmp/cp-stage7-timeout-parallelism-20261019`
- Candidate HEAD reviewed: `12a30e69c1fd406683ba97cc824c9d27b9fce918`
- Base `main` remains separate; its live HEAD is `7c41ac64c4b599f4e1d6a50be055f82cdd87a7b5`.
- Candidate files at the reviewed HEAD:
  - `scripts/stage7_state.py`: blob `5615178a40200dec90247b6ddae63cd93c07126f`
  - `tests/test_stage7_authoring.py`: blob `4afba1c7c66a60560bbe148cd503c38a67b9c4dd`
  - `.github/workflows/stage7-full-run.yml`: blob `b686004505f57e123708ce2d0aacce38b3d5033e`
  - `scripts/stage7_run_trial_block.py`: blob `9842acf6187728b1984ed06edbbbc3bb638daaa4`
  - `.github/workflows/stage7-authoring-verify.yml`: blob `5afce3f0dfd1ab47864f1fb03a18e679bc15bc9d`

## Exact-SHA verification evidence
- Authoring-only Run: [39188323789](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39188323789)
- Event: push; workflow `stage7-authoring-verify`; conclusion `success`.
- Tested SHA: `12a30e69c1fd406683ba97cc824c9d27b9fce918` (matches candidate HEAD above).
- Exact test output: `79 passed in 0.62s`.
- Other successful steps: Python AST parse; YAML lint; all 25 scenario IDs parsed (`ALL_25_OK`); JSON newline check (`JSON_NEWLINE_SERIALIZATION_OK`).
- Artifact list: empty; this is a source-verification workflow, not a production simulation.
- Earlier Run `39178436432` tested older SHA `09e66f203915609e3e5a199a11be6a1be890b1d6`; it is not evidence for the newer HEAD and is not used as such here.
- No production Stage 7 workflow, Monte Carlo, Trial, Checkpoint, CLI, workbook build, or final delivery was run.

## R4 — bounded code review before proposed edit

| Element | Current state | Governing scope / controlling text | Ruling |
|---|---|---|---|
| `StateStore.restore_trial_blocks` empty inventory | At lines 727–729, an empty Git-tree inventory returns `0` immediately, before comparing `expected_completed_trials`. | Owner-authorized CP-R4-TIMEOUT-PARALLELISM-FAIL-CLOSED; candidate branch only. Durable restore contract later requires the actual block prefix to equal the saved checkpoint count and fail closed on incomplete identity/prefix. | `K_CODE`: empty inventory with a positive saved checkpoint is not rejected by this method itself. The workflow currently catches the discrepancy later through `validate_trial_sequence`, but the restore API should fail closed at its boundary. |
| Minimal proposed change | If inventory is empty and `expected_completed_trials != 0`, raise `StateIntegrityError` with the existing durable block/state mismatch wording; return zero only when expected completed count is zero. | No change to model, source SHA, master seed, RNG, sampling, scenarios, trial IDs, data, thresholds, or production workflow execution. Candidate branch only. | Narrow defensive correction. |
| Regression test | Existing in-memory store fixture starts with `completed_trials=2` and no durable block files. Add an assertion that restore rejects an empty inventory when the expected checkpoint is positive; preserve successful zero-trial/empty-inventory behavior if already covered. | Same CP-R4 candidate scope; test edit must remain limited to this regression. | Acceptance: exact-SHA authoring verifier passes and the new test proves fail-closed behavior. |

## Finding classification and impact
- Classification: `K_CODE` (defensive contract gap; downstream orchestrator currently catches the sequence mismatch).
- Exact observed source branch: `if not listing: return 0`.
- Impact: direct callers can mistake a missing durable prefix for a clean zero-block restore; the current Stage 7 orchestration subsequently rejects positive `completed_trials` with `StateIntegrityError("trial sequence mismatch")`, so this is not evidence of silent acceptance by the current caller.
- Minimal fix and acceptance criterion are listed in the R4 table.
- No code change has been made as part of this report. The proposed candidate edit will be separately read back and validated against its exact SHA.

## Governance and remaining blockers
- `main/state.json` remains blob `2178260bb18efeb81437486f13b6d10cf5e85936`, stage `12-CLOSED`, status `FINAL_DELIVERY_BLOCKERS_OPEN`, pinned `source_sha=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, and `sha_semantics=parent_state_commit_pointer`.
- The live main branch includes the previously documented protected-branch incident; do not modify or roll back main without separate explicit owner approval.
- PR #46 remains OPEN / DRAFT / UNMERGED, with stale base SHA relative to the current main head; do not merge it.
- Production Gate A provider missing, SOURCE_SHA drift, undefined Stage 11 topology, missing Stage 13 assembler, incomplete/reconciled final seven-file delivery, governance/report mismatch, and G2 risk remain open.
- No merge, PR closure, Release, source/reference/state edit, or production execution is authorized by this report.
