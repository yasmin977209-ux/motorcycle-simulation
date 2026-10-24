# Stage 7 finite-support and termination-bound review — 2026-10-24

## Scope and result

This is a static/source and synthetic-state audit on main SHA 6e108209c75a2705c9ba4d669578b6f472d74a4f, after PR #69 merged. It does not execute a canonical Monte Carlo batch, alter RNG/model equations, rerun historical trials, or change any production authorization.

**Result: K_SPEC remains blocked.** The current source does not establish a deterministic maximum termination horizon or a quantitative tail/moment bound for final financial outputs. The review finds a conditional stuck-state path involving an unfunded PREP bike. It does **not** claim to have proved that this synthetic state is reachable from the canonical create_initial_project() trajectory; reachability (or a proof of unreachability) is itself still open.

## Source evidence

1. **constants.py:** FINAL_CLOSE_DATE = None; the normative expansion cutoff is 2030-12-31; SECONDARY_CONTRACT_DURATION = None (open-ended).
2. **daily_engine.py::run_deterministic_trial:** while not project.simulation_stopped has no max_days/date-limit guard.
3. **daily_engine.py::_m2:** preparation costs are paid only when both project_cash and partner1_reinvestment_balance meet each threshold. Prep oil/lubricant is paid at PREP_OPERATING_EXPENSE_PER_BIKE; customs/registration is paid at CUSTOMS_AND_REGISTRATION_COST. actual_ready_date is assigned only after both prep_paid and customs_paid become true. The expansion loop is suppressed while any PREP bike remains underfunded, but that is not a timeout or recovery transition.
4. **closure.py::closure_preconditions_met:** closure requires no PREP bike, no active primary-state bike, no active post-maturity settlement, and a date after the expansion cutoff. Thus a PREP that never reaches funded/ready status blocks dynamic closure.
5. **daily_engine.py::_m11 and _m3:** a failed secondary contract can move to AVAILABLE_FOR_SECONDARY, from which a new open-ended secondary contract starts; the existence of a PREP bike is what keeps global closure from occurring.
6. **daily_engine.py::_cash_out** subtracts the requested amount without a non-negative-cash guard. Therefore the code does not itself impose a finite lower bound on accumulated cash/expense over an arbitrarily long run.

## Synthetic adversarial probe

tests/test_stage7_finite_support_review.py constructs a project with one expansion-sourced PREP bike, zero project cash, zero Partner 1 reinvestment balance, no active contract/income source and no funding completion date. It calls only the deterministic _m2 funding transition for a finite list of post-cutoff dates. The test checks that (a) neither cost flag changes, (b) actual_ready_date remains unset, and (c) the dynamic-closure preconditions remain false. This is **not** a production run and not evidence that canonical initialization can reach this exact state.

The same test file pins the current architecture fact that the runner has no max-days parameter/guard and FINAL_CLOSE_DATE remains None. These are source assertions, not a mathematical proof of distributional reachability.

## Why the mean-confidence-sequence question remains open

A finite support assumption cannot be asserted merely from the presence of finite contractual thresholds: underfunded PREP delays are coupled to cash and reinvestment inflows, and the source contains no hard final-close date or global timeout. A tail/moment argument would need, at minimum, a reviewed statement of the stochastic interpretation of the SHA-derived event draws (the implementation deterministically hashes master_seed | scenario | trial_id | bike_id | day | event_type) and a proved quantitative bound on the stopping/funding process and per-day financial increments. The deterministic hash implementation is not, by itself, a proof that event draws are independent Bernoulli variables.

No numerical tail constant or independence assumption is invented in this CP. Owner delegation authorizes work but does not supply these missing mathematical premises. Candidate quantile and Bernoulli procedures remain unintegrated, financial-mean K_SPEC is unchanged, and docs/stage7/statistical_execution_gate.json stays BLOCKED_FOR_IMPLEMENTATION.

## Next valid paths

- **Path A — prove reachability/termination:** establish, with code-level invariants or an exhaustive model proof, that canonical initialized projects cannot enter a non-progressing underfunded-PREP state and that the stopping horizon/financial output has the required support or tail property.
- **Path B — reviewed stochastic contract:** explicitly specify/approve the event-dependence model, quantify the tail/moment bound for stopping time and financial increments, and validate a confidence sequence that is valid under that model and the adaptive checkpoint schedule.

Do not change the reference's dynamic-close semantics to an arbitrary fixed date as a shortcut. Do not open the statistical execution gate until the chosen path has proof, independent review, exact-source tests, and an explicit reviewed implementation-approval record.

## Exact-main verification evidence

At SHA 6e108209c75a2705c9ba4d669578b6f472d74a4f, the following independent workflows succeeded:
- Stage 1: [Run 40108022784](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40108022784)
- Stage 2: [Run 40108022745](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40108022745)
- Stage 3A: [Run 40108022830](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40108022830)
- Stage 3B: [Run 40108022912](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40108022912)
- Stage 5 round-3 validation: [Run 40108022892](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40108022892)

PR #69 candidate-method checks passed on exact candidate head 30b66687105355cdacd980a3b8e9c59f6641c78e, and current-main Stage 1/2/3A/3B/5 runs above all target the exact merged main SHA. These are regression/validation checks, not statistical acceptance or final-delivery acceptance.

## Safety boundary

No production Stage 7 full-run, adaptive checkpoint, Monte Carlo cohort, Golden expansion, Stage 12 materialization, MaxCase replay, workbook acceptance, or release was dispatched by this review. No historical data or model-source file was modified. All production execution and final-acceptance authorization flags remain false.
