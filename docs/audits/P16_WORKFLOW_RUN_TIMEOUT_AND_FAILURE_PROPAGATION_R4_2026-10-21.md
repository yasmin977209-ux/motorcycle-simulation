# R4 — P16 360-minute retry and truthful build failure propagation — 2026-10-21

## Scope
Minimal review and repair of the selected P16 workflow after the two earlier 90-minute attempts were cancelled. No production simulation, Trial, checkpoint, source/data change, test change, main write, cancellation, or re-run of an existing run is authorized by this change.

## Evidence read before modification
- Repository: `yasmin977209-ux/motorcycle-simulation`.
- Main HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`; `main/state.json` continues to use `parent_state_commit_pointer`.
- Candidate branch: `tmp/p16-provisional-outputs-20261021`.
- Candidate SHA for the active 360-minute run: `7f7bd72bd5927e310685fc861cb542476b44e294`.
- Workflow blob at the inspected SHA: `0fb41cae348a9bcc57bf286697a01663c4e2815f`.
- Workflow already had `timeout-minutes: 360`, but also retained `continue-on-error: true` on the build step and included a documentation-only audit path in the `push.paths` trigger.
- A single read of Run `39523807220` showed status `in_progress`, build step `in_progress`, tests successful, and no artifact registered at that read. It uses the above candidate SHA and 360-minute workflow timeout.
- Runs `39516070267` and `39517048697` were read as `cancelled`; each had only a 90-minute timeout in the workflow definition loaded for that attempt. Their existing Artifacts contain evidence only, not the seven requested deliverables.
- Relevant failure evidence from previous attempts: build process was externally cancelled around the 90-minute mark; `build.log` was empty; the artifact upload completed, but final provenance registration was skipped.

## R4 classification
| Item | Current state | Governing evidence | Defect class | Minimal change | Authority | Acceptance |
|---|---|---|---|---|---|---|
| Build step error propagation | `continue-on-error: true` while finalization requires `steps.build.outcome == 'success'` | Current workflow blob; prior run steps/artifacts | `WORKFLOW_DEFECT` | Remove `continue-on-error: true` so a build failure fails the Job while `if: always()` still uploads evidence | User instruction: “قم بكلما يلزم واعد تشغيل افضلهما بمهلة 360 دقيقة”; bounded to the P16 candidate workflow, no main write | Read-back has no continue-on-error override; build failure propagates; evidence upload remains under `if: always()` |
| Audit document path in push filter | Documentation-only commits can trigger P16 build workflow | Current workflow blob and previously documented fan-out | `WORKFLOW_DEFECT` | Remove only `docs/audits/P16_PROVISIONAL_OUTPUTS_R4_2026-10-21.md` from `push.paths` | Same scoped authority | Documentation-only change no longer matches this workflow’s paths |
| Job timeout | Already set to 360 minutes | Current workflow blob, Run 39523807220 metadata | No change required | Keep `timeout-minutes: 360` unchanged | Explicit request | Read-back remains 360 |

## Boundaries and risks
- The active Run `39523807220` already loaded its workflow definition. Editing YAML cannot change its loaded `continue-on-error` behavior or timeout, and this repair must not cancel or replace it.
- Do not start a second build while Run `39523807220` is active. No further polling of that run is part of this CP.
- The alternate old P16 SHA `5f783dd1c56b6718e82168bd7617e39d91280100` is not used as the base for a new build.
- The code change is limited to the candidate workflow; `main`, tests, source files, trial data, parquet, manifests, seeds, and cohorts remain unchanged.
- A commit tagged `[skip ci]` prevents the workflow-file repair commit from launching another build. Read-back verification must confirm the changed file and that no additional run was created by this commit.

## Status before change
`R4_REVIEWED; P16 RUN 39523807220 ALREADY IN_PROGRESS AT 360 MINUTES; WORKFLOW EDIT NOT YET APPLIED`.
