# D-2026-10-29-S6-REFERENCE-CHECKPOINT-RECONCILIATION

**Date:** 2026-10-29  
**Status:** OWNER-DIRECTED S6 GOVERNANCE RECONCILIATION; NOT PRODUCTION ACCEPTANCE  
**Scope:** Exact reference identity, unlimited checkpoint schedule, test-fixture provenance, S6 full-accounting evidence boundary, and independent financial Golden approval.  
**Protected refs:** `main` is read-only in this decision. This decision was recorded only on `tmp/s6-aggregate-contract-fix-20261027`.

## 1. Normative reference conflict — resolved by source lineage

The supplied immutable normative file `المرجع_النهائي_الموحد_v2.3-إعادة_صياغة.md` was hashed from its actual bytes and equals:

`e5efaf0874384e8248c339ca10e248ea9e17f0882153b4ef88bc955b91d53f`.

The explicit project instruction selects that exact file/hash as the sole normative reference for S6 v2.3. Do not modify the reference file, or treat an alternate file/hash as a replacement for this S6 task.

The older SHA `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479` is retained as historical reference identity for the pre-existing `main` / `SOURCE_SHA=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b` lineage. It is not silently overwritten or retroactively declared invalid for historical records. The two identities are not to be combined in a single cohort or treated as byte-identical.

The S6 v2.3 execution contract already on this temporary branch points to the supplied `e5ef...` file and binds to `SOURCE_SHA=da1a9ea9b5cd789c944de3f07b08395bb67c49e7`, `cohort_id=s6-v23-da1a9ea9`, `MASTER_SEED=20270101`. The gate change in commit `4d5f794a275b9a0b2cf7c7ec8f5ccb919ed14270` adds this reconciliation context without editing `main`, changing business thresholds, changing the seed, or changing production acceptance flags.

The uploaded reference has internal wording that includes both approved/effective and draft/not-auto-approved labels. For this task, the exact byte identity selected by the explicit project instruction governs S6 scope; the wording conflict is disclosed rather than hidden, and the reference remains immutable.

## 2. Checkpoint contract — resolved, unbounded, no false ceiling

The normative schedule is `N_k=300*2^(k-1)` for `k=1,2,...`: `300 → 600 → 1200 → 2400 → 4800 → 9600 → …`. The list `[300,600,1200,2400]` is the initial four-point cumulative evaluation window, not an upper bound. Four points are the minimum window required to evaluate three consecutive adjacent transitions; they are not a ceiling. Continue to the next doubling point unless `CONVERGED` is established, or a separately evidenced operational stop is approved and recorded.

At checkpoint index `k`, use the normative spending rule `alpha_s,k = 0.0025/(k*(k+1))`; `k` continues without a fixed upper limit. Do not evaluate at non-checkpoint `N/2`, reset `k`, discard a historical failure, or transfer stability history across source/cohort identities.

Read-only source review confirms that `scripts/stage7_stability.py::next_statistical_checkpoint` already computes the next doubling checkpoint without a fixed ceiling. The defect was that the JSON contract exposed only the initial four points without explicitly saying the sequence continues. Commit `4d5f794a275b9a0b2cf7c7ec8f5ccb919ed14270` adds explicit machine-readable extension semantics to the candidate gate. Gate status and acceptance booleans are unchanged: this does **not** declare Gate A, Gate B, stability, or final delivery accepted.

## 3. Missing Stage 5 test-fixture data — provenance identified, outputs not fabricated

The files missing from the tracked tree are `results_stage5/worker_equivalence_manifest.json`, `results_stage5/trials_summary.parquet`, and `results_stage5/daily_distribution.parquet`.

The source code that has historically generated them is inline and ephemeral in the following current-main workflows:
- `.github/workflows/stage4-acceptance-port.yml`, blob `120366c01a7b7624d4dd1d8ff81e75a94c337e69`;
- `.github/workflows/stage9c-precision-regression.yml`, blob `1f54d80cb026b25be7ce21a8e678bdebe6d36623`;
- `.github/workflows/stage5-main-postround2-validation.yml`, blob `abe1f8afdb6fc13a1a44e4811f25c44f70099db8`.

The inline scripts delete/recreate `results_stage5`; the builder calls `monte_carlo.run_single_trial("C100_G100", 1, master_seed=20270101)`, asserts hard-coded outputs and 2,198 daily rows, and the additional manifest generator runs sequential/parallel `C070_G100` trial IDs `1..3`. These are instructions for rebuilding disposable fixtures, not a retained immutable dataset artifact. Their workflow uploads do not retain this input directory as an authoritative artifact.

Decision: record the source recipe and its provenance, but do not invoke it, download unrelated outputs as substitutes, create invented fixtures, or rerun completed trial IDs. The recorded full suite for PR #78 is still `NON_PASS` (`5 failed, 512 passed, 1 skipped, 1 warning` on each recorded run); its focused R4 test passed, which does not convert the full-suite result into PASS. Closing this evidence gap requires a separately reviewed fixture policy that uses immutable prior outputs or expressly authorizes disposable fixture generation with exact model/source scope.

## 4. Full accounting balance evidence — separate lineages, explicit gap

### Existing, verified full-accounting evidence for the older main cohort only
- Source identity: `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`; seed `20270101`; schema `stage12-daily-accounting-v1`.
- Roll-forward report `docs/stage12/roll_forward_validation.json`, blob `6084e8f68fa649fcf0726daa04f41ae9b0636706`; source Run `37964656154`; audit Run `37971902520`; Artifact `11636856147`; archive SHA-256 `fe677294001f4239d72b53524efa1759897d8ae85ad0d843161e1a094435ce87`. The immutable report states 22,546,465 rows, 25 scenarios, 11,005 trials, and zero roll-forward violations, including assets/equity and balance-difference checks.
- Closure report `docs/stage12/closure_settlement_validation.json`, blob `81bc3cd9c7666487b69b644dcc3291d0547c8e8b`; Run `37972735159`; Artifact `11636767404`; archive SHA-256 `16287336a360bc08ad3ce34de220765f6ed815f9f62cb44071cc3232e0014bd8`. It independently states 22,546,465 rows with zero violations for terminal balance difference and terminal assets equal equity.
- Both archives passed ZIP integrity checks and their downloaded outer digests match the Actions API. This is `VERIFIED` for the older `f3af...` lineage only; it is not evidence for S6's `da1a...` cohort.

### Historical S6 N=2400 full balance remains missing
- S6 source Run `40731224990`, source head `a23ba71f48487f3ebead99bc30039b14ef9b7609`, source SHA `da1a9ea9b5cd789c944de3f07b08395bb67c49e7`, cohort `s6-v23-da1a9ea9`. The parent run failed, although 20 scenario jobs and their artifacts were successful and verified. The source-run metadata's original `sha256` remains null.
- The read-only N=2400 report Run `40787081064`, Artifact `12859837254`, archive digest `f6cafd8dc682191db83464cbbbc43b73d0cf2bc105ab7c795b08abdb109d6c73`, JSON digest `a2cb641beb3896cffca14629212594b8c55394b619628c7f840ac4b8e82fb6a1`, verified `Net_Equity == Capital + Retained_Earnings` in 98,323,918 stored rows with zero mismatches. It explicitly reports `full_balance_sheet_status=MISSING_EVIDENCE`.
- Existing S6 daily snapshots omit `Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, and `Total_Assets`. There is no persisted full daily balance-sheet projection in those historical artifacts. This cannot be repaired for N=2400 by inference or backfill; do not alter historical artifacts or rerun IDs 1..2400.
- Current temporary source `monte_carlo.py` (blob `dab5fdec1325c76700a39ec4713656574fada828`) now projects a versioned complete daily balance snapshot from `accounting.balance_sheet_snapshot`; the pure no-simulation test `tests/test_s6_daily_balance_snapshot_schema.py` (blob `2b345c008f1b146201c89c1dfdc0fbf65cdd6094`) checks the initial-project projection. The verification workflow was added in commit `f4de3352d080eb433e3852d5a365b5655d054619`. No verified CI run result was found in this review, so the test execution status is `NOT_VERIFIED`. Even if the projection test passes, it validates new output shape, not the historical N=2400 files. Its schema changes the complete daily-path fingerprint input, so validate source/schema/path identity and independent Golden compatibility before a future checkpoint; no N4800 run is authorized by this decision.

## 5. Independent Golden approval — explicit, hash-pinned, narrowly scoped

The candidate workflow `40760465042` completed successfully on tested SHA `3a972c9a0b18b9bc170a289a6aaf8fe1b8797f10`; artifact `12857612467` digest `sha256:e6d94d715eb7e52ffc8ba61ae6dafb766b76914d956879190f1e87b87e311078`. Its map SHA-256 is `32abf1d54be67c5e9ee37e9e14ad3bc28c9d1c0e36b2af17e44bbb23b5b3e581`; manifest SHA-256 is `6a79489331f78a5cfe1db67ec3c7ead1dace1f0aa3d31614208d1d0be27ec4c3`; combined map hash is `3312c57580c1717b2b59f64a7c0e2611d206d552b847639f31de5735852f711c`. All 20 scenarios cover trial IDs `1..2400`, totalling 48,000 fingerprints; candidate generation read no production result artifacts.

Independent comparison Run `40784902124`, Artifact `12859860023`, reports `PASS_EXACT_MATCH`: 48,000/48,000 financial fingerprints match, zero mismatches. Its overall audit still fails at the full-accounting guard; that remains visible.

Based on the explicit instruction to approve the independent Golden, a separate approval record is created at `docs/stage7/S6_GOLDEN_APPROVAL_DA1A_N2400.json`. It pins source/cohort/seed/schema/trial coverage, both candidate inner-file digests, the immutable outer artifact digest, the tested Actions SHA, all 20 per-scenario artifact file digests, and the exact comparison report. It authorizes use of this map **as a read-only financial fingerprint reference for S6 Gate A evaluation**.

This approval deliberately does **not** declare production Gate A PASS, Gate B PASS, full accounting balance, convergence, or final delivery acceptance. The candidate's original status `INDEPENDENT_GOLDEN_CANDIDATE_NOT_APPROVED` remains unchanged as historical artifact metadata; the separate hash-pinned approval record supplies the independently reviewed approval input expected by the S6 loader. The missing original source-run metadata digest and full balance-sheet evidence remain explicit exceptions.

## 6. R4 closure table for this decision

| Item | Execution | Evidence status | Disposition |
|---|---|---|---|
| S6 v2.3 reference selection | `EXECUTED` | `VERIFIED` for supplied immutable file; `CONFLICTED` only if legacy main identity is mixed into S6 | Scope E5 to S6; preserve EE for historical f3af lineage; do not modify main/reference bytes |
| Unlimited checkpoint contract | `EXECUTED` | `VERIFIED` against reference and code; candidate gate contract updated | Initial four points are minimum window, not ceiling; alpha spending extends for all k |
| Missing Stage 5 fixture source | `EXECUTED` | `VERIFIED` for inline workflow recipe; `MISSING_EVIDENCE` for immutable output dataset | No rerun/fixture generation until separately reviewed fixture policy |
| Main Stage12 accounting evidence | `EXECUTED` historically | `VERIFIED` for f3af only | Cannot be reused as S6 da1a evidence |
| S6 N2400 full balance | `EXECUTED` partial recheck | `MISSING_EVIDENCE` | Keep 98,323,918-row partial identity pass scoped; no backfill |
| Independent Golden financial map | `EXECUTED` comparison and recorded approval | `VERIFIED` for exact financial-map scope | Separate approval file, not blanket Gate A/B or final acceptance |
| N4800 / final delivery | `NOT_EXECUTED` | `BLOCKED` | Complete source/schema/path-identity preflight and independent accounting status first; any future continuation uses only IDs 2401..4800 |

## 7. Required next actions

1. Verify the new approval JSON against the exact candidate map/manifest and comparison evidence using the S6 loader's hash and identity checks, without running a Trial. Only then regard the approval file as structurally verified.
2. Obtain a verified, non-simulation CI result for the new daily-snapshot projection test if the configured workflow can run within the non-blocking review path; do not trigger N4800 or any workflow that replays completed trials.
3. Decide the new full-daily schema/source identity and path-fingerprint contract before a future checkpoint. Existing S6 N2400 rows remain incomplete and immutable; old main Stage12 rows are another lineage.
4. Adopt a separately reviewed test-fixture policy; no immutable `results_stage5` input bundle is currently identified.
5. Keep Gate B, stability, and final delivery acceptance blocked until their own exact-cohort evidence and review conditions pass.


## 8. Verification results after the approved read-only Gate A review — 2026-10-29

### Golden and balance projection verification
- Read-only workflow Run `40795230337`, tested SHA `ae3a50f3a5580ceff2715ae7218043ebf5e895b7`, completed `success`. Artifact `12862963702`, outer SHA-256 `288fd93c44e15520b9ba07e119e0b702d53be77254081828afac0bfa6d1bc25d`, report JSON SHA-256 `3461dd75fda118e95f1f8be851c437ddc943fd62c058853d8941f46f1c972bc4`. It independently checked the Golden map/manifest/approval and called the real S6 approved-Golden loader. Scope: 48,000 fingerprints, 48,000 exact matches, zero mismatch. The report explicitly retains daily full-balance `MISSING_EVIDENCE`, 0 rows recomputed, Gate B `FAIL_SCOPED`, stability `NOT_CONVERGED`, acceptance `NOT_GRANTED`.
- Read-only checkpoint comparison Run `40795628228`, tested SHA `fe0ab11a00bf05f958a7cc2eb4c05064128bbfc3`, completed `success`; artifact `12862934537`, outer SHA-256 `d465de983b6fd574f792eae245f92745c3a70bcaf40e11bbbb7ec76f5ebc073b`, report JSON SHA-256 `3683605fda2e2e3a0a3a3f370c404d7de32b30347155b803a49729e4407849b9`. It loaded the approved map through `scripts/s6_first_checkpoint.py::load_approved_gate_a_golden`, then applied the actual `evaluate_gate_a_checkpoint` function to the immutable N2400 aggregate trial rows for the initial cumulative checkpoints 300, 600, 1200 and 2400 across all 20 stochastic scenarios.
- Gate A retrospective scoped result: **80/80 scenario-checkpoint pairs PASS**, **90,000** financial-fingerprint comparisons, **zero** mismatches. Verified per-checkpoint pairs: N=300: 20/20; N=600: 20/20; N=1200: 20/20; N=2400: 20/20. The separate total production-vs-Golden comparison remains 48,000/48,000 exact.
- This evaluation reads previously materialized trial rows from immutable Artifact `12852969854` / aggregate Run `40773412377`, manifest SHA-256 `3f01d143b7c98a0da272fa38411d079572deae328afbba81b24320b4a745a6ba`. The historical aggregate and prior statistical JSON were not rewritten; their historical Gate A `NOT_EVALUATED_NO_SAME_SOURCE_PRODUCTION_GOLDEN` status is preserved as at the time of that run.
- Daily balance projection unit verification Run `40792786844`, tested SHA `f4de3352d080eb433e3852d5a365b5655d054619`, completed `success`: `py_compile` and `tests/test_s6_daily_balance_snapshot_schema.py` succeeded without running a simulation Trial. This validates the pure snapshot projection contract on an initial project object, not the historical N=2400 Parquet exports.

### Updated interpretation
- S6 gate JSON blob `05b4fadd14e8670a765714fef1954af9b9d78855` records `gate_a_exact_golden.status=PASS_SCOPED_FINANCIAL_FINGERPRINT_MATCH_BY_CHECKPOINT` with the approval identity, artifact digest, checkpoint comparison evidence, and explicit remaining accounting/provenance blockers.
- Overall gate status remains `AUTHORIZED_FOR_V2.3_EXECUTION` for the scoped S6 candidate contract; `scenario_stability_declaration_allowed=false`, `final_delivery_acceptance_allowed=false`, and `final_production_gate_cleared=false`. This is not an overall project acceptance or convergence result.
- Gate B remains `FAIL_SCOPED` in the immutable N=2400 evidence: 10/20 pass and 10/20 fail at N=2400; 60 historical transitions, zero successful transitions. The independent Golden approval does not change any Gate B estimate or historical transition.
- The five asset-side fields absent from the S6 historical `daily_snapshots.parquet` remain absent. No full `Assets == Equity` row was recomputed for S6. The new projection writes future schema `s6-daily-balance-v1`; its addition changes daily-path fingerprint inputs, so source/schema/path-identity and Golden compatibility must be reviewed before any next checkpoint. Do not backfill the old data or start N=4800 as a result of these scoped passes.
- Original source Run `40731224990` remains parent `failure`; its 20 scenario jobs/artifacts are verified, but the original `source_run_metadata.sha256` remains null. No substitute hash was written.
- Verifier-fix runs `40794882008`, `40794944921`, and `40795071356` remain failed on their tested verifier revisions. Preserve them in the audit trail as validator defects (field-status literal, run-ID string normalization, and reference digest typo); subsequent exact-head verification passed on Runs `40795230337` and `40795628228`. These failures are not production-trial failures.

## 9. R4 refresh after read-only Gate A review

| Item | Execution | Evidence status | Disposition |
|---|---|---|---|
| S6 normative reference selection | `EXECUTED` | `VERIFIED` | E5 reference bound to S6 cohort; EE preserved for historical f3af lineage |
| Unlimited checkpoint extension | `EXECUTED` | `VERIFIED` in candidate gate contract | `N_k=300*2^(k-1)`, unbounded k; alpha spending unbounded; no N4800 authorized here |
| Missing Stage 5 fixtures provenance | `EXECUTED` | `VERIFIED` recipe / `MISSING_EVIDENCE` immutable dataset | No fixture data files retained; no build or trial rerun |
| Golden approval and runtime loader | `EXECUTED` | `VERIFIED` scoped | Separate approval JSON passes the runtime loader and hash/identity checks |
| Gate A financial fingerprint checkpoints | `EXECUTED` | `PASS_SCOPED` | 80/80 pairs PASS; 90,000 comparisons; 0 mismatches |
| Full daily S6 Assets == Equity | `NOT_EXECUTED` for historical full-row recomputation | `MISSING_EVIDENCE` | Historical S6 snapshots lack the required fields; new projection unit test is not historical proof |
| Gate B / stability / release | `BLOCKED` | `FAIL_SCOPED / NOT_CONVERGED / MISSING_EVIDENCE` | No stable declaration, no P17/P18 acceptance, no `FINAL_ACCEPTED` |
| N=4800 | `NOT_EXECUTED` | `BLOCKED_PENDING_SOURCE_SCHEMA_PATH_PREFLIGHT` | Any later authorization uses only IDs 2401..4800 |

