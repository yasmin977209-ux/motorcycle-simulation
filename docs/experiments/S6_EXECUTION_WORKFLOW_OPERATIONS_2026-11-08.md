# S6 isolated execution workflow — operator and recovery procedure — 2026-11-08

## Workflow availability

- File: `.github/workflows/s6-isolated-execution.yml`
- Trigger: `workflow_dispatch` only.
- It is not available for dispatch until this workflow file is present on the repository default branch. PR #84 is still Draft/unmerged; do not merge solely to make it dispatchable.
- Select branch `fix/explicit-cohort-identity-20261108` for dispatch. The workflow HEAD and model-source SHA are separate identities.

## Protected environment configuration

Create environment `s6-simulation-execution` in repository settings and configure required reviewers before adding the approval values. Require owner/reviewer approval for each protected execution job; disable self-approval and admin bypass where repository policy permits.

Set these environment variables only after the owner decision and independent review are complete:

| Variable | Exact value |
|---|---|
| `S6_EXECUTION_ENVIRONMENT_LOCKED` | `true` |
| `S6_EXECUTION_APPROVED_SOURCE_SHA` | `ac0d009aa004976009ed01e97f96d019945e9ad6` |
| `S6_EXECUTION_APPROVED_WORKFLOW_SHA` | exact final workflow branch HEAD named in the owner decision |
| `S6_EXECUTION_APPROVED_COHORT_ID` | `s6-v23-rebuild-20261105` |
| `S6_EXECUTION_APPROVED_N` | `300` |
| `C100_EXECUTION_APPROVED_COHORT_ID` | `c100-v23-rebuild-20261105` |

Set environment secret `S6_OWNER_EXECUTION_DECISION_ID` to the exact new owner decision ID. Do not place a bearer token, API key, or other credential in a workflow input.

If any variable/secret is missing or mismatched, the execution job must fail before invoking a Trial.

## Dispatch values

- `source_sha`: `ac0d009aa004976009ed01e97f96d019945e9ad6`
- `s6_cohort_id`: `s6-v23-rebuild-20261105`
- `c100_cohort_id`: `c100-v23-rebuild-20261105`
- `trial_count`: `300`
- `owner_decision_id`: exact decision ID stored in the protected environment secret.

The workflow rejects other cohort IDs and N values. It checks the selected workflow branch HEAD separately from the checked-out model-source commit.

## Execution and stop behavior

- S6 scenario order is sequential: collection 085, 070, 050, 030; within each collection, recovery 100, 070, 050, 030, 000.
- For C085 and C070, lower-recovery scenarios use the same collection's G100 base artifact; the workflow waits for the base scenario to finish before proceeding.
- The first scenario failure stops the loop. No downstream aggregate runs after a scenario failure.
- A failure/cancellation trap attempts to write `EXECUTION_FAILURE.json`; artifact upload runs with `if: always()`.
- `cancel-in-progress: false` prevents a later dispatch from silently cancelling an active run.
- No automatic retry, previous-checkpoint resume, or partial-output promotion is permitted.
- Partial artifacts are diagnostic-only. A new run after failure requires a separate owner decision.
- C100 runs only after the S6 initial checkpoint succeeds. It is uploaded separately and is not consumed by the current S6 aggregator, which still records historical C100 reuse only.

## Output and retention

- S6 outputs: `execution-source/results_stage7_s6/`
- C100 outputs: new Golden, manifest, report, undefined-business-rule record, failure record if any, and `s4_evidence/`.
- The historical R4 report is deliberately excluded from C100 artifact upload.
- Actions artifacts are retained for 90 days. This is not durable external backup; archive them to independently verified Dropbox and OneDrive locations before relying on them for long-term evidence.
- No repository contents write, automatic commit, Release, or main-branch update is granted.

## Current status

`NOT_DISPATCHED`. The environment has not been configured/verified with required reviewers. No Trial, Simulation, Monte Carlo, or Golden generation has occurred through this workflow.
