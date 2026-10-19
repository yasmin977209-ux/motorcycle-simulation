# CP-R4 — Empty durable-checkpoint restore fail-closed implementation — 2026-10-19

## Disposition
**CANDIDATE PATCH READ BACK; EXACT-SHA AUTHORING RUN QUEUED; RESULT NOT INSPECTED AGAIN UNDER M4. NOT READY TO MERGE.**

## R4 and implementation
This edit implements the bounded change authorized in the preceding R4 report:
- Report: [CP-R4-STAGE7-VERIFICATION-EMPTY-RESTORE-REVIEW_2026-10-19.md](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/tmp/cp-session-continuity-20261017/docs/audits/CP-R4-STAGE7-VERIFICATION-EMPTY-RESTORE-REVIEW_2026-10-19.md)
- Candidate branch: `tmp/cp-stage7-timeout-parallelism-20261019`
- Parent SHA: `12a30e69c1fd406683ba97cc824c9d27b9fce918`
- New candidate HEAD: `89224a0e202f27afeb62f0f08965592dcd7e008b`
- Changed paths only:
  - `scripts/stage7_state.py`, blob `0543373b570c793d6123aab65749aaca426b7284`
  - `tests/test_stage7_authoring.py`, blob `a8797935013e6a5aee6e8828e1c673ae22e71111`

### Minimal code change
When `_block_listing()` returns no durable block entries, `restore_trial_blocks()` now raises `StateIntegrityError("durable block/state checkpoint mismatch: blocks=0, state=N")` if `expected_completed_trials != 0`. It returns zero only for a zero-trial checkpoint. No model source, source SHA, seed/RNG, sampling policy, scenario set, trial IDs, production workflow, historical data, or state was changed.

### Regression test
Added `test_durable_restore_rejects_empty_inventory_when_checkpoint_is_positive`. It uses the existing in-memory store fixture with no durable block files and a positive checkpoint, asserting the fail-closed error.

## Validation state
- Previous HEAD `12a30e69c1fd406683ba97cc824c9d27b9fce918` had exact-SHA authoring-only Run [39188323789](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39188323789): `success`, `79 passed in 0.62s`. That result does **not** cover the new commit.
- After pushing this edit, the authoring-only verifier triggered Run [39285773426](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39285773426), exact head SHA `89224a0e202f27afeb62f0f08965592dcd7e008b`.
- First run inspection returned `status=queued`, `conclusion=null`. Per M4, no polling or second run inspection was performed. Current patch verification is therefore **PENDING / UNVERIFIED**.
- No production Stage 7 workflow, Monte Carlo, Trial, Checkpoint, CLI, workbook build, or final delivery was run.

## Acceptance / next action
The fix is accepted only if Run `39285773426` completes successfully on the exact SHA `89224a0e202f27afeb62f0f08965592dcd7e008b`, including the new regression test. If it fails, inspect the exact failing step and make only a minimal candidate correction under the same scoped CP-R4 authorization. Do not poll the queued Run under the current M4 inspection limit; use a later explicit review cycle.

## Unchanged governance
- `main` HEAD at this review: `7c41ac64c4b599f4e1d6a50be055f82cdd87a7b5`; do not modify or roll it back without separate explicit owner approval.
- `main/state.json` blob: `2178260bb18efeb81437486f13b6d10cf5e85936`, stage `12-CLOSED`, `FINAL_DELIVERY_BLOCKERS_OPEN`.
- PR #46 is OPEN / DRAFT / UNMERGED and its base SHA is stale relative to current main; do not merge.
- Gate A provider missing, SOURCE_SHA drift, undefined Stage 11 topology, missing Stage 13 assembler, incomplete final seven-file delivery and governance/report reconciliation, and G2 risk remain blockers.
- No merge, PR closure, Release, main/state/reference/source/RNG/sampling/cohort/trial/data change is authorized.
