# Statistical policy and execution-topology reconciliation — R4 (2026-10-24)

**Scope:** documentary reconciliation only. This note does not dispatch any workflow, run a trial/checkpoint, mutate a canonical dataset, alter a manifest, or approve a final delivery.

## 1. Governing references and cohort boundary

The five supplied reference bodies have been inspected alongside the repository decision log and the conflict map. The source-file hashes recorded for this review are:

| Reference | SHA-256 |
|---|---|
| `المرجع_النهائي_الموحد_المعتمد.md` | `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479` |
| `المرجع_النهائي_الموحد_المعتمد_v1.1.md` | `d57341f64dd9050b02571e0d54b1111305ba5d5d23a2981afe9674a95b9f4cbc` |
| `المرجع_النهائي_الموحد_المعتمد_v2.0.md` | `9ecece31a5397ebb5e3478c728c407b757bee7cbc11a7e87676254981312cab6` |
| `المرجع النهائي الموحد المعتمد المدمج.md` | `c816e2b61734390e57500cab738829ae1810d0063f9b49bdf0d107344f867fd5` |
| `المرجع_النهائي_الموحد_v.md` | `03e2f070d51f6bfec297f4196a3579b42bd68577425e0caae632bb6c65bd8146` |
| Conflict map: `prompt_merge_map_conflicts.md` | `48209338125400861ab297d36c776feffd55d381ca7ca7c3d402c8763511b53b` |

Do not collapse three distinct scopes into one count or identity:
- **Historical canonical delivery cohort:** Stage 9A/Stage 10/Stage 11 recorded 11,005 canonical trials across the 25 scenarios (C100 has one canonical result per scenario; the 20 non-C100 scenarios have 550 each).
- **Statistical analytical cohort:** the approved new-execution/continuation policy starts the non-C100 analysis at IDs 1–300 and doubles at 600, 1200, 2400, 4800, … on a per-scenario basis. Exact Golden coverage and the applicable authorization must exist for every extension.
- **Presentation/delivery cohort:** the workbook must use the approved immutable source and declared representative roles; extended analytical trials are not automatically added to the historical delivery dataset or substituted into a manifest.

The v2.0 initial-N table (5000/8000/15000/20000) and its B=1000 bootstrap sufficiency rule must not be silently mixed into the new-execution cohort. The later scoped execution decision controls its defined scope; it does not rewrite historical cohort identities or every output rule in v2.0.

## 2. Approved statistical decision framework versus blocked implementation

### Gate A — exact Golden identity, not mean closeness

Gate A is an integrity/provenance gate. For every covered trial ID it requires exact SHA-256 equality with the approved Golden TrialResult, plus source SHA, master seed, scenario identity, and complete ID coverage. A missing/corrupt governing decision, provider/fingerprint, or unsupported checkpoint is **BLOCKED**; a result/source/seed mismatch is **FAIL**. A correct artifact digest proves integrity, not project authority.

### Family-wise error and IUT — decision accepted, evidence implementation still blocked

The latest owner-approved IUT record is present in current main's docs/PROJECT_CONTINUITY.md (blob 1a69a1f4cf8c87b8e2575a800b92fc80bcd6677e):

- Family-wise target: probability of one or more false SCENARIO_STABLE declarations among the 20 stochastic non-C100 scenarios across the full adaptive inspection horizon is at most 0.05. C100 follows its separate determinism-verification path and is outside this stochastic family.
- Per-scenario risk: alpha_s = 0.0025, with sum_s alpha_s <= 0.05.
- The scenario-level decision is an intersection–union test: every required statistical component and every non-statistical gate must pass. Each component procedure must be valid over all eligible adaptive looks at the required scenario-level risk. This does not imply simultaneous 1-alpha coverage for every table cell/interval.
- The former seven-way within-scenario alpha allocation is retained as historical text and is superseded for this scenario-level IUT decision. Do not silently apply both IUT and the old Bonferroni allocation.

**Status distinction:** the IUT/family-wise policy is **APPROVED AS A DECISION FRAMEWORK**; production false-stability control is **NOT IMPLEMENTED / NOT VERIFIED** until every component test/CS is valid across adaptive looks, required data-identity assumptions hold, and the acceptance code is independently tested.

### Seven §2.5 indicators — target margins and candidate confidence-sequence method

The accepted method-review record identifies a distribution-free, time-uniform fixed-quantile confidence sequence based on order statistics (Howard–Ramdas family; beta-binomial mixture variant is the primary candidate). Preserve the report estimator numpy.quantile(..., method="linear"); it is the point estimate, not a confidence interval. Precision is demonstrated only when the complete confidence set lies within the preapproved band around that estimate. Discrete ties for Held_Assets and Termination_Count must be tested deterministically.

The current policy/method review records these seven indicators and margins:
- P10/P50/P90_Cumulative_Project_Profit and P90_Final_Cash: ±18,500 project-currency units.
- P90_Termination_Count: ±1 termination.
- P90_Held_Assets: ±1 asset.
- Probability_of_Accounting_Loss: time-uniform Bernoulli mean CS/e-process candidate; half-width strictly below 0.005 and the independent adjacent-change condition abs(Delta p) < 0.005.

These candidate methods are **not integrated into the current production decision path**. The prior metric alpha split is not automatically retained under IUT, and no simultaneous all-cells coverage claim is inferred.

### Gate B financial means — acceptance band known; inferential construction blocked

The underlying Gate B acceptance criterion remains the approved three-metric rule:
- Final_Net_Project_Equity
- Partner1_Final_Entitlement
- Partner2_Final_Entitlement

The precision band remains a 95% confidence interval half-width strictly below 1% of abs(mean), with the approved absolute one-currency-unit rule near zero. But the current run_batch.py implementation uses pointwise Student-t intervals at each N and the faulty max(CI_ABSOLUTE_EPSILON, CI_RELATIVE_TOLERANCE * abs(mean)) threshold. It is not time-uniform under adaptive stopping and it does not implement the required branch-at-near-zero rule. The continuity record states no finite support bound or quantified variance/tail/moment bound has been proved for the financial mean outcomes.

Therefore Gate B financial-mean construction remains **K_SPEC / BLOCKED**. Do not substitute bootstrap, Bonferroni, empirical-Bernstein, Catoni, or another CS based on assumed bounds that are not sourced and approved. A bounded-support proof or a separately approved quantified moment/tail assumption is required first. This CP records the current limit; it does not invent one.

### Checkpoint schedule, stopping window, and historical failure

- The policy schedule for non-C100 scenarios is 300 → 600 → 1200 → 2400 → 4800 → …; completed IDs are never rerun. C100 stays on its deterministic trial-ID-1 path under the current applicable decision.
- The accepted IUT record requires **three successful adjacent transitions across four cumulative points**. This is stricter than three checkpoint points/two transitions. Main's current window accepts three history entries, so it is a live implementation defect and must not be called stable under the later rule.
- The P50 continuation trigger is strictly greater than 5.0% on adjacent comparisons 300→600 or 600→1200; when triggered, continue to N=2400 without resetting the failed transition history. This rule is separate from the seven §2.5 indicators.
- C030_G030 / P90_Final_Cash failed N=300→600 at 1.5715059335%. A later pass at 600→1200 does not erase that failure. The prior scenario-specific decision authorizes Golden reference preparation for C030_G030 IDs 1201–2400, not an automatic overall acceptance or N=4800 run. Further requalification beyond the explicitly approved scope needs its own reviewed authority.

### Coverage guard and observed evidence

The read-only P50 review recorded 40 adjacent transitions across 20 non-C100 scenarios; none exceeded the separate 5% continuation trigger (maximum 300→600 change 0.348341%, maximum 600→1200 change 0.191901%, both C050_G000). That does not prove time-uniform precision and does not replace any failed §2.5 indicator.

The current candidate Golden map covers non-C100 IDs 1–1200 and C030_G030 IDs 1–2400 only; the five C100 scenarios have ID 1 each. The other 19 non-C100 scenarios are not Golden-covered to N=2400. The production guard must stop before executing an unsupported target checkpoint and must never create its own Golden reference from the sample it evaluates.

## 3. Remaining blockers and acceptance consequences

The family-wise IUT target and scenario-level decision logic are approved in the continuity record, but the current code does not implement the required valid-over-time component procedures. The approved method-review record specifically leaves financial-mean confidence sequences blocked because finite support or quantified tail/moment bounds have not been established; the seven-metric/quantile and Bernoulli CS choices are recorded as candidates and lack production integration/acceptance evidence. The present pointwise Student-t code and current three-point/two-transition stop window cannot support a final adaptive-stability PASS.

Consequently:
- Family-wise target/framework: **APPROVED**; end-to-end assurance implementation: **K_CODE/K_SPEC — BLOCKED**.
- Financial means: **K_SPEC / BLOCKED** pending support proof or explicit quantitative tail/moment assumptions.
- Quantile and probability-of-loss CS: **METHOD SELECTED AS CANDIDATE; IMPLEMENTATION/ACCEPTANCE MISSING**.
- P90_Held_Assets: threshold ±1 is recorded, but production data path/integration/acceptance test remain missing.
- Do not claim SCENARIO_STABLE or FINAL_ACCEPTED on the basis of pointwise t intervals or historical P50 comparisons alone.

### Historical failed transition: C030_G030 / P90_Final_Cash

The documented N=300→600 relative change is 1.5715059334983579%, exceeding the strict <1% historical threshold. A later passing transition does not erase the failure. The approved IUT record additionally requires three successful adjacent transitions across four cumulative points; the existing C030_G030 record does not satisfy that rule, and its 1201..2400 extension artifact is reference-preparation evidence, not a completed statistical checkpoint. The overall scenario remains blocked. Do not start N=4800 or rewrite the threshold without new explicit authorization.

## 4. Execution topology — separate implemented orchestration from Stage 11 scope

### Verified / observed in the current repository

- Stage 7 is implemented as a 25-scenario matrix with per-scenario state/history, checkpoint evaluation, and immutable trial-block outputs. Its workflow has `max-parallel: 10`, a 40-minute internal budget, and a 45-minute job timeout. The Golden-wiring candidate adds a preflight and per-worker exact-coverage guard, but remains an unmerged draft PR.
- The accepted Stage 10 benchmark report records 45 successful matrix jobs, maximum observed concurrency 10, matrix elapsed time 1051 seconds, and slowest job 470 seconds. This is a measured Stage 10 benchmark, not a measured full Stage 11 runtime.
- Main contains `docs/stage11/dataset_identity.json`, but that file alone does not define an execution workflow.
- A candidate-only decision record, `D-2026-10-14-02`, says Stage 11 is **documentation-only**, its outputs are `docs/stage11/dataset_identity.json` and `docs/stage11/global_manifest_11005_reconciled.json`, no execution topology is required, and the status is `CLOSED_BY_APPROVED_SCOPE_DECISION` (intentionally not `COMPLETE`). It also preserves Stage 10 metadata drift as open. That decision record is not present in the effective `main` decision log at the reviewed HEAD, so its authority still needs formal governance reconciliation; do not treat a candidate-only decision as an effective-main rule.
- Therefore, do **not** invent or implement a separate Stage 11 production workflow just to fill the earlier topology gap. Reconcile the missing scope decision and retain the recorded Stage 10 metadata-drift blocker.

### Topology contract for the existing Stage 7 → Stage 12 → Stage 13 path

This is the target control sequence for review; items marked target are not a claim that an authorized production rehearsal has passed.

1. **Read-only preflight (target):** pin source SHA/seed, scenario set, immutable manifest identities, Golden provider provenance and approval status, full exact Golden coverage through the requested checkpoint, and tool/schema versions. Coverage alone must not be mistaken for decision authority.
2. **Scenario workers (partly observed in Stage 7):** matrix over 25 scenarios with maximum parallelism 10; restore exact completed IDs and run only missing authorized ranges. Each scenario has its own state/history. No worker may start an unsupported target checkpoint.
3. **Checkpoint gate (target for the provider candidate):** validate canonical ID continuity and source/block identity, then apply exact Gate A, Gate B and the supplementary transition checks. Gate A that is not explicit PASS or coverage that is absent stops before any next trial block. The 75 focused/static checks validate wiring contracts, not production checkpoint acceptance.
4. **Aggregate barrier (Stage 12 evidence):** only accept the aggregate after all required scenario data has matching identity, row counts and hashes. Historical Run 37964656154 is recorded as 25 scenario ledgers, 22,546,465 daily rows and zero retries; verify current source artifacts/contract before reuse.
5. **Stage 12 → Stage 13:** Stage 13 must use the accepted Stage 12 delivery input and manifest, validate representative trial identity/fingerprint, daily terminal reconciliation, exactly 185 workbook sheets, precision serialization, zero formula/error cells, and README sheet count. Missing financial fields stay `MISSING_EVIDENCE`; pending markers may keep a diagnostic workbook explicit but do not qualify as final acceptance.
6. **Runtime safety:** the 40-minute internal cap within a 45-minute job timeout leaves five minutes for unwind/state persistence/upload. Stage 10's 470-second maximum is not evidence for the full adaptive Stage 7 path, and no full production-workload timing has been established here. Do not label the runtime budget production-proven without an authorized, identified rehearsal.

**Disposition:** Stage 11's intended scope is candidate-documented as documentation-only/no execution topology, but that scope decision is absent from effective `main` governance and Stage 10 metadata drift is still open. Stage 7 Golden provider wiring is candidate-only and passed focused static/unit verification; it has not executed or passed a production checkpoint. The overall sequence and final delivery remain unaccepted until governance authority, statistical validity, data blockers and final artifact checks are closed.

## 5. Required status vocabulary

Keep these statuses separate:
- `GATE_A_PASS` / `GATE_A_BLOCKED` / `GATE_A_FAIL`
- `GATE_B_POINTWISE_PASS` / `GATE_B_FAIL`
- `TRANSITION_GUARD_PASS` / `TRANSITION_GUARD_FAIL`
- `SCENARIO_STABLE` only after the three-consecutive-point policy and all applicable transition constraints are resolved
- `FAMILYWISE_ASSURANCE_UNRESOLVED` until the formal adaptive-inference specification is approved and validated
- `FINAL_ACCEPTED` only after all required delivery files are built from the approved cohort and independently verified

This reconciliation is a documentary candidate. It does not alter production code, authoritative reference files, historical records, manifests, trial IDs, or delivery status.

## 6. Effective branch reconciliation — D-2026-10-24-02

The branch now records decision `D-2026-10-24-02` in `docs/governance/DECISIONS_LOG.md`, reflects it in `state.json` and `docs/PROJECT_CONTINUITY.md`, and adds a static verification workflow. The decision closes the Stage 11 *scope question* as documentation/identity reconciliation only; it does not claim a production runtime topology was measured. It preserves the observed Stage 10 benchmark values and leaves its `source_identity=PARTIAL`, `fidelity=PARTIAL`, and 40/45-minute `G2_RISK` open.

The effective branch checks the reconciled `global_manifest_11005_reconciled.json` and `dataset_identity.json` without rewriting them: 11,005 canonical trials, 25 scenarios, seed 20270101, source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, and G1–G8 pass. It also verifies `state.json` remains `12-CLOSED` and keeps `STATISTICAL_INFERENCE_BLOCKED`, `STAGE10_METADATA_DRIFT_OPEN`, `FINAL_DELIVERY_NOT_ACCEPTED`, and `G2_RISK` as explicit blockers.

This is a candidate governance CP on `tmp/cp-statistical-topology-reconcile-20261024`; it does not write `main` or alter canonical trial data. Its static workflow must pass on the exact final head before this decision/state correction is merged.

## Effective-main replay after PR #64 merge — 2026-10-24

The original document above records the before-PR64 candidate state. The exact-head Gate A provider candidate was subsequently merged into main as `ca813f3fcf928ebb7143ad6301ae6fe8e6287b77` after fixture-first CI Run `40103434415` passed 488 tests with one documented K_TEST skip. The provider/map is now present on main and its scoped read-only decision `D-2026-10-24-01` is effective. The statistical gate remains `BLOCKED_FOR_IMPLEMENTATION`; no production execution, stability declaration or final acceptance is permitted.

This rebased Stage11 CP updates the governance decision log and state snapshot only to record `D-2026-10-24-02`: Stage11 is documentation/identity reconciliation for the existing 11,005-trial cohort and does not require a separate runtime workflow/topology. The scope decision retains Stage10 metadata/fidelity drift and G2 runtime risk. Its static workflow explicitly validates the merged statistical-gate schema using `execution_authorization`, not the old candidate-only field name `authorization`.

No Trial/Checkpoint/Monte Carlo or production workbook ran. Final delivery remains NOT_FINAL_BLOCKED.
