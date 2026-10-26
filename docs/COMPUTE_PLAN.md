# Compute Plan — v2.3 / S5 → S6

## Scope and guardrails

- This document is a work-branch execution plan. It is not a production stability declaration or release acceptance.
- S5 validates worker equivalence and output schemas on the 20 non-C100 stochastic scenarios with trial IDs 1–5, running the same inputs sequentially and with 2 and 4 workers.
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

The workflow writes its actual outputs under `s5_evidence/`: worker-equivalence JSON, integer/Fraction-safe Parquet trial and selection tables, both daily-distribution policies, the five representative daily files per stochastic scenario with both partner reinvestment balances, number registry, mini-only diagnostic history, runtime benchmark, and SHA-256 manifest. The sample has N=5 and **cannot** establish a convergence checkpoint or scenario stability.

The S5 workflow fails closed on sequential/parallel mismatches, incomplete daily dates, missing representative roles, missing partner-balance integers, financial float leakage, cohort identity mismatch, or failure to validate reused C100 hashes.

## Measured S5 runtime

<!-- S5_RUNTIME_BEGIN -->
Pending actual S5 workflow execution. No runtime or throughput is inferred before measurement.
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
