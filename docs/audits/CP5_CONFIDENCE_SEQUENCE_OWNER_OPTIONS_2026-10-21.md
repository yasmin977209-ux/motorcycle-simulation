# CP5 — Confidence Sequences (CS): owner decision options — 2026-10-21

**Status:** `PENDING_APPROVAL` — proposal only; no CS implementation authorized or performed  
**Branch:** `tmp/cp-path5-cs-options-20261021`  
**Base/main HEAD re-read for this session:** `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`  
**Original governing reference SHA-256:** `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479` (the uploaded original reference's bytes were rehashed and matched)  
**Decision scope:** the three items below only. This proposal does not amend the business reference, existing Gate A/B acceptance rules, source identity, sample/cohort, or completed historical evidence.

## Executive recommendation

Keep formal Confidence Sequences blocked until the owner records all three decisions below. Do not infer distributional support from observed samples, reuse the existing financial-mean threshold as a loss-probability tolerance, or silently interpret `alpha_s` as either an IUT level or a multiplicity allocation. Once decisions are explicit, draft a separate versioned statistical contract and R4; only then consider an implementation proposal.

## Decision 1 — support/moment assumptions for financial means

The target is a time-uniform statement about the mean of a financial outcome. A valid CS construction depends on assumptions about the outcome distribution or increments; empirical trial values by themselves do not prove a known finite support or tail condition.

| Option | Proposed assumption contract | Evidence required before implementation | Trade-off |
|---|---|---|---|
| **1A — proven bounded support** | For each covered scenario/metric, the owner identifies a deterministic lower and upper bound `[L_s,k, U_s,k]` that every value must satisfy. The CS method and constants are chosen for this declared bounded outcome/increment model. | An authoritative model invariant or governing rule proving the bounds across all admissible paths, including closure/termination outcomes; a schema/range audit; tests of fail-closed handling outside the bounds. Observed min/max alone is insufficient. | Transparent assumptions, but invalid if a bound is merely estimated from the existing sample. |
| **1B — explicit tail/moment condition** | The owner identifies a precise condition supported by the stochastic model (for example a known sub-Gaussian/sub-gamma proxy or another theorem-specific moment bound), and the CS method is derived for that exact condition. | A derivation tied to the model, justified constants/parameters, units and metric scaling, assumptions on dependence/adaptivity, plus coverage-oriented synthetic tests. Do not estimate a supposedly “known” constant solely from the same small sample without an approved method. | Potentially less conservative than a crude bound, but requires stronger mathematical and provenance evidence. |
| **1C — defer CS** | Do not claim a time-uniform finite-sample guarantee for financial means yet. Preserve current status and report the descriptive estimates/approved legacy gate separately. | No additional assumptions invented. Revisit after a governing support/moment contract and evidence exist. | Safest while the true tail/support structure is unknown; does not falsely promote empirical stability to a CS guarantee. |

**Recommendation:** 1C until 1A or 1B is established from authoritative constraints or an explicitly approved probabilistic model. The 24-month horizon does not, by itself, prove that all financial outcomes have a known bounded support.

**Owner must specify:** selected option; covered metric set; per-scenario or global scope; any `L/U` or moment/tail parameters and their source; whether assumptions are deterministic invariants or stochastic conditions; treatment of invalid/out-of-range values.

## Decision 2 — loss-probability precision gate

Let `p_s = P(loss event in scenario s)`, using the exact already-governed loss-event definition. This decision selects a precision/decision gate; it does not redefine what constitutes a loss.

| Option | Proposed gate | Owner inputs still required | Trade-off |
|---|---|---|---|
| **2A — absolute precision target** | Require a predeclared absolute confidence-sequence half-width no greater than `epsilon_loss` for each required scenario. Define the confidence level, stopping behavior and handling of a boundary case in advance. | Numerical `epsilon_loss` in probability units, global confidence level, covered scenarios, and whether width alone or width plus a decision threshold is required. | Directly interpretable even when `p_s` is near zero; the numerical tolerance must not be guessed. |
| **2B — decision-boundary gate** | The owner defines a risk boundary `p_max,s` and a one-sided CS decision rule (for example, a scenario is acceptable only when the upper bound is below the boundary); precision/stopping requirements are stated separately so “not enough evidence” is not reported as acceptance. | Numerical boundary per scope, confidence level, strict/non-strict comparison, precision/stopping rule, and explicit handling of an interval that straddles the boundary. | Aligns with a risk decision, but requires an authoritative loss-risk tolerance and must distinguish “failed” from “not yet established.” |
| **2C — leave blocked** | Do not introduce a formal loss-probability precision gate; keep the relevant status `PENDING_APPROVAL` / `NOT_ACCEPTED` and do not claim a CS pass. | Owner can define the loss precision or decision boundary later. | Avoids fabricating risk appetite or statistical acceptance criteria. |

**Recommendation:** 2C until a numerical risk tolerance is supplied. If the owner prefers a precision-only contract, 2A is the clearest starting point; if acceptance is meant to answer “is loss risk below an approved maximum?”, 2B fits that question better.

**Explicit non-equivalence:** the current Gate B rule for financial metrics is a 95% Student-t CI half-width below 1% of the absolute mean at its specific checkpoint scope. It is not an approved `epsilon_loss`, loss-risk boundary, or time-uniform CS rule. It must not be copied over to this metric by inference.

## Decision 3 — meaning of `alpha_s` and IUT

The owner must decide what claim the project intends to support. An intersection-union test (IUT) for a conjunctive claim and a family-wise simultaneous-confidence requirement are different statistical contracts; the code should not choose between them implicitly.

| Option | Intended interpretation | Acceptance/error-control consequence | Trade-off |
|---|---|---|---|
| **3A — conjunctive IUT** | The single global claim is “all required conditions in all required scenarios pass.” Every component condition must pass; any failed or undefined component blocks the global claim. Use a common predeclared component level `alpha` only if the owner confirms this exact IUT interpretation and the statistical derivation fits the tests. | For a genuine intersection-union test, a conjunctive rejection rule can control the global test size at the component level without automatically splitting alpha. This does **not** by itself establish simultaneous time-uniform coverage for every displayed CS; that coverage construction must be justified separately. | Matches an all-scenarios-must-pass gate, but the claim and per-component construction must be documented carefully. |
| **3B — global family-wise simultaneous guarantee** | The owner wants the stated coverage/error guarantee to hold jointly across every scenario, metric/component, and required time horizon. | Predeclare a global `alpha_global` and a valid joint CS or a documented allocation `alpha_s,k` with a justified aggregate bound (for example, a declared sum constraint). An allocation rule may not be improvised from the number of tests after seeing results. | Clearer if simultaneous coverage of every scenario interval is the goal; potentially more conservative. |
| **3C — defer formal interpretation** | No CS or IUT code until the intended claim is settled. Preserve current legacy checks and distinguish them from formal CS evidence. | `PENDING_APPROVAL`; no test/threshold is upgraded and no `alpha_s` behavior is assumed. | Safest while claim semantics are not explicit. |

**Recommendation:** 3C now. If the intended business assertion truly is only a single conjunction (“all required gates pass or the overall gate does not pass”), review 3A with a documented theorem and keep the separate simultaneous-coverage question explicit. Choose 3B only if joint coverage/error control across the full family is the intended guarantee.

**Owner must specify:** meaning and numeric value of global `alpha`; whether `alpha_s` is a scenario-level budget, a component test level, or another quantity; exact null/alternative and global pass rule; whether the guarantee is IUT size control, simultaneous CS coverage, or both; any allocation rule and its predeclared scope.

## Decision record template

Please record three separate owner decisions in the authoritative decision log before any implementation:

1. **Financial-mean assumptions:** `1A / 1B / 1C` plus the exact metric scope and source of any bound/proxy.
2. **Loss-probability gate:** `2A / 2B / 2C` plus required numerical values and the loss-event definition reference.
3. **Alpha/IUT semantics:** `3A / 3B / 3C` plus confidence/error guarantee, numeric alpha, component/scenario scope, and decision rule.

If any item remains ambiguous, leave that item `PENDING_APPROVAL` and do not implement CS. The recommended choices above are proposals, not owner decisions.

## Implementation guardrails

- No CS implementation, experiments, production trials/checkpoints, source/seed/RNG/cohort changes, or updates to existing results were performed as part of this report.
- No acceptance or release is implied.
- After explicit owner decisions: record a versioned statistical contract, complete R4 for the proposed implementation, establish testable synthetic coverage requirements, and independently review the derivation and code before any claim of statistical acceptance.
