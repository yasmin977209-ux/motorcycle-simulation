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

## 2. Resolved operational statistical protocol for new execution

### Gate A — exact Golden identity, not mean closeness

Gate A is an integrity/provenance gate, not a statistical tolerance test. For every covered trial ID it requires exact SHA-256 equality with the approved Golden TrialResult, plus the approved source SHA, master seed, scenario identity, and complete ID coverage. A missing provider/fingerprint or unsupported checkpoint is **BLOCKED**; a mismatching result/source/seed is **FAIL**. Gate A must not be replaced by average/percentage similarity.

### Gate B — pointwise confidence-interval precision

For the approved new-execution path, Gate B uses the Student-t 95% confidence interval for the three approved financial metrics:
- `Final_Net_Project_Equity`
- `Partner1_Final_Entitlement`
- `Partner2_Final_Entitlement`

At each applicable checkpoint, the half-width must be strictly less than 1% of the absolute mean; the approved absolute tolerance is 1 currency unit near zero. The implementation must retain the approved strict inequality. All three metrics must pass. This is a pointwise precision test at each checkpoint; by itself it is **not** a demonstrated family-wise false-stability guarantee under adaptive stopping.

### Escalation and the supplementary §2.5 transition rule

- For non-C100 scenarios, the operational checkpoint schedule is (300 	o 600 	o 1200 	o 2400 	o 4800 	o cdots); there is no general cap in the governing execution policy. Never rerun completed IDs; generate only the missing next interval.
- C100 is a deterministic special case: one canonical TrialResult (trial ID 1), plus the specified independent verification execution with a different trial identity/derived seed. C100 is not treated as a 300-sample stochastic cohort.
- A scenario can be finally stable only after **three consecutive checkpoint points** satisfy the approved Gate A and Gate B criteria. Do not reinterpret this as three transitions: three points and three transitions are different counts.
- The approved P50 continuation rule is separate: compare adjacent checkpoint P50 values using the declared formula; a relative change **strictly greater than 5.0%** requires continuation to N=2400 for that scenario. At a denominator below the approved reference epsilon, use the already approved one-currency absolute comparison rather than inventing a percentage or a new epsilon.
- The separately specified seven-indicator §2.5 adjacent-transition evaluator remains a **supplementary transition gate**. It neither replaces exact Gate A nor changes the three-metric Gate B definition. Preserve each failed transition in history even if a later transition passes.

### How current evidence bounds extension

The preserved N=300/600/1200 reports and the read-only P50 review show 40 adjacent transitions across the 20 non-C100 scenarios; none exceeded 5%. The largest P50 changes recorded were 0.348341% for N=300→600 and 0.191901% for N=600→1200 (both C050_G000). Those calculations do not create universal N=2400 Golden evidence.

The current exact Golden map supports IDs 1–1200 for the non-C100 scenarios and IDs 1–2400 for C030_G030 only, with the five C100 scenarios covered at ID 1. The approved scenario-specific extension decision authorizes C030_G030 IDs 1201–2400. For the other 19 non-C100 scenarios, a Gate A pass cannot be claimed beyond ID 1200 until exact, independently approved extension maps are verified. The runtime must refuse to start a target checkpoint whose whole ID range is not covered.

## 3. Statistical assurance items deliberately not fabricated

The reference conflict map records a proposed family-wise α / IUT approach, a requirement for valid inference across adaptive looks, disagreement over the v2.0 bootstrap method and seven metrics, and an unresolved source/threshold for `P90_Held_Assets`. The current documented pointwise t-CI rule does not, by itself, settle those inferential questions.

Therefore:
- Status for family-wise error control under adaptive stopping: **UNRESOLVED / NOT CLAIMED**.
- Do not implement Bonferroni/IUT, a confidence sequence, percentile/BCa bootstrap, finite-support assumptions, or a new `P90_Held_Assets` threshold by intuition.
- Before making a claim that the whole adaptive procedure controls false stability at family-wise 0.05, the owner must approve a formal specification that states the estimand/null, scenario family, metric family, dependence and look structure, stopping rule, interval or test construction, simulation/calibration tests, and treatment of all previously observed looks.

### Historical failed transition: C030_G030 / P90_Final_Cash

The documented N=300→600 relative change is 1.5715059334983579%, exceeding the historical strict <1% threshold; a later passing transition does not erase this fact. The available decisions do not unambiguously specify whether this historical failure is permanently disqualifying for overall scenario acceptance or whether a later, explicitly defined requalification rule may resolve it. Preserve the failed point in the record and classify overall acceptance of that scenario as `UNDEFINED_BUSINESS_RULE` pending a written owner decision. No N=4800 run or rule change is authorized by this note.

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
