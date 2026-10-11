# R4 — Increase Gate B N=1200 scenario concurrency without rerunning verified trials

Date: 2026-10-12  
Repository: `yasmin977209-ux/motorcycle-simulation`  
Main HEAD reviewed: `2325b6ae6e110d9e54e614aa9b1e255be5965375`  
Candidate CP-C workflow HEAD reviewed: `dae9cd6d5ba639ad2265a6d52a1b086a2c9dbe95`  
Normative source: `المرجع_النهائي_الموحد_المعتمد.md`, SHA-256 `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`.

## R4 three-way comparison

| Item | Current main | `stage3b-preserved` (diagnostic only) | Reference / approved decision / live evidence | Judgment |
|---|---|---|---|---|
| Stage and scope | `state.json` at main HEAD records Stage 12-CLOSED, N=600 only as `PASS_AT_N600_ONLY`, and authorizes the N=1200 checkpoint next. It explicitly says never rerun completed trial IDs. The N=1200 workflow is not yet part of main. | `state.json` is from Stage 9 and records legacy diagnostic evidence only. It is not a Stage 12 authority; no code is copied. | Current candidate is Run `38178068848`, branch `tmp/gateb-historical-1200-verify-20261012`, head `dae9cd6d5ba639ad2265a6d52a1b086a2c9dbe95`. It currently limits the 20-scenario matrix with `max-parallel: 10`. At review, 10 jobs were in progress and 10 were queued; no N=1200 scenario output artifact had yet been uploaded. | MATCH: changing the candidate workflow's concurrency cap remains within CP-C; no stage/CP transition is authorized. |
| Parallel execution and reproducibility | No matching N=1200 workflow exists on main. Main state requires source/sample identity and prevents rerunning completed trial IDs. | Diagnostic state notes a historic parallelism check, but does not define Stage 12 execution policy. No diagnostic code is used. | Reference §14.4 explicitly states serial execution and parallel execution with any number of workers must produce identical results when ordered by `trial_id`; scenario/trial identity is seed-independent of execution order. Acceptance test 127 requires exact serial/parallel equivalence. | MATCH: permit all 20 independent scenario jobs concurrently with `max-parallel: 20`; engine math, RNG, seeds, trial IDs, and the statistical criteria remain unchanged. |
| Dependency graph | Main has not yet accepted the N=1200 workflow. | Not authoritative. | The N=600 identity/hash proof must succeed before new trials; aggregation requires all scenario outputs. | MATCH: keep preflight → cumulative input verification → scenario jobs → aggregate dependencies. Do not run dependent jobs prematurely. |
| Completed outputs and resumption | State explicitly says completed trial IDs must not be rerun. | No authority. | The Stage 12 policy requires trial identities and result hashes to be retained and validated; past accepted artifacts remain read-only. | MATCH only if the new run restores and validates archived per-scenario outputs from the prior N=1200 run before executing missing IDs, and fails closed on conflicting or unverifiable duplicates. |
| Branch and workflow controls | No main change permitted directly; use a temporary branch and PR. | No workflow copied. | Project rules require a precisely pinned temporary branch, no wildcard trigger or `workflow_dispatch`, and `timeout-minutes` inside jobs. | MATCH: exact trigger pin to the new temporary branch, preserve in-job timeouts (10/20/30/15 minutes), and no self-dispatch. |

## Approved implementation constraints

1. Change only the independent scenario-matrix concurrency from 10 to 20. This makes all 20 scenario jobs eligible to start together; actual simultaneous runner capacity remains subject to the repository's GitHub Actions concurrency allowance.
2. The replacement workflow's preflight waits on the exact prior Run `38178068848` for at most 15 minutes (preflight job timeout 20 minutes), checking its fixed run ID, head SHA, branch and attempt each poll. No matrix job can start until that run completes. On timeout or identity mismatch, fail closed before running any scenario. Once complete, the workflow fetches that run's exact attempt-1 scenario artifacts; it validates run/head identity, artifact digest, per-row source SHA, source commit, seed, scenario/trial IDs, attempt and result SHA-256. It copies validated restored payloads into the new run's output artifacts, and executes only IDs whose prior output is absent and whose non-execution is verifiable. If a completed trial cannot be reconciled, stop rather than silently rerun it.
3. Keep source engine commit `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`, source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, master seed `20270101`, trial range 601..1200, and all statistical gates unchanged.
4. Keep the workflow on the temporary branch and open/update a PR. Do not merge until the final workflow run, artifact provenance, complete 24,000-key aggregation and all 60 CI-point calculations have been inspected. Gate A and Stage 9C/CP-D remain separate.
5. The preflight job timeout is raised from 10 to 20 minutes to bound the prior-run wait; all timeouts remain within jobs (20/20/30/15 minutes, each below the 35-minute risk threshold). This review authorizes a workflow scheduling/resumption change only; it does not mark the N=1200 checkpoint PASS or complete CP-C.

## Verdict

**MATCH**, with the safeguards above. No production file is changed by this R4 record itself.
