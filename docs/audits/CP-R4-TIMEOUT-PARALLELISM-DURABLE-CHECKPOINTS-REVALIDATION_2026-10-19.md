# CP-R4-TIMEOUT-PARALLELISM-FAIL-CLOSED — Durable checkpoint implementation revalidation — 2026-10-19

## Executive disposition

**IMPLEMENTED ON CANDIDATE; STATIC READ-BACK ONLY; NOT VERIFIED BY TEST EXECUTION; DO NOT MERGE.**

The candidate contains an implementation for persisting each completed Stage 7 50-trial block together with its scenario state in one Git commit, restoring and validating the persisted prefix, and rejecting stale checkpoint writes. The final-workflow summary is fail-closed and checks scenario artifacts against the exact workflow attempt.

No Pytest, YAML parser, workflow, CLI, Monte Carlo, Trial, or Checkpoint was executed. Local cloning/testing was unavailable because the execution environment could not resolve github.com. This report is not a test PASS or production acceptance.

## Authority and scope

The owner explicitly approved CP-R4-TIMEOUT-PARALLELISM-FAIL-CLOSED on a candidate branch only. The protected boundaries remain: no main/reference/state write, no SOURCE_SHA/master_seed/RNG/sampling/cohort/Trial ID/statistical-policy change, no historical dataset/Parquet mutation, no production Workflow or Monte Carlo/Trial/Checkpoint execution, no PR merge/closure, and no Release.

## Live repository identity

- Repository: yasmin977209-ux/motorcycle-simulation.
- main HEAD: 647c19826b90d8224ce73ef9b90c306a45e03fb0.
- main/state.json blob: 2178260bb18efeb81437486f13b6d10cf5e85936.
- main state: stage=12-CLOSED; repository_status=FINAL_DELIVERY_BLOCKERS_OPEN; source_sha=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b; sha_semantics=parent_state_commit_pointer.
- Candidate branch: tmp/cp-stage7-timeout-parallelism-20261019.
- Candidate HEAD: f69b08033420d6cfe043a1654ab69b101577b683.
- GitHub compare: ahead_by=37, behind_by=0; exactly four changed paths:
  - .github/workflows/stage7-full-run.yml — 498 additions, 172 deletions.
  - scripts/stage7_state.py — 560 additions.
  - scripts/stage7_run_trial_block.py — 10 additions.
  - tests/test_stage7_authoring.py — 537 additions, 26 deletions.
- Final read-back blobs:
  - Workflow: 514aff8bbde36e961f077469989b1245dff52c51.
  - Durable state/store: 7da0173bbae08e74f6eccfd83a953f19b1525c49.
  - Trial-block metadata writer: 9842acf6187728b1984ed06edbbbc3bb638daaa4.
  - Test file: 4cdd532398a020b9e79c8152dfa2936e8eb3e496.
- PR #46 remains OPEN / DRAFT / UNMERGED; no new PR was created.

## Implementation read back on candidate

### 1. Timeouts, parallelism, and orchestration

- The internal 40-minute JOB_TIMEOUT_MINUTES cutoff and its early final_status=timeout exit path are absent from the current candidate Workflow.
- The matrix job external ceiling is timeout-minutes: 360; this is the platform limit, not an unlimited runtime. Preflight and final-report jobs retain their separate 15-minute guardrails.
- max-parallel: 25, the unchanged 25-scenario matrix, and fail-fast: false are present. GitHub runner capacity may reduce actual simultaneous starts.
- Each simulation block is capped at 50 Trial IDs. This is an operational checkpoint granularity; statistical evaluation targets, gates, Trial identities, and seed/RNG rules were not changed.
- Workflow logs include restore, legacy migration, and durable-progress markers with scenario, Trial-ID range, committed count, next statistical checkpoint and prefix fingerprint.

### 2. Durable persistence and restoration

- Each new block writes its Parquet file and metadata containing scenario, source SHA, master seed, RNG-policy ID, statistical schedule ID, Trial-ID range/count, block fingerprint, Parquet SHA-256, and per-trial SHA-256 digests.
- The candidate state module builds an identity sidecar that binds Parquet bytes, metadata bytes, scenario/source/seed/policy/range/fingerprint, and origin run.
- The Parquet file, metadata sidecar, identity sidecar, and state.json are committed together on stage7-state/<scenario> using Git Data API objects and a single non-forced branch-ref update. The writer checks the observed state blob and branch head before committing; a stale writer raises StateConflict.
- Restore requires matching Parquet/metadata/identity file sets; validates remote blob SHA and the manifest; verifies source/seed/policy/range; rejects duplicate/gapped/non-prefix ranges and state-count mismatches; and restores only when any pre-existing local bytes match the durable copies.
- Legacy Artifact-only blocks are not blindly relabeled: the candidate attempts to verify each originating Run's head SHA and historical Stage 7 Workflow source SHA/master seed before generating a migration proof. Missing or unverifiable origin identity fails closed.
- The orchestrator validates local block metadata, Parquet digest, block fingerprint, per-trial digests and Trial-ID order before calculating the prefix. Current scenario artifacts are regenerated on a verified already-stable resume so the final summary does not rely on stale output from an earlier Run.

### 3. Fail-closed final summary

The final-report uses the current GitHub run attempt to select scenario artifacts. Each scenario must have exactly one final-fingerprint file and one statistics file, and they must agree with the state snapshot on scenario, source, trial count, fingerprint, artifact identity, and inclusion status. Missing, duplicate, unparsable or mismatched artifacts are classified as errors. The unified summary exits nonzero unless all 25 scenarios are stable, included, and have a count plus fingerprint, with zero timeouts or errors.

### 4. Targeted tests authored; execution not performed

The candidate test file now covers:
- byte and identity binding for durable manifests;
- SOURCE_SHA/master-seed drift rejection;
- atomic block + state persistence and restore;
- appending a next block without rewriting an immutable prior block;
- rejection of missing identity sidecars and stale state blobs;
- legacy migration rejection without a valid historical Workflow seed/source proof;
- the no-internal-timeout/360-minute cap/25-way parallelism/concurrency contract;
- current-attempt artifacts and regeneration of terminal artifacts on already-stable resumes; and
- fail-closed summary behavior.

These are source-level test definitions only. No Pytest result exists for candidate HEAD f69b08033420d6cfe043a1654ab69b101577b683. No YAML parser result exists. GitHub read-back and static marker checks only were performed.

## Blocking risks / remaining verification

1. **Execution evidence missing:** no test or YAML parser could be executed in the current environment because the GitHub host could not be resolved. The candidate is not accepted until targeted tests and syntax/YAML validation run on the exact candidate SHA in an authorized verification environment.
2. **SOURCE_SHA_DRIFT remains open on main:** the current model tree's daily_engine.py differs from pinned source SHA f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b. Stage 7 preflight compares model files to SOURCE_SHA and therefore remains a production blocker until separately resolved; this CP did not change it.
3. **GATEA_PROVIDER_MISSING remains open:** no production stability claim or additional production Trial/checkpoint is authorized by this CP.
4. GitHub API rate limits, storage growth on per-scenario state branches, six-hour runner limits, and real restoration after a process interruption have not been measured in execution. The design is source-reviewed only; do not claim operational success.
5. Existing unrelated blockers remain: undefined Stage 11 topology, missing scripts/stage13_assemble.py, incomplete seven-file delivery set, and governance/report gaps.

## Unchanged state

- main HEAD and main/state.json are unchanged.
- SOURCE_SHA, master_seed, RNG, sampling/cohort/Trial IDs, statistical rules, source/reference and historical data/Parquet remain unchanged.
- No Workflow, CLI, Monte Carlo, Trial or Checkpoint ran; no Run, Job or Artifact was created by this CP.
- tested_sha=NOT_RUN; run_id=NONE; artifact_id=NONE.
- No PR was opened/merged/closed and no Release was created.

## Final status and next action

**PARTIAL / DO NOT MERGE / DO NOT CLAIM TEST PASS.** The next permitted step is to obtain an execution environment that can run the scoped authoring tests and YAML/source checks against the exact candidate SHA, then address any failures without touching main or protected data. Production Stage 7 remains blocked on current SOURCE_SHA drift and Gate A provider evidence.
