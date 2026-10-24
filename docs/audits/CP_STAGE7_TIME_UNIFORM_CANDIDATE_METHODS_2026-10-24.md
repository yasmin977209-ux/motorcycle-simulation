# Stage 7 statistical candidate methods — 2026-10-24

## Verified policy source

The normative checkpoint schedule is Decision D-2026-10-10-01 in `docs/governance/DECISIONS_LOG.md`: non-C100 execution starts at N=300 and uses doubling checkpoints 300, 600, 1200, 2400, 4800, 9600, … without a fixed cap. The retained `ITERATION_ESCALATION_STEP=50` and `STATISTICAL_CHECK_STEP_N=50` constants are historical compatibility values only. This change centralizes the active multiplier in `constants.STATISTICAL_ESCALATION_MULTIPLIER` while keeping old values readable for legacy metadata.

The approved familywise framework is an intersection-union test (IUT), with 20 stochastic scenarios and per-scenario alpha 0.0025. Every required component must pass; component procedures must be valid under adaptive looks. Three successful adjacent transitions require four cumulative points.

## Candidate implementation added (not connected to production)

- `ORDER_STATISTIC_ALPHA_SPENDING_GRID_V1`: exact distribution-free fixed-quantile order-statistic intervals at approved checkpoints. At look j, it spends alpha_j = alpha/[j(j+1)], whose infinite sum is alpha. It assumes an identity-verified complete prefix of independent trial outcomes. Non-finite observations, an incomplete prefix, unsupported N, missing finite endpoints, or a margin miss fail closed.
- `BETA_BINOMIAL_MIXTURE_CS_V1`: inverts the beta-binomial mixture likelihood-ratio martingale for a Bernoulli probability. Ville's inequality gives time-uniform coverage across all sample sizes for a fixed alpha. The Beta(a,b) distribution is the test-martingale mixture, not an assumption about the unknown probability.
- Precision helpers apply strict thresholds: quantile interval radius must be below the configured metric margin; Bernoulli half-width must be below 0.005; adjacent probability estimate change must be below 0.005.

## Explicit limits

These helpers are candidate components only. They are not wired into `run_batch.py`, do not validate source identity or full trial-ID coverage, and do not prove the P90_Held_Assets source/completeness path. They do not solve K_SPEC for the three financial means: current pointwise Student-t intervals remain non-time-uniform under adaptive stopping and there is no approved finite support or quantified tail/moment bound. The historical C030_G030 P90_Final_Cash transition N=300→600 remains failed and unqualified. The four-point/three-transition and historical failed-transition path still need exact integration tests against the production decision path.

Accordingly, `docs/stage7/statistical_execution_gate.json` remains `BLOCKED_FOR_IMPLEMENTATION`; no production Trial, checkpoint, Monte Carlo run, Golden extension, workbook, or final acceptance is authorized by this candidate.

## Verification plan

The branch workflow runs Stage 1 contract tests, Stage 7 authoring contracts, Gate B unit tests, and the candidate-method unit tests, then parses the workflows. Its tests do not launch production simulation batches.


## Gate contract component-status reconciliation — 2026-10-24

Exact-main source review and the candidate workflow passed the tests listed above. The gate contract's previous `stopping_window` field said the code used only three points/two transitions, but `run_batch.py` calls the current helper with required values 3 transitions and 4 cumulative points, and dedicated tests reject a three-point history and malformed checkpoint binding. The previous `gate_b_implementation_guards` record likewise repeated two stale blockers: Gate B now rejects non-Boolean `stable` values, and `_metric_summary` implements the approved near-zero absolute epsilon branch. The JSON component statuses are updated to match those facts.

This reconciliation is deliberately narrow: K_SPEC remains blocked; quantile and Bernoulli candidate methods remain unintegrated; P90_Held_Assets source/completeness remains unaccepted; historical C030_G030 P90_Final_Cash transition remains failed; overall status stays `BLOCKED_FOR_IMPLEMENTATION`; all production execution authorizations remain false. This is evidence normalization, not statistical acceptance.
