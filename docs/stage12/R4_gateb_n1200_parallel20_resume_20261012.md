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


## Addendum — cancelled prior-run evidence and fail-closed recovery (2026-10-12)

The subsequent live workflow evidence clarified that Run \`38178068848\` ended with \`status=completed\`, \`conclusion=cancelled\`, while retaining ten per-scenario attempt-1 artifacts. For those ten scenarios, the simulation/materialization step was started and cancelled, and each has its matching artifact. The other ten matrix jobs have no runner and no steps, and no scenario output artifact. The artifacts are partial; they do not establish N=1200 completion.

Replacement Run \`38179110800\` passed its audit unit tests (9 passed) but failed before simulation with the exact blocker \`PRIOR_N1200_RUN_NOT_SAFELY_COMPLETED run=38178068848 status=completed conclusion=cancelled\`. This is a \`WORKFLOW_DEFECT\`: the preflight rejected the terminal state before reaching the per-job/artifact safeguards; it is not an engine failure and not a reason to change a test to fit engine behavior.

### Corrective constraint

Accept \`cancelled\` only as a terminal state for this exact pinned Run/head/branch/attempt so that the existing evidence audit can run. Do **not** interpret cancellation as proof that a trial did not run. Preserve the checks that require exactly one completed matrix job per scenario, fail with \`PRIOR_N1200_OUTPUT_ARTIFACT_MISSING_AFTER_TRIAL_STEP\` whenever a materialization step ran without a matching artifact, and validate artifact archive digests plus every restored payload's scenario/trial ID, source SHA/commit, seed, origin, attempt, and result SHA before reuse. Re-materialize only validated payloads and compute only trial IDs absent from verified prior artifacts. If any output is unaccounted for, stop without silently rerunning it.

The engine, RNG, master seed, sample ranges, statistical policy, parallel matrix, and branch pin are unchanged. Added tests cover the terminal cancellation case and prove the fail-closed missing-artifact path. The R4 scheduling/resumption judgment remains **MATCH with these controls**; this addendum does not mark Gate B or CP-C as passed.


## Addendum — Gate B P50 change rule and cumulative checkpoint decision (2026-10-12)

### R4 three-way comparison

| Item | Current main before this decision | `stage3b-preserved` (diagnostic only) | Reference / current approved policy / live evidence | Judgment |
|---|---|---|---|---|
| P50 threshold wording | D-2026-10-10-01 specifies a P50 change (>5%) between N=300/600/1200 but omits the exact denominator/formula. | Its `state.json` is a legacy Stage 9 diagnostic state. It is not Stage 12 statistical-policy authority and no code is copied. | The reference §2.5 defines the existing relative-change pattern using the prior value as denominator and `REFERENCE_EPSILON=1e-6`; for near-zero prior values it uses an absolute one-unit test. Amendment-01 fixes the separate Gate B threshold at (>5%) but leaves this formula omitted. | MATCH: D-2026-10-12-01 preserves the approved (5.0%) trigger, makes the previous-checkpoint denominator explicit and reuses the reference's already-defined near-zero pattern. |
| Metric and checkpoint adjacency | The N=1200 report exposes P50 `Final_Net_Project_Equity` at N=300/600/1200 but marks the formula decision undefined. | No authority for this Gate B decision. | The report was generated from cumulative IDs 1..300, 1..600 and 1..1200 for each of the 20 non-C100 scenarios. The defined calculation evaluates 300→600 and 600→1200 separately. | MATCH: no trial outputs or IDs are changed; only the missing decision formula is applied analytically. |
| Escalation and scope | CP-C's N=1200 report says `PASS_AT_N1200_ONLY`; it cannot, on its own, establish combined Gate B or final project acceptance. | Not applicable/authoritative. | Runs 38162171123, 38174743440 and 38179919488 each report 60/60 CI points passed, with 0 failed and 0 undefined. The N=1200 report archive SHA-256 matches GitHub's published digest. Read-only recomputation across 40 P50 comparisons finds no (>5.0%) transition. | MATCH: combined N=300/N=600/N=1200 Gate B statistical checkpoint evidence is accepted; no P50-triggered N=2400. Final project stability remains blocked on separate Gate A and Stage 9C/CP-D. |

### Decision and evidence identities

- Normative decision: `D-2026-10-12-01` in `docs/governance/DECISIONS_LOG.md`.
- Reference SHA-256: `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`.
- Engine source SHA / commit: `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b` / `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`; master seed `20270101`.
- N=300: Run `38162171123`, HEAD `4d979ff4de178ed07c81ef26a0707c14e1de15ee`, report artifact `11711110209`, ZIP SHA-256 `3800e6788de7e57940e03fb94968961eb6dc6621ffaf3da14d276b9d6d51ba22`; 60/60 CI PASS.
- N=600: Run `38174743440`, HEAD `61ae9e2354ff37b1d4d9d13849bd6b264cf9cfa3`, report artifact `11715388165`, ZIP SHA-256 `67d5033a67eec27bd7a90b735c56f7f7ceff4181e32c88271dd07f39f3b8e8ae`; 60/60 CI PASS; ordered map SHA-256 `dd537fe96c5a8736201441e9a620db148a0d16cadae518d2a777fbc723db395f`.
- N=1200: Run `38179919488`, HEAD `54822f2737fc8e474239598ea15d47ae0f55cb4e`, report artifact `11717929259`, ZIP SHA-256 `17391caa64a7ed0fb7f3819a5df2f3b69bee982fb16060f3c542c84370bee7c0`; 24,000/24,000 scenario/trial keys, 12,000 new trial outputs verified, 60/60 CI PASS; ordered map SHA-256 `eaf1f8f3060aac6967b064d3199c082d2a9b47027c865628986f56cbb23c1fc3`.
- P50 re-evaluation: exactly 40 comparisons, all previous P50 values are outside the near-zero fallback; maximum (300→600) change is 0.348341% (`C050_G000`), maximum (600→1200) change is 0.191901% (`C050_G000`), and escalation-required scenarios = 0.

### Per-scenario audit table

All monetary values and percent changes below are copied/derived from the preserved N=1200 report; the report artifact itself is immutable.

| Scenario | P50 @300 | P50 @600 | P50 @1200 | Change 300→600 | Change 600→1200 |
|---|---:|---:|---:|---:|---:|
| C030_G000 | 24,985,675 | 25,001,825 | 25,031,575 | 0.064637% | 0.118991% |
| C030_G030 | 37,194,150 | 37,178,175 | 37,154,150 | 0.042950% | 0.064621% |
| C030_G050 | 47,986,575 | 47,949,675 | 48,010,025 | 0.076897% | 0.125861% |
| C030_G070 | 61,657,150 | 61,563,775 | 61,645,450 | 0.151442% | 0.132667% |
| C030_G100 | 88,899,175 | 88,911,625 | 88,856,150 | 0.014005% | 0.062393% |
| C050_G000 | 277,594,350 | 276,627,375 | 277,158,225 | 0.348341% | 0.191901% |
| C050_G030 | 288,761,300 | 288,421,100 | 288,347,725 | 0.117814% | 0.025440% |
| C050_G050 | 295,901,825 | 296,516,875 | 296,625,700 | 0.207856% | 0.036701% |
| C050_G070 | 303,879,900 | 303,909,975 | 303,967,950 | 0.009897% | 0.019076% |
| C050_G100 | 316,668,550 | 315,924,000 | 315,905,250 | 0.235120% | 0.005935% |
| C070_G000 | 209,131,500 | 209,128,750 | 209,129,500 | 0.001315% | 0.000359% |
| C070_G030 | 209,128,500 | 209,128,250 | 209,123,750 | 0.000120% | 0.002152% |
| C070_G050 | 209,127,250 | 209,125,000 | 209,125,000 | 0.001076% | 0.000000% |
| C070_G070 | 209,122,000 | 209,127,750 | 209,128,500 | 0.002750% | 0.000359% |
| C070_G100 | 209,132,500 | 209,127,000 | 209,127,750 | 0.002630% | 0.000359% |
| C085_G000 | 209,810,000 | 209,812,500 | 209,813,500 | 0.001192% | 0.000477% |
| C085_G030 | 209,818,250 | 209,815,500 | 209,814,000 | 0.001311% | 0.000715% |
| C085_G050 | 209,813,000 | 209,812,500 | 209,813,500 | 0.000238% | 0.000477% |
| C085_G070 | 209,813,250 | 209,812,000 | 209,813,000 | 0.000596% | 0.000477% |
| C085_G100 | 209,813,750 | 209,812,500 | 209,813,500 | 0.000596% | 0.000477% |

### Disposition and limitations

- Statistical Gate B checkpoint criteria: `PASS_AT_N300_N600_N1200` across the three preserved reports plus the newly specified P50 condition.
- P50-specific N=2400 trigger: `NOT_TRIGGERED`. No N=2400 run was started.
- No trial was rerun during this P50 reassessment; historical datasets and metadata were not modified.
- This result does **not** establish overall project PASS or final stability. Gate A (PR #30) and Stage 9C/CP-D (PR #29) remain independent, unaccepted gates. Do not move to either CP in this commit.
- The N=1200 report remains an immutable historical artifact whose generated text said the formula was undefined at creation time; this addendum records the subsequent delegated normative decision and reproducible read-only reevaluation rather than altering that artifact.
- R4 verdict: **MATCH**. No engine, RNG, seed, trial IDs, CI criterion, workflow, tests or simulation outputs were changed by this policy reassessment.
