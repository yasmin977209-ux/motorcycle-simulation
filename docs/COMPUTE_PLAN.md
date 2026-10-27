# Compute Plan — v2.3 / S5 → S6

## Scope and guardrails

- This document is a work-branch execution plan. It is not a production stability declaration or release acceptance.
- S5 validates worker equivalence and output schemas on the 20 non-C100 stochastic scenarios with trial IDs 1–50, running the same inputs sequentially and with 2 and 4 workers.
- New-cohort identity is bound to the exact tested commit SHA and a separate S5 cohort ID. The historical C030_G030 N=300→600 P90_Final_Cash failure remains unchanged and is never merged into the S5 cohort.
- C100 is a separate deterministic cohort and is reused read-only from S4. Do not rerun it as part of S5/S6.

## Reused C100 evidence

- GitHub Actions Run: [40263424595](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40263424595)
- Cohort: `c100-v23-s4-20261026-965281d5`
- Golden: `docs/golden/v2.3/C100_GOLDEN_965281d52441cd0d4b744e211c9f68ee4cdc3753.json`
- Golden SHA-256: `39950d91c3b40b11bea0997b8504ac932a57bcc0ef8e0c51e12d031342a53327`
- Manifest SHA-256: `2097284d77ead6b00492bf75830d09aeef8dbde4aaa1c15dae6a877dc7e9ff04`
- C100 results are reused as a distinct deterministic cohort; they are not counted as stochastic trials, and their source/cohort identifiers remain intact.

## S5 evidence contract

The workflow writes its actual outputs under `s5_evidence/`: worker-equivalence JSON, integer/Fraction-safe Parquet trial and selection tables, both daily-distribution policies, the five representative daily files per stochastic scenario with both partner reinvestment balances, number registry, mini-only diagnostic history, runtime benchmark, and SHA-256 manifest. The sample has N=50 and **cannot** establish a convergence checkpoint or scenario stability.

The S5 workflow fails closed on sequential/parallel mismatches, incomplete daily dates, missing representative roles, missing partner-balance integers, financial float leakage, cohort identity mismatch, or failure to validate reused C100 hashes.

## Measured S5 runtime

<!-- S5_RUNTIME_BEGIN -->
Actual workflow Run: 40440814682 (attempt 1); tested source SHA: 7a3cd8208f79157b8ad04b7ab77891f555b710b2.
Measured S5-B workload: 3000 executions, 1000 unique stochastic scenario/trial paths, 20 non-C100 scenarios, N=50 trials each.
- Sequential total: 4684.856597 s; throughput: 0.021345 unique scenario/trial paths/s.
- Parallel 2 workers total: 2481.158059 s; throughput: 0.040304 unique scenario/trial paths/s; speed-up: 1.888173x.
- Parallel 4 workers total: 2155.170253 s; throughput: 0.046400 unique scenario/trial paths/s; speed-up: 2.173776x.
- Total measured script elapsed: 10006.227717 s.
- Full repository tests: 567 passed, 1 skipped, 0 failed, 0 errors (command exit code 0).
S6 extrapolations remain unmeasured linear projections from this N=50 validation cohort; no production checkpoint or stability claim is inferred.
C100 was hash-verified and reused read-only from S4 Run 40263424595; neither C100 nor Test 192's coverage simulation was rerun in S5-B.
<!-- S5_RUNTIME_END -->

## S6 launch recommendation

1. Launch only on a work branch. Reuse the existing C100 Golden and manifest; do not spend compute re-running deterministic C100.
2. Before generating the 20 stochastic scenarios at N=300, use the S5 benchmark to choose worker count and batch size. Select the worker count with verified bit-for-bit equivalence and the best measured end-to-end throughput, not CPU count alone.
3. Persist one cohort per exact `SOURCE_SHA`, master seed, schema, and trial-ID range. Keep C030_G030 historical transition artifacts immutable; record all new checkpoint points separately.
4. At each approved checkpoint N=300, 600, 1200, 2400… compute the three financial means and seven indicators using the approved `alpha_s,k = 0.0025/[k(k+1)]` spending rule, with checks at N and N/2; enforce the exact P50 cross-multiplication guard and the required three consecutive adjacent successful transitions across four cumulative checkpoints.
5. Keep C100 determinism, Gate A exact identity, Gate B inference, scenario convergence and delivery acceptance as separate decisions. S5 mini output is diagnostic plumbing/equivalence evidence only.
6. Use the S5 measured runtime to stage checkpoint jobs and persist block-level manifests; avoid claiming a completion date until the actual production checkpoint runs have measured times and verified artifacts.

## Known unresolved acceptance boundaries

- No S5 mini run may set `SCENARIO_STABLE`.
- P90 held-assets production identity/completeness must be verified on production checkpoint data.
- Existing historical C030_G030 failure is retained; the S5 cohort must use its own source SHA, cohort ID, manifests and stability history.
- Excel/report reconciliation and delivery archive checks remain in their proper later phases; an S5 number registry is not by itself evidence that later workbooks/reports reconcile.

<!-- S5_OPT1_BEGIN -->
## S5-C — Owner-approved OPT-1 evidence

- Evidence Run: 40440814682; tested source SHA: 7a3cd8208f79157b8ad04b7ab77891f555b710b2. This section is recorded only after S5-B and the full test inventory passed.
- Accepted Test 192 proof reused without rerunning its simulation: SHA-256 f6add77e9e7ff8256b36b661df337897de10cd96d7e00b0d9dfa660dea0e927b; S5-A Run 40397897155.
- C100: OPT1_REUSED_ACCEPTED_C100_S4_EVIDENCE, S4 Run 40263424595, Golden SHA-256 39950d91c3b40b11bea0997b8504ac932a57bcc0ef8e0c51e12d031342a53327; no C100 rerun.

| Collection level | OPT-1 status | Eligible zero-claim trials | Full independent G runs verified |
|---|---|---:|---|
| C100 | OPT1_REUSED_ACCEPTED_C100_S4_EVIDENCE | reused S4 evidence | No (reused S4) |
| C085 | OPT1_ENABLED_VERIFIED_FOR_ELIGIBLE_TRIALS | 50 | Yes: G100/G070/G050/G030/G000 |
| C070 | OPT1_ENABLED_VERIFIED_FOR_ELIGIBLE_TRIALS | 50 | Yes: G100/G070/G050/G030/G000 |
| C050 | OPT1_INELIGIBLE_FULL_RUN_REQUIRED | 0 | Yes: G100/G070/G050/G030/G000 |
| C030 | OPT1_INELIGIBLE_FULL_RUN_REQUIRED | 0 | Yes: G100/G070/G050/G030/G000 |

For any level with claims_created == 0, the S5-B sample compared the financial trial_fingerprint and each daily row against all four lower-G candidates before marking the trial eligible for DERIVED_FROM=Cxxx_G100. Positive-claim trials remain full-run-only. If no sampled trial is claim-free, the level is recorded as OPT1_INELIGIBLE_FULL_RUN_REQUIRED and all five G scenarios must complete independently; the program does not raise an eligibility RuntimeError.

### Required S5-B artifact SHA-256

- results_stage5/worker_equivalence_manifest.json: dd941cfefcf6f86e2417f7bdbe71835853184ad640e419cdb18e4d094e79445d
- results_stage5/trials_summary.parquet: 8b7edf562a103d3f0ed54d8e9511fa55845d53bad93996ca9120d89773a40c13
- results_stage5/daily_distribution.parquet: ad7884055396eb85b20e1e0f42d17e0cb531f3f244298d643b86bf2d8c94a18f
- results_stage5/opt1_sample_validation.json: 8e593cbe8712c6439aeb96971edaf5e7c382ccb16ae24dba71ad66e07103be05
- results_stage5/s5_manifest.json: 13e7d3c64fdb803a30e3ff99d8fa708dde904807668d85b9ec858f94836388bb

- Test inventory: 567 passed, 1 skipped, 1 warning in 510.51s (0:08:30)
- Scope limitation: this closes only S5-B/S5-C execution/equivalence evidence. It does not declare Gate A or Gate B production acceptance, convergence, or final delivery acceptance.
<!-- S5_OPT1_END -->
