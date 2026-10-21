# R4 — Stage 7 workflow concurrency and state fail-closed hardening — 2026-10-22

## Scope and baseline

- Base/main HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- Candidate branch: `tmp/cp-stage7-workflow-fail-closed-20261022`.
- Production workflow base blob: `4bb3b8df6742f51087b45eed1b9200468f12ac60`.
- Test base blob: `6a4e11399e2c6b85e9dc240a0c669f395a639e66`.
- Classification: `K_WORKFLOW + K_TEST`, candidate-only static/authoring tests. No production workflow run is authorized by this CP.

## Verified defects

1. Concurrency key `stage7-full-run-${{ github.run_id }}` differs across runs and cannot serialize concurrent executions on the same branch.
2. Preflight holds `actions: write`, cancels any other incomplete Stage 7 run found in a hard-coded branch scan, then force-PATCHes existing `stage7-state/<scenario>` refs back to `SOURCE_SHA` when their `run_id` differs. These are remote side effects before model-file byte identity is checked.
3. Model source identity is only fully checked later in each simulation job. Consequently the preflight could have mutated state refs before detecting `MODEL_SOURCE_DRIFT_DETECTED`.

## Intended minimal change

- Concurrency group: `stage7-full-run-${{ github.workflow }}-${{ github.ref }}`, with `cancel-in-progress: false`; runs for the same workflow/ref queue instead of running side by side.
- Remove preflight's automatic cancellation and switch to read-only detection: if another incomplete run is present (including an older run that predates the new concurrency group), emit a concrete conflict and stop.
- Set workflow `actions: read`, retaining `contents: write` only because the scenario StateStore writes state JSON and checkpoints.
- Move full pinned model-file identity comparison into preflight **before any state-branch decision**. A source mismatch exits before state access/changes.
- For an existing scenario state ref: resume only if its stored `run_id` equals this run ID. If it belongs to any other run or the state cannot be read/identified, emit `STAGE7_STATE_CONFLICT` and stop. Never PATCH the existing ref to `SOURCE_SHA`, delete state, or silently restart from a clean history.
- Keep the runtime's separate source-identity check in each simulation job as defense in depth.
- Update authoring tests to assert serialization and non-destructive fail-closed behavior. Add a candidate-only read-only verification workflow that compiles/parses code and runs `tests/test_stage7_authoring.py`; it must not invoke the production workflow.

## Owner authorization / restrictions

The owner explicitly authorized all necessary work in the conversation (2026-10-21/22). This R4 narrows that delegation to the listed workflow/test lines. It does not authorize running the production workflow, canceling existing jobs, patching remote state refs, executing trials/checkpoints, changing source SHA/seed/RNG/trial identity, changing statistical acceptance, merging, or releasing.

## Acceptance criteria

1. YAML parses and authoring tests pass on exact candidate SHA.
2. Same workflow/ref gets a stable concurrency group, with non-canceling queue semantics.
3. No automatic stale-run cancellation endpoint is invoked and no `PATCH` of any `stage7-state/*` ref exists in preflight.
4. Preflight validates exact model-source byte identity before it inspects or decides about state refs.
5. Same-run state may be preserved; state from another run or invalid state fails closed without mutation.
6. No production workflow run, Monte Carlo, Trial, or Checkpoint occurred.
7. Candidate compare lists only this R4, the Stage 7 workflow, authoring test file, candidate verification workflow, and continuity record.

## Status

`PENDING_STATIC_READBACK_AND_CI`. This is a preventative, candidate-only workflow repair; it does not establish Gate A or overall stability.


## Exact-SHA static verification result

- GitHub Actions Run `39683073413`, candidate SHA `5c3f77091bec0037e6331253ce2e8fa855ee391c`, conclusion `success`: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39683073413.
- YAML parse and compile checks passed; `tests/test_stage7_authoring.py`: `67 passed in 0.23s`.
- Verified workflow blob after the safe-preflight changes: `30b07f55c000b3b5ca1319b34d1b41f5e8f36557`; test blob at exact tested SHA: `8b5912818c255e1ff8a7624734157cd2a2d57678`.
- Static read-back confirms concurrency key uses `github.workflow` + `github.ref`; workflow permissions are `contents: write` and `actions: read`; preflight has no run cancellation API and no force PATCH; exact model-file identity check precedes any state-ref request; existing non-current-run state fails closed.
- The earlier candidate runs `39682882666`, `39682928810`, and `39682998530` failed during iteration (the former embedded-script duplication and then one incorrect test path assertion). Those exact failures were fixed and the later successful SHA above is authoritative; no production workflow was dispatched.
- No trial, checkpoint, Monte Carlo, source SHA, seed/RNG, dataset, or main branch was changed. This CP improves safety but does not establish Gate A or validate runtime limits.
- Disposition: `PASS_STATIC_AUTHORING_CI / PRODUCTION_WORKFLOW_NOT_RUN`.


## Final refinement and latest-SHA verification

- After the first successful static run, refined the active-run scan to select only `status == "in_progress"`, because queued runs should serialize through the workflow/ref concurrency group rather than be treated as already-active conflicts. This still detects old active runs that predate the concurrency group; it does not cancel them.
- Final verification Run `39683924760`, exact SHA `bd63a22ed86655264cf99cbb3aff4d94fb66eca6`, conclusion `success`: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39683924760.
- YAML parse and module compile passed; `tests/test_stage7_authoring.py`: `67 passed in 0.36s`. Tested workflow blob `5508a069ec902d2e75b439cee22b8a0d0bfe4719`; tested authoring-test blob `a6d80e350eb4a568ebca3889431e410c0989f8fc`.
- The prior Run `39683906067` failed because its tested SHA's test file asserted the former active-run predicate; the subsequent commit corrected that assertion and its exact-SHA rerun passed. Run `39683073413` passed the preceding implementation before this predicate refinement. No production workflow was run during any of these iterations.
- Final disposition: `PASS_STATIC_AUTHORING_CI / PRODUCTION_WORKFLOW_NOT_RUN`; main unchanged.


## Queue preservation correction — final exact-SHA run

- Added `concurrency.queue: max`. GitHub's default concurrency mode keeps at most one pending run and replaces that pending run when a newer one arrives; queue mode now allows up to 100 pending runs to wait. This is required to support the stated non-cancellation requirement. Source: GitHub Actions concurrency documentation, https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency.
- Final exact-SHA verification Run `39684779907`, SHA `16df1cab1245297fc31b91ed5b008b721018b936`, conclusion `success`: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39684779907.
- YAML parse and compile passed; `tests/test_stage7_authoring.py`: `67 passed`. The exact test now asserts `queue == "max"` in addition to the stable workflow/ref concurrency group and `cancel-in-progress: false`.
- The preceding Run `39684747170` failed because it tested the workflow update before the matching regression-test update was committed; the next exact-SHA run above passed with the test and workflow changes present together.
- Final tested workflow blob: `5d7e1e5c73c7fdf619d26ce80987dac4ad79c929`; final tested test blob: `4f44e16aafdfa566b62105721a76dc8f1d4d5c86`.


## Final post-main-merge candidate verification (2026-10-22)

- Main baseline included in this candidate is `ed751ca0993ddec282743c6913864fd173c4d1fd`, which contains the reviewed Gate B fail-closed fixes and exact pinned model source.
- Latest exact-SHA verification Run `39688725055`, tested SHA `7b990adbd981f3f7aedba356628432eac7e1bbec`, conclusion `success`: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39688725055.
- Every step passed: exact candidate checkout, Python setup, requirements installation, YAML parse for `.github/workflows/stage7-full-run.yml`, module compilation, and `tests/test_stage7_authoring.py` (67 deterministic authoring tests).
- Final tested blobs: production workflow `5d7e1e5c73c7fdf619d26ce80987dac4ad79c929`, authoring tests `4f44e16aafdfa566b62105721a76dc8f1d4d5c86`; candidate-only verification workflow `d521bc99fea631b4f10694ff020e8cfcc49d22eb`.
- Main-source integration did not reintroduce prior Stage 7/Gate B code: the main baseline already has the exact pinned source and fail-closed N/Boolean/near-zero code. No source SHA constant, seed/RNG, cohort/trial ID, state ref, Parquet, or production data changed.
- The production Stage 7 workflow was **not run**. Static checks do not validate runtime timeouts or create Gate A proof. The five state blockers remain as documented; Gate A stays BLOCKED.
- Disposition: `PASS_STATIC_AUTHORING_CI / PRODUCTION_WORKFLOW_NOT_RUN`; ready for independent review, not evidence of operational Stage 7 or final-delivery acceptance.
