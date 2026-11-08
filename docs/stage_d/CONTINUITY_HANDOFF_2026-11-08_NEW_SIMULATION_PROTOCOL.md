# Continuity Handoff — New Simulation Protocol — 2026-11-08

## Resume point
- Repository: `yasmin977209-ux/motorcycle-simulation`
- Documentation branch: `docs/new-simulation-protocol-20261108`
- Branch base: `tmp/d1-rebuild-20261101` at `f2ffb9743c8b9aff9fd9d4cadcdb5484e6069866`
- Protocol commit at handoff preparation: `48f29a32183a0a5fe3e1496215f7a099f75ada22`
- Protected `main` baseline: `1d67cd56d326a9c42f7ecf324fa284dcc129acd4`; read-only.
- Protocol file: `docs/experiments/NEW_SIMULATION_EXPERIMENT_PROTOCOL_2026-11-08.md`
- Session status: `docs/stage_d/SESSION_STATUS_2026-11-08_NEW_SIMULATION_PROTOCOL.md`

## Current disposition
`PREPARATION_ONLY — NOT_AUTHORIZED_FOR_EXECUTION`.

No Trial, Simulation, Monte Carlo, Golden revalidation, N expansion, or D0'–D6' execution has been dispatched by this work. No workflow was run. No historical evidence, manifest, source identity, main branch, or Release was modified.

## Key boundaries
1. D0 historical remains `BLOCKED / MISSING_EVIDENCE`; the new lineage cannot repair or rewrite old D0 evidence.
2. E2 rebuild preparation is not final execution authorization. The decision document says `WAIT_FINAL_OWNER_CONFIRMATION`.
3. S6 proposed scope: 20 scenarios × 2,400 Trial IDs = 48,000; new cohort `s6-v23-rebuild-20261105`; seed `20270101`.
4. C100 proposed scope: five deterministic paths × 300 repetitions; new cohort `c100-v23-rebuild-20261105`; the comparison contract requires explicit owner confirmation.
5. Candidate source pin `002b748...` must be distinguished from Workflow HEAD and verified as the intended Model SOURCE_SHA before use.
6. The exact approved v2.4.0 bytes must be recovered and SHA-256 verified; the repository copy inspected in this session has a conflicting proposed-status header.
7. The E2 old-identity replay Run `41958935113` is not evidence of execution of the new S6/C100 lineage.

## Resume sequence
- Re-read live branch and main refs, PRs, relevant E2 decision, governing reference decision, workflows, Actions and Releases.
- Complete PF-01..PF-11 in the protocol; document unresolved gates without guessing.
- Obtain independent preflight review.
- Present the exact verified identity, workload, comparison contract, resource estimate, and stop rules to the owner.
- Wait for explicit final confirmation matching protocol section 14.
- Only after confirmation may the separately authorized execution workflow be considered.

## Stop conditions
Do not dispatch any Trial/Simulation/Monte Carlo before final owner confirmation. Do not modify main, merge PRs, publish Releases, change business rules/thresholds/identities, mutate historical artifacts/manifests, backfill or zero-fill missing historical accounting fields, or claim final acceptance.


## Final remote readback correction — 2026-11-08
- Final branch HEAD is `880c2f6f04967dc7b95f86f2ba7aaabe3af9c31b` (the protocol's original file-creation commit is `48f29a32183a0a5fe3e1496215f7a099f75ada22`).
- Draft PR #83 is open and unmerged: https://github.com/yasmin977209-ux/motorcycle-simulation/pull/83. Base remains the working branch, not `main`.
- Diff is 4 files / 385 additions / 0 deletions. Main remains `1d67cd56d326a9c42f7ecf324fa284dcc129acd4`.
- No Actions run was associated with the final head; no workflow dispatch occurred.
- Git blob SHA readback is recorded in the session status. Raw-byte SHA-256 was not calculated; do not claim `VERIFIED_LIVE`.
- This is a documentation-only proposal. Do not dispatch execution without final owner confirmation after PF-01..PF-11.


## Full preflight review handoff — 2026-11-08
- Detailed report: `docs/experiments/NEW_SIMULATION_PREFLIGHT_REPORT_2026-11-08.md`.
- Protocol addendum: section 16, appended at commit `2f7c9aa30021d61f3cef41167b580e1e2b5d3c82`.
- Reference v2.4.0 Raw bytes verified live at the protocol branch: SHA-256 `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`, 401,397 bytes, blob `9fe43bfbb2cbfd2bb7f7010866e7469506d22c33`. Owner decision matches this exact hash. The file's stale proposed-status header and path alias remain documented; reference bytes were not changed.
- E2 source pin `002b748...` is a valid full source-tree commit, not merely a workflow diff. Model source and workflow head must remain separate in future manifests.
- Critical blocker: the E2-approved new S6/C100 cohort IDs do not pass current source validators; S6 code derives cohort from SOURCE_SHA, C100 daily identity permits only the historical C100 exception or the S6-derived format, and the Actions checkpoint config is pinned to old source/cohort/previous run. This requires an explicit owner decision before code/config changes.
- No current workflow is suitable for the proposed new S6+C100 run. Existing S6 N300, E2 old-identity replay and C100 historical workflow are not interchangeable.
- PF results: PF01/PF02/PF04 PASS_SCOPED; PF03/PF05/PF06/PF08/PF10/PF11 BLOCKED; PF07/PF09 NOT_RUN.
- PR #83 remains Draft/open/unmerged; no independent reviews or comments. No Actions run for the protocol branch.
- Resume: obtain owner decision on identity-contract route; then implement only approved code/config/workflow changes on a new isolated branch, lock runtime/dependencies, prove storage/security/fail-fast, run safe tests at exact pin, obtain independent review, then seek final owner execution confirmation.
- Do not dispatch any Trial/Simulation/Monte Carlo or Golden revalidation. D0 historical remains BLOCKED. No main write, merge, Release, historical mutation or gate promotion.


## End-of-session disposition — 2026-11-08
- Read the full preflight report before continuing.
- Overall status is `BLOCKED_BEFORE_EXECUTION`; no execution authorization exists.
- First required action is an explicit owner decision resolving the mismatch between `s6-v23-rebuild-20261105` / `c100-v23-rebuild-20261105` and current code's enforced cohort rules. The existing S6 checkpoint config is still pinned to the historical source/cohort and cannot be reused for a clean new run.
- Do not modify source/validators/config/workflows to bypass the mismatch. Any authorized change requires a new source pin and exact manifest.
- Then complete dependency lock, dedicated least-privilege workflows, storage/restore, security scan, fail-fast/recovery, safe exact-pin tests and independent review; only after those should the owner be asked for final execution confirmation.
- PR #83 remains Draft/open/unmerged. No Actions run was dispatched for this branch. No Trials/Simulation/Monte Carlo/Golden revalidation were run. Main and historical evidence remain untouched.

## Handoff addendum — Path B approved and implemented — 2026-11-08

The earlier handoff instruction to obtain an owner identity decision is superseded by the owner's explicit Path B approval at 2026-11-08T16:30:32Z. The approval covers only identity-contract code/config changes and creation of a new source pin for review; it does not authorize any Trial.

- Working branch: `fix/explicit-cohort-identity-20261108`
- Draft PR: #84, based on PR #83 protocol branch.
- Explicit S6 cohort: `s6-v23-rebuild-20261105`
- Explicit C100 cohort: `c100-v23-rebuild-20261105`
- Safe test Run `42500791300`: success; 11 identity tests passed, validators compiled, non-execution guard passed.
- Safe workflow environment: Ubuntu 24.04 / CPython 3.11.18 / pip 26.2.2 / exact package versions in `requirements-lock-py311.txt`. This is not yet a hash-locked wheel set or immutable runner image.
- Do not use historical run IDs/checkpoints; fresh S6 baseline is N=300. The old C100 evidence remains read-only historical reuse and is not the new C100 cohort.
- Verify final branch HEAD and all Raw SHA-256 / Git blob SHA-1 values before calling the source pin `VERIFIED_LIVE`.
- Complete a dedicated least-privilege simulation Workflow with fail-fast/recovery, two independent durable storage destinations plus restore test, secrets/redaction scan, and independent review.
- Only after those blockers are closed, request a separate final owner confirmation before any Trial or Monte Carlo dispatch.
- No simulation execution, N expansion, historical artifact mutation, main write, merge, Release, or final acceptance occurred. Overall status remains `BLOCKED_BEFORE_EXECUTION`.

## Identity-scope clarification — exact owner-approved values only — 2026-11-08

This addendum narrows any earlier wording that referred to a cohort “family” or pattern. The implementation accepts only the exact E2-approved values:
- S6: `s6-v23-rebuild-20261105`
- C100: `c100-v23-rebuild-20261105`

Other date variants or cohort IDs matching the same textual pattern are rejected. The exact historical C100 source/cohort exception remains unchanged and narrowly pinned. This is a fail-closed clarification; it does not authorize any additional cohort, Trial, or N expansion.

## Final verification and guard-scope correction — 2026-11-08

- The approved cohort contract is exact, not pattern-based: S6 `s6-v23-rebuild-20261105`; C100 `c100-v23-rebuild-20261105`. All other date variants are rejected. Historical C100 remains an exact source/cohort exception only.
- Final safe test run before the PR-trigger-only workflow correction: Run `42501711253`, candidate HEAD `1293d883071355200e90948fcce801f45aac7b7c`, `success`. It ran both approved safe suites: 13 passed in 0.95s; py_compile passed; non-execution guard passed; `SIMULATION_TRIALS=NOT_EXECUTED`.
- The safe workflow's pull-request base filter was corrected to `docs/new-simulation-protocol-20261108`, matching PR #84's actual base. The new branch HEAD must be re-read and the safe workflow run on that exact final HEAD before source-pin acceptance.
- Storage inspection: Dropbox rescue folder ~2.74 GB and OneDrive rescue folder ~4.11 GB / 85 children exist. Dropbox's `secondary_verified_mirror` is still the same Dropbox provider, not a second failure domain. OneDrive raw readback returned HTTP 403 `Database Is Read Only`; no byte-for-byte verification or restore test is complete. PF-08 remains `BLOCKED`.
- PR #84 remains Draft/open/unmerged with zero independent reviews/comments. PF-11 remains `BLOCKED`; dedicated simulation workflow, fail-fast/recovery, security scan/redaction, and separate final owner execution confirmation remain outstanding.
- No Trial, Simulation, Monte Carlo, Golden generation/revalidation, N expansion, main write, merge, Release, or historical evidence mutation occurred. Overall `BLOCKED_BEFORE_EXECUTION`.

## 2026-11-08 — Security, storage, environment, and owner-approval follow-up

- Model-source identity is now separate from the workflow/event HEAD. The exact candidate model-source commit is `ac0d009aa004976009ed01e97f96d019945e9ad6`; the workflow branch HEAD is separately pinned through protected environment variable `S6_EXECUTION_APPROVED_WORKFLOW_SHA`. S6 manifests record model `git_commit` and `workflow_head_sha` separately. C100 validates its checked-out model source.
- The manual execution workflow is owner-gated, uses a separate `execution-source` checkout, least-privilege read permissions, N=300 only, sequential fail-fast scenario execution, diagnostic-only partial artifacts, and no repository writes. It is not dispatchable until the workflow is present on the default branch and the protected environment is configured. It has not been dispatched.
- Runtime lock now contains 15 exact Linux x86_64 / CPython 3.11.18 wheel SHA-256 hashes. Hash-lock SHA-256: `074944b6a48090723f51a1f25e0d9dcf5e29f3a5df025b064bef485c2daa6fbf`. Safe CI regenerated all 15 hashes and matched the committed lock.
- Safe CI at branch HEAD `059ca9b6202b7cf02140a73f9d1bca9819e86856`: Run `42505862577`, success; 22 tests passed in 1.17s; compile checks passed; `SIMULATION_TRIALS=NOT_EXECUTED`.
- Gitleaks PR-diff scan found no leaks. Full reachable-history scan found nine unclassified `generic-api-key` findings. No secret values were emitted. Security remains blocked pending human classification and rotation of any confirmed live credentials. See `docs/experiments/SECURITY_STORAGE_ENVIRONMENT_REVIEW_2026-11-08.md`.
- One C100 reuse archive was fetched raw from OneDrive, restored, and ZIP-validated; its bytes matched Dropbox's provider content hash. This is scoped evidence only: Dropbox raw download and full-folder restore remain incomplete; storage is not PASS.
- Independent review remains pending. The review packet is `docs/experiments/INDEPENDENT_REVIEW_PACKET_2026-11-08.md`; it is explicitly not represented as an independent review.
- Conditional owner request is `docs/experiments/OWNER_FINAL_EXECUTION_APPROVAL_REQUEST_2026-11-08.md`. It asks for one initial checkpoint only: 20 S6 scenarios × 300 = 6,000 stochastic Trials and 5 C100 scenarios × 300 = 1,500 deterministic Trials, MASTER_SEED 20270101. No N expansion or final acceptance is authorized.
- The S6 aggregate still uses historical C100 reuse evidence; the new C100 Golden remains a separate evidence artifact and is not yet consumed by the S6 aggregate.
- No Trial, Simulation, Monte Carlo, Golden generation/revalidation, N expansion, main write, merge, Release, or historical evidence mutation occurred. PR #84 remains unmerged. Execution remains blocked.
