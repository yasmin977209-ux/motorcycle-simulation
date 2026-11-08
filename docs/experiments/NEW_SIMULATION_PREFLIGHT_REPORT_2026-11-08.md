# تقرير مراجعة جاهزية تجربة المحاكاة الجديدة — 2026-11-08

**Experiment:** `NEW-SIM-EXP-2026-11-08`  
**Protocol:** `docs/experiments/NEW_SIMULATION_EXPERIMENT_PROTOCOL_2026-11-08.md`  
**Branch under review:** `docs/new-simulation-protocol-20261108`  
**Reviewed source pin:** `002b74893ca9dfea864e83fecc558f2388748ffe`  
**Disposition:** `BLOCKED_BEFORE_EXECUTION`  
**Scope of this review:** live GitHub inspection, raw-byte identity verification, source/validator/workflow inspection, decision reconciliation. No workflow dispatch, Trial, Simulation, Monte Carlo, Golden revalidation, or data mutation was performed.

---

## 1. Executive result

The approved reference bytes and the proposed source tree can now be identified with substantially better evidence than at protocol creation. However, the proposed S6/C100 identities in E2 are not accepted by the current source validators and checkpoint configuration, and no existing workflow implements the approved new-lineage workload. Environment reproducibility, durable storage, secret/security checks, global fail-fast orchestration, and independent review are also incomplete.

**Do not dispatch the new simulation.** The current E2 decision requires a separate final owner confirmation, and this preflight found an additional identity-contract incompatibility that must be resolved by an explicit owner decision before implementation or execution.

## 2. Verified live baseline

| Item | Live evidence | Disposition |
|---|---|---|
| `main` | `1d67cd56d326a9c42f7ecf324fa284dcc129acd4` | unchanged/read-only |
| Working base | `tmp/d1-rebuild-20261101` at `f2ffb9743c8b9aff9fd9d4cadcdb5484e6069866` | unchanged |
| Documentation branch | `docs/new-simulation-protocol-20261108` at initial review HEAD `1491aefa84d061ef2b08cd3ea1e290a0bf3fb58b` | isolated |
| PR #83 | open, Draft, unmerged; base `tmp/d1-rebuild-20261101`; head `1491aefa84d061ef2b08cd3ea1e290a0bf3fb58b` | review only |
| PR #83 reviews/comments | 0 reviews, 0 review comments, 0 issue comments | independent review not supplied |
| Actions for protocol branch | 0 workflow runs | no CI execution |
| Historical E2 Run `41958935113` | completed/success; 20 scenario jobs and aggregate job succeeded | old-identity Replay only; not new-lineage execution |
| D0 historical | `BLOCKED / MISSING_EVIDENCE` for `PASS_GAP_FREE` | unchanged |

## 3. PF-01 — governing reference bytes and approval

<badge>PASS_SCOPED</badge>

Fetched the exact GitHub Raw bytes at:

`https://raw.githubusercontent.com/yasmin977209-ux/motorcycle-simulation/1491aefa84d061ef2b08cd3ea1e290a0bf3fb58b/docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md`

- Raw-byte SHA-256: `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`
- Size: `401397 bytes`
- Git blob SHA-1: `9fe43bfbb2cbfd2bb7f7010866e7469506d22c33`
- Containing commit: `1491aefa84d061ef2b08cd3ea1e290a0bf3fb58b`
- Owner decision file: `docs/governance/D-2026-10-30-REFERENCE-V2.4.0.md`, Git blob `58f89bc016523f1350345428b4a224ac42a8b130`, Raw-byte SHA-256 `1076b3e876d3db1a7e6ab4473fedb22226dfda0cb499d230ba3a0c2a9652a95d`.
- Decision status: `APPROVED_BY_OWNER`; it names the exact SHA-256 above and effective date 2026-10-30.

The uploaded v2.4.0 archive's 401,397-byte member independently produced the same SHA-256. This is a byte-identity cross-check, not a substitute for the GitHub Raw verification above.

**Governance note:** the reference's opening status line still reads `PROPOSED_FOR_OWNER_ADOPTION — NOT_EFFECTIVE_YET`, and the decision's Arabic filename differs from the current repository path. The decision is explicit and matches the exact bytes; the stale header/path alias should be corrected by an append-only governance correction record, not by silently editing the approved reference bytes. This report does not change the reference.

## 4. PF-02 — model source pin and source-tree identity

<badge>PASS_SCOPED</badge>

E2 decision explicitly selects source pin `002b74893ca9dfea864e83fecc558f2388748ffe`, with tree SHA `9cfaa2a8a57cfaf62beeb4a4166c042553173159`. The commit's direct diff from its parent `1cfc6c13fbe8344a9f433ebc340a7f3d6c0cbaa9` changes only the E2 Workflow concurrency setting (`cancel-in-progress: false → true`). That does not mean the commit lacks the model source: its full tree contains the repaired model and execution scripts.

Selected Git blob identities at old execution source `a23ba71f48487f3ebead99bc30039b14ef9b7609`, repair-reference commit `a5573eb1891ed2c56b01f6c9b3ccfe9619a08358`, and selected source pin `002b748...`:

| File | Old S6 `a23ba71` | Repair anchor `a5573eb` | Selected pin `002b748` |
|---|---|---|---|
| `monte_carlo.py` | `7897d6de31653b18038d07e5e2793b9c41efe18d` | `dab5fdec1325c76700a39ec4713656574fada828` | `98992c7dd5bc0dfe01cd94b2d17a9e2e9b64c8c1` |
| `accounting.py` | `0575c1ee8d94577e386b709b801f3e86f6fbb8fc` | same | same |
| `daily_engine.py` | `5c84732a8e18e89a3979600ca8bf05181df6f4d0` | same | same |
| `rng.py` | `dc042883b25011c91911c443631023d5c32a838a` | same | same |
| `entities.py` | `1cb1a348131931e2d6632c283290444e6aa4f03a` | same | same |
| `state_machine.py` | `8fe52dfe159487b79aa583e1ce5d41fb87fc39d5` | same | same |
| `constants.py` | `76c7b9ade9c7b4d98a7c78a6c5b2c09a577a2efc` | same | same |
| `dateutils.py` | `faa665b6222b33ef12f8af1588f1d4b9eddd65ec` | same | same |
| `requirements.txt` | `7201e50fdaf4c03511953b57c0514e92276acf10` | same | same |

The selected source pin is technically identifiable. The future Run Manifest must still separate `model_source_sha=002b...` from the commit that contains/dispatches the new Workflow, and checkout the model source explicitly by this pin. No new-run manifest exists yet.

## 5. PF-03 — identity and configuration compatibility

<badge color="danger">BLOCKED</badge>

The E2 decision proposes:
- S6 `cohort_id=s6-v23-rebuild-20261105`
- C100 `cohort_id=c100-v23-rebuild-20261105`
- `MASTER_SEED=20270101`
- 20 stochastic scenarios × Trial IDs 1..2400 = 48,000 S6 Trials.
- Five C100 paths × 300 deterministic executions = 1,500 records.

The selected source does not accept these cohort IDs:

1. `scripts/s6_first_checkpoint.py` constructs `cohort_id=f"s6-v23-{args.source_sha[:8]}"` (line 531); it has no `--cohort-id` argument. With source `002b...`, the derived S6 cohort is `s6-v23-002b7489`, not the E2-approved `s6-v23-rebuild-20261105`.
2. `scripts/s6_daily_path_identity.py::_identity` rejects any cohort other than `s6-v23-{source_sha[:8]}`, except one pinned historical C100 identity (`source_sha=965281...`, `cohort_id=c100-v23-s4-20261026-965281d5`). The proposed new C100 cohort is rejected by this contract too.
3. `scripts/s6_checkpoint_config.json` is still pinned to old S6 `SOURCE_SHA=da1a9ea9...`, old cohort `s6-v23-da1a9ea9`, and historical previous-run IDs. On GitHub Actions, `_s6_action_checkpoint_config()` loads this file and `apply_action_checkpoint_config()` rejects a different source SHA. The configuration also resumes from the historical checkpoint rather than providing a clean new-lineage start.
4. `scripts/s6_first_checkpoint.py` contains no CLI `--cohort-id`; the current daily path/aggregate validators also reconstruct the derived cohort string internally.
5. `scripts/s4_c100_golden.py` accepts environment `S4_COHORT_ID`, but its existing workflow hardcodes the old C100 source/cohort and old branch; downstream daily-path validation still rejects the proposed new C100 cohort.

This is not a cosmetic naming issue. Using the approved E2 IDs with current source code fails closed; silently substituting derived IDs would change the owner's approved identity. Supporting the requested IDs requires a formally approved identity-contract/code/config change and a newly pinned source commit, or a revised owner decision selecting compatible identities. No such change is authorized in this preflight.

## 6. PF-04 — source/code review

<badge>PASS_SCOPED</badge>

Static inspection confirms the repaired `monte_carlo.py` changes the daily snapshot projection to persist the full accounting balance snapshot. Core accounting, daily engine, RNG, entity, state-machine, constants and date utility blobs listed in section 4 are unchanged between the historical source, repair anchor and selected source pin. The dedicated schema unit test `tests/test_s6_daily_balance_snapshot_schema.py` explicitly constructs an initial project and calls `_daily_snapshot`; its comment says it does not call `run_single_trial` or `run_day`.

This is a scoped static inspection, not a complete independent code audit. It does not prove all 48,000 runs balance. The `scripts/s6_first_checkpoint.py` cohort/configuration constraints in section 5 remain a blocking execution defect. An independent reviewer must inspect the full source diff and the final workflow before execution.

## 7. PF-05 — runtime/dependency reproducibility

<badge color="danger">BLOCKED</badge>

The selected `requirements.txt` blob is unchanged, but it is not a lock file:
- `pyarrow` and `pyyaml` have no version pins.
- Other dependencies are range-pinned, not exact versions.
- Existing workflows use differing Python versions (S6 workflow Python 3.11; the separate C100 determinism check uses Python 3.12).
- No exact dependency lock/export, container digest, or environment manifest has been attached to this proposed run.

Before execution, freeze exact Python version, OS/runner image, dependency versions/hashes, locale/timezone and all environment variables; prove a clean install from the frozen lock. Do not update the model source merely to accommodate an unreviewed dependency upgrade.

## 8. PF-06 — workflow readiness and execution design

<badge color="danger">BLOCKED</badge>

No current workflow implements the new S6+C100 lineage:
- `.github/workflows/simulate.yml` is an N=300 first-checkpoint workflow, with push triggers limited to old branches. It is not the approved 48,000-Trial new-cohort run.
- `.github/workflows/e2-s6-deterministic-replay-reconstruction.yml` checks out original execution source `a23ba71...`, applies replay instrumentation, and retains old S6 source/cohort. Run `41958935113` succeeded as old-identity Replay, not new-lineage execution.
- `.github/workflows/s4-c100-golden-v23.yml` hardcodes source `965281...`, cohort `c100-v23-s4-20261026-965281d5`, and branch `tmp/s4-c100-golden-v23-20261026`; it requests `contents: write` and commits outputs to that branch.
- The S6 script's Actions-only checkpoint config is pinned to the historical source/cohort and previous run.

A separate, reviewed, manually gated workflow is required after the owner resolves the identity incompatibility. It must checkout the model source by exact pin, carry the approved cohort as an explicit and validated identity, write only to new unique paths, use least-privilege permissions, and never reuse historical checkpoints or output paths. It must also separate S6 and C100 jobs/outputs.

## 9. PF-07 — safe static tests

<badge color="warning">NOT_RUN</badge>

The following tests are suitable candidates for a source-free/simulation-free preflight job after their imports and fixtures are independently confirmed:
- `tests/test_s6_daily_balance_snapshot_schema.py` — initial-project snapshot projection only; explicitly does not call `run_single_trial` or `run_day`.
- `tests/test_s6_daily_path_identity_contract.py` — fixture-based identity/schema/balance validation.

No exact-pin run was executed for this report. No Actions workflow was dispatched. Do not use the full `simulate.yml` or C100 execution workflow as a substitute for static validation; they run actual Trials or a broader suite.

## 10. PF-08 — artifact storage, retention and restore

<badge color="danger">BLOCKED</badge>

The new lineage has no approved, verified two-failure-domain storage plan, no exact destination/path confirmation, no capacity estimate based on actual output size, and no new-lineage restore test. Existing Actions artifact retention is limited (the S6 first-checkpoint workflow sets 14 days for scenario artifacts and 30 days for aggregate). The existing D0 handoff reports Dropbox upload pending and OneDrive raw readback 403 for a different historical recovery bundle. Those facts do not prove durable storage for this new run.

Before execution, calculate the expected volume from representative output sizes, confirm both authorized durable destinations, verify access/retention, and run a small non-simulation storage write/readback/restore test. Do not upload or overwrite historical evidence as part of this experiment.

## 11. PF-09 — security/secrets

<badge color="warning">NOT_RUN</badge>

No secret scan or artifact/log redaction audit was run at the selected source pin. The existing C100 workflow requests `contents: write` and pushes generated files; it is not a suitable least-privilege template. New execution must use the minimum permissions, avoid printing credentials, scan the final diff/workflow, and prove logs/artifacts contain no secrets before dispatch.

## 12. PF-10 — fail-fast, concurrency and recovery

<badge color="danger">BLOCKED</badge>

The current workflows do not implement the E2 immediate-stop requirement for the new combined rebuild:
- Existing `simulate.yml` matrix sets `fail-fast: false`.
- The E2 replay workflow at `002b...` sets `cancel-in-progress: true`; it is an old-identity replay workflow, not a safe new-lineage orchestrator.
- No new S6 workflow currently cancels dependent scenario work on the first financial fingerprint mismatch and records all partial outputs as diagnostic-only.
- No approved idempotent restart/recovery plan exists for the new identity.

A new orchestrator must use a unique concurrency group, `cancel-in-progress: false` for unrelated runs, explicit fail-fast cancellation only for this experiment's child jobs, immutable per-scenario outputs, and a resume strategy that cannot duplicate Trial IDs or silently consume historical artifacts.

## 13. PF-11 — independent review and owner confirmation

<badge color="danger">BLOCKED</badge>

- PR #83 is Draft/open/unmerged.
- It has zero reviews, zero review comments and zero issue comments.
- No independent reviewer has signed the source/workflow/preflight matrix.
- E2 decision `OWNER_APPROVES_DETERMINISTIC_ACCOUNTING_REBUILD` still states `WAIT_FINAL_OWNER_CONFIRMATION` and `FINAL_OWNER_CONFIRMATION_REQUIRED_BEFORE_ANY_TRIAL`.
- The existing E2 approval does not authorize this report to bypass the separate final confirmation.

A reviewer must approve the exact preflight report commit and final source/workflow identities. The owner must then issue a separate final confirmation. The current user instruction to continue review does not replace the E2 decision's explicitly required final execution confirmation.

## 14. Existing Run 41958935113 — correct scope

Run `41958935113` is completed/successful. Its 20 scenario jobs and aggregate job succeeded; it produced 20 scenario replay artifacts plus an aggregate artifact. The E2 decision explicitly records that it checked out original execution source `a23ba71...`, applied `scripts/e2_prepare_replay_source.py`, and retained old S6 `SOURCE_SHA=da1a9ea9...`, old cohort `s6-v23-da1a9ea9`, and old seed. It is `REPLAY_RECONSTRUCTED_NOT_ORIGINAL_PRESERVED` for the old identity. It is not the proposed new S6/C100 cohort, and its success must not be relabeled as a new run.

## 15. Required owner decision before implementation

The owner must resolve the mismatch between the E2-approved cohort IDs and the selected source's enforced identity contract. The decision must choose one explicit route:

A. Amend the E2 scope to use cohort IDs supported by the exact pinned code, including a valid distinct C100 identity, if and only if that remains acceptable to the owner; or

B. Authorize a narrowly scoped metadata/identity-contract change that supports the already approved S6 and C100 cohort IDs, update the checkpoint configuration and validators, pin the resulting new source commit, and explicitly approve the new SOURCE_SHA. This must not alter business logic, accounting, RNG algorithm, thresholds, or historical records.

The owner must also confirm C100's 300-repeat-to-one-Golden comparison contract, the exact S6 48,000 fingerprint comparison, and the planning estimate. No choice is made by this report.

## 16. Final preflight matrix

| Gate | Result | Evidence summary |
|---|---|---|
| PF-01 Reference bytes/approval | `PASS_SCOPED` | Raw SHA-256 matches owner decision; stale header/path alias noted |
| PF-02 Model source pin | `PASS_SCOPED` | E2 source pin and full source tree/blob identities checked |
| PF-03 Identity/configuration | `BLOCKED` | Approved cohorts rejected by current code; old checkpoint config |
| PF-04 Code review | `PASS_SCOPED` | Core diff reviewed at file-identity level; independent audit pending |
| PF-05 Runtime/dependencies | `BLOCKED` | No exact lock/environment manifest |
| PF-06 Workflow readiness | `BLOCKED` | No new-lineage workflow; existing workflows are incompatible |
| PF-07 Safe tests | `NOT_RUN` | Safe candidates identified; no exact-pin run |
| PF-08 Storage/restore | `BLOCKED` | No two durable verified destinations/restore plan |
| PF-09 Security/secrets | `NOT_RUN` | No secret scan/redaction evidence |
| PF-10 Fail-fast/recovery | `BLOCKED` | Existing workflows do not implement required new-lineage stop behavior |
| PF-11 Independent review/owner confirmation | `BLOCKED` | No independent PR review; final owner confirmation pending |

**Overall:** `BLOCKED_BEFORE_EXECUTION`. This is a readiness judgment, not a simulation result.

## 17. Actions explicitly not performed

- No Workflow dispatch, no Trial, no Simulation, no Monte Carlo, no Golden revalidation, no N expansion.
- No source/cohort/seed/Trial identity mutation.
- No business rule, accounting rule, RNG, threshold, or reference modification.
- No historical Artifact/Manifest mutation, backfill, zero-fill, or inference.
- No main write, PR merge, Release publication, or final acceptance declaration.

## 18. Next safe sequence

1. Record an owner decision resolving the identity-contract incompatibility.
2. Implement only the authorized metadata/config/workflow changes on a new isolated branch; assign and verify the resulting source pin.
3. Freeze dependencies/runtime and establish durable storage/readback.
4. Run only the two identified safe static tests on the exact pin, with a workflow proven not to invoke Trials.
5. Obtain independent review of exact final HEAD, source pin, workflow, storage, and fail-fast behavior.
6. Present the completed report and exact run manifest draft for explicit final owner confirmation.
7. Only after that confirmation may the new S6/C100 run be dispatched.

---

**Final status:** `BLOCKED_BEFORE_EXECUTION`  
**Historical D0:** `BLOCKED / MISSING_EVIDENCE` — unchanged  
**Project gates:** unchanged  
**Approval to execute:** `NOT_GRANTED`
