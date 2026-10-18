# CP-R4-TIMEOUT-PARALLELISM — Durable checkpoint and authoring verification addendum — 2026-10-19

## Disposition

**ADDITIONAL STATIC FIXES READ BACK; AUTOMATED TEST CONCLUSION STILL UNVERIFIED; DO NOT MERGE.**

This addendum supersedes the candidate identity and file-blob snapshot in the earlier same-day revalidation report for current state only. The earlier report remains a historical record; this addendum is the latest candidate read-back as of the recorded SHA.

## R4 review and ruling

| Element | Current state observed before this edit | Governing reference / decision and branch | Controlling text | Ruling |
|---|---|---|---|---|
| Durable block inventory: scripts/stage7_state.py | _block_listing used a Contents API directory listing, which can omit entries once the directory exceeds the endpoint's listing limit. Each completed trial block requires three durable files. | Owner-authorized CP-R4-TIMEOUT-PARALLELISM-FAIL-CLOSED; candidate branch only. Project scope says preserve Trial IDs and fail closed on loss or mismatch. | “لا تغيّر ... البيانات التاريخية/Parquet أو sampling/threshold/cohort/trial IDs”; “اجعله fail-closed عند الفقد/التكرار أو اختلاف source/fingerprint/schema.” | Replace folder listing with recursive Git tree inventory; raise StateIntegrityError if GitHub says the tree is truncated. Does not change model source, data, seed, trial identities or statistical policy. |
| Durable inventory test: tests/test_stage7_authoring.py | Existing in-memory GitHub fake supported Contents listing only and had no test beyond the directory listing size. | Same explicit CP-R4 scope; candidate-only tests. | “أي تعديل test/workflow يتطلب R4 أولًا وموافقة محددة.” The owner-approved CP-R4 covers candidate-only verification of durable checkpoint behavior. | Update the fake API to emulate recursive tree listing; add a fixture with 1,105 entries and assert fail-closed behavior on a truncated tree response. |
| Static contract test | A new assertion checked the Git tree implementation string in the Workflow text instead of in the state module where the implementation resides. | CP-R4 acceptance tests; exact candidate files. | “قبل أي تغيير وثّق R4” and “لكل عطل: النص الحرفي، السبب المثبت ... أقل إصلاح ومعيار القبول.” | Correct the assertion to read scripts/stage7_state.py. This fixes the test, not production behavior. |
| Authoring verification Workflow | The verification Workflow only listened to the historical authoring branch and hard-coded checkout to that old branch; therefore it could not verify this candidate HEAD. | Owner-approved CP-R4, scoped to candidate-only verification. No production Workflow run is authorized. | “الغاية المفوضة إنجاز المشروع كاملًا”; “لا تكتفِ بتقرير حالة ما دامت هناك خطوة هندسية مسموحة”; “أي تعديل test/workflow يتطلب R4 أولًا وموافقة محددة.” | Add the candidate branch to the non-production authoring-only Workflow trigger and checkout the pushed commit SHA so it tests the exact commit. The Stage 7 production Workflow remains untriggered by this branch. |
| Newline authoring check | Previous verifier used brittle grep/cat commands to inspect a JSON newline literal. | Same CP-R4 candidate verification scope. | “شخّص ... subprocess logs وstdout/stderr وعقد CLI ... اربط الاختبار بـSHA محدد وافحص النتيجة الحرفية لكل اختبار.” | Replace grep with an AST assertion that the metadata write_text expression appends a real newline character, rather than a literal backslash-n sequence. |

## Live repository and candidate identity

- Repository: yasmin977209-ux/motorcycle-simulation.
- main HEAD: 647c19826b90d8224ce73ef9b90c306a45e03fb0.
- main/state.json blob: 2178260bb18efeb81437486f13b6d10cf5e85936.
- Main state remains stage=12-CLOSED, repository_status=FINAL_DELIVERY_BLOCKERS_OPEN, source_sha=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b, sha_semantics=parent_state_commit_pointer.
- Candidate branch: tmp/cp-stage7-timeout-parallelism-20261019.
- Candidate HEAD: c3d26245361ed0d9f59254c6b23aed5bf304aecc.
- GitHub compare: 42 commits ahead / 0 behind main, exactly five changed paths:
  - .github/workflows/stage7-authoring-verify.yml
  - .github/workflows/stage7-full-run.yml
  - scripts/stage7_run_trial_block.py
  - scripts/stage7_state.py
  - tests/test_stage7_authoring.py
- Current read-back blob SHAs:
  - .github/workflows/stage7-authoring-verify.yml: 5afce3f0dfd1ab47864f1fb03a18e679bc15bc9d.
  - .github/workflows/stage7-full-run.yml: 514aff8bbde36e961f077469989b1245dff52c51.
  - scripts/stage7_run_trial_block.py: 9842acf6187728b1984ed06edbbbc3bb638daaa4.
  - scripts/stage7_state.py: 5615178a40200dec90247b6ddae63cd93c07126f.
  - tests/test_stage7_authoring.py: 8a43bc412c4b65ff5155816111a43e5338ba8c3b.
- PR #46 remains open/draft/unmerged on the continuity branch; its latest head must be rediscovered before any subsequent write.

## Additional fixes read back

1. Durable block enumeration now reads the recursive Git tree and converts all blobs beneath stage7-blocks/ into an inventory. If GitHub marks the tree truncated, the function raises StateIntegrityError rather than treating an incomplete inventory as complete.
2. The in-memory StateStore fake now emulates the recursive Git tree API. A new test fixture places 1,105 entries beneath stage7-blocks and checks full inventory, then marks the tree truncated and checks rejection.
3. The source-level Workflow assertion for recursive tree inventory now reads scripts/stage7_state.py, its real implementation location.
4. The non-production stage7-authoring-verify Workflow now triggers on pushes to tmp/cp-stage7-timeout-parallelism-20261019 and checks out the pushed commit SHA. It does not invoke the production stage7-full-run Workflow. Its newline check uses Python AST and verifies the runtime value of the appended string is a real newline.
5. Static read-back confirms the current candidate has no JOB_TIMEOUT_MINUTES / JOB_TIMEOUT_SECONDS / early internal timeout exit; the matrix retains the exact 25 scenarios, max-parallel=25, fail-fast=false, and the 360-minute external matrix-job ceiling; durable restoration/persistence and final-report fail-closed markers remain present.

## Execution status — unresolved

No Pytest, YAML parser, production Workflow, CLI, Monte Carlo, Trial, or Checkpoint execution was performed by this assistant. A local clone attempt failed with the exact transport error: fatal: unable to access 'https://github.com/yasmin977209-ux/motorcycle-simulation.git/': Could not resolve host: github.com.

The non-production authoring Workflow is configured to run on the candidate push and targets the pushed commit SHA. However, the available GitHub Actions connector does not expose listing or lookup of push-triggered runs; its commit-associated runs wrapper filters to pull-request-triggered runs, and the commit status query returned an empty statuses list. Accordingly no authoring run ID, job conclusion, tested SHA, or artifact ID has been verified. This must remain TEST_RESULT=UNVERIFIED, not PASS.

No production Workflow, simulation, Monte Carlo, Trial, or Checkpoint was run. main/state.json, SOURCE_SHA, master_seed, RNG, historical data/Parquet, sampling/cohort/Trial IDs, thresholds and statistical rules remain unchanged. The Stage 7 production gate remains blocked independently by SOURCE_SHA drift and missing Gate A provider evidence.

## Next permitted action

Use an authorized environment with access to the repository's GitHub Actions run listing to retrieve the non-production stage7-authoring-verify run triggered by candidate push, confirm its head_sha equals c3d26245361ed0d9f59254c6b23aed5bf304aecc (or a newer explicitly recorded candidate head), inspect every job/step result and artifact if present, and fix failures on the candidate only. Do not merge, close PRs, run the production simulation, or claim acceptance until exact-SHA verification passes and independent project gates are addressed.


## R4 follow-up — exact candidate authoring Run 39177883109 (pre-repair record)

**Observed run identity:** Run [39177883109](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39177883109), workflow `stage7-authoring-verify`, event `push`, branch `tmp/cp-stage7-timeout-parallelism-20261019`, exact `head_sha=c3d26245361ed0d9f59254c6b23aed5bf304aecc`; conclusion `failure`. Job `verify` ID `117824219222`. No artifacts were published. Job-step log confirms AST parse and YAML lint passed; command `python -m pytest -q tests/test_stage7_authoring.py` ended `6 failed, 72 passed in 0.52s`, exit code 1. The following R4 rulings are recorded before editing candidate tests.

| Element | Current state | Authority / branch | Exact observed contract or error | R4 ruling |
|---|---|---|---|---|
| Missing identity sidecar test | Durable persistence rejects incomplete file triplets before restore. | Owner-approved CP-R4-TIMEOUT-PARALLELISM-FAIL-CLOSED; candidate-only tests, no production run. | Expected regex `triplet sets differ`; actual `persisted Stage 7 block files are incomplete: Parquet/metadata/identity sets differ`. | `K_TEST`: update expected message to the exact fail-closed invariant. Do not weaken the exception requirement. |
| Preflight state-branch test A | Candidate verifies scenario/source identity and refuses state reuse/reset when a checkpoint is ambiguous. | Same CP-R4 scoped authority; candidate authoring test only. | Test expected `STAGE7_STATE_RESET=` and a forced PATCH of a state ref; candidate instead emits `STAGE7_STATE_WITHOUT_CHECKPOINT`, `STAGE7_STATE_IDENTITY_MISMATCH`, or `STAGE7_STATE_PRESERVED`. | `K_TEST` stale expectation of destructive reset. Replace with assertions that all 25 intended scenario branches are considered and ambiguous/mismatched state is preserved and rejected, never force-reset. |
| Preflight state-branch test B | Candidate derives state identity from `scenario` and `source_sha`, not originating run ID. | Same CP-R4 scope. | Test expected `jq -r '.run_id // empty'`, `STAGE7_STATE_RESUME=`, and reset-on-different-run logic; that logic is not in the candidate preflight. | `K_TEST`: assert identity-bound preservation/fail-closed behavior instead; do not restore run-ID-based branch reset. |
| Legacy artifact restore test | Candidate first checks durable `stage7-blocks` on the scenario's state branch; legacy artifact retrieval uses the saved `PREVIOUS_RUN_ID` and validates each origin Run head SHA plus its Workflow SOURCE_SHA/master seed. | Same CP-R4 scope; only authoring test, no artifact/production execution. | Test expected current-run endpoint `actions/runs/${GITHUB_RUN_ID}/artifacts?per_page=100`; candidate legacy path uses `actions/runs/${PREVIOUS_RUN_ID}/artifacts?per_page=100` after durable-storage lookup. | `K_TEST` outdated restore contract. Assert durable-first restoration, saved-run-only legacy retrieval, identity-proof guards and fail-closed diagnostics; do not reintroduce same-run-only lookup. |
| Runtime elapsed-time test | Per-block execution is in `scripts/stage7_run_trial_block.py`; workflow internal timeout cutoff was deliberately removed by CP-R4. | Same CP-R4 scope. | Test expected `JOB_STARTED_AT_EPOCH = time.time()` and `return time.time() - JOB_STARTED_AT_EPOCH` inside the Workflow text, where neither exists now. The runner measures per-block duration with `time.monotonic()`. | `K_TEST` obsolete location/contract. Test monotonic per-block measurement in the runner and the separate external 360-minute job limit; do not reinstate an internal timeout. |
| CP3 overlap fingerprint test | Candidate computes both fingerprints through multiline `monte_carlo.fingerprint_trial_results(...)` calls on the exact overlapping prefixes. | Same CP-R4 scope; model/trial identity must remain unchanged. | Assertions for `fingerprint_trial_results(stage7_prefix)` and `fingerprint_trial_results(cp3_prefix)` fail because source has multiline formatting and a `monte_carlo.` qualifier. | `K_TEST` brittle whitespace/string matcher. Normalize whitespace in the extracted snippet and assert both actual prefix-fingerprint calls plus contiguous overlap-count checks; no CP3 algorithm change. |

**Pre-edit R4 acceptance criteria:** preserve each behavior asserted above; only update tests to the candidate's fail-closed/durable architecture and correct whitespace-sensitive matching. Do not change business rules, SOURCE_SHA, seed/RNG, sampling policy, cohort, Trial IDs, production Workflow execution, `main`, `state.json`, PR state, or Release. Exact-SHA revalidation is required after the candidate test commit.
