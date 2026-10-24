# Owner-approved delivery preparation — 2026-10-25

## Purpose and authority boundary

This is a candidate-only engineering record following the owner's explicit approval in the current conversation to proceed with the proposed delivery-preparation plan. It does not change the effective governance on `main`, authorize production Monte Carlo/trials/checkpoints, authorize new Golden generation/extension, declare stability, accept the final delivery, or create a Release.

- Repository baseline: `main` at `c6e54349a5e94f65d5aa9f83141f225d777bb474`.
- Work branch: `owner-approved-delivery-preparation-20261025`.
- Baseline canonical model source identity in current governance: `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`.
- Baseline `rng.py` blob: `e50d0410729aeeb657d4b187c0bc32f9527442d1`.
- Effective main gate: `docs/stage7/statistical_execution_gate.json` = `BLOCKED_FOR_IMPLEMENTATION`; trial/checkpoint/production Monte Carlo, stability declaration and final acceptance are all explicitly unauthorized.

## First candidate implementation

The owner approved preparation of an independent change that brings the RNG stream key into line with the reference's `SEED_SCOPE=COLLECTION_LEVEL` rule.

- Before: `master_seed | Cxxx_Gxxx | trial_id | bike_id | date | event_type`.
- Candidate: for canonical `Cxxx_Gxxx` IDs, `master_seed | Cxxx | trial_id | bike_id | date | event_type`.
- Guarantee-recovery variants within a collection level must share the same event seed when all other event dimensions match.
- Different collection levels, trial IDs, bikes, dates, and event types must continue to produce distinct seeds.
- All historical Parquet/JSON/TrialResult data, manifests, Golden fingerprints, and `main` remain untouched.
- Because this candidate changes RNG behavior, it must not be represented as the same historical source identity or be combined with old outputs as if produced by the modified engine.

Candidate CI will test the seed contract and the scoped acceptance tests only. A green candidate CI result does not authorize a production trial, checkpoint, statistical-stability declaration, Golden extension, final workbook, or Release.

## Reference identity must be reconciled before production acceptance

The attached comparison reference `المرجع_النهائي_الموحد_v2.1-1.md` has SHA-256:

`297fb4c445bcce20fdd66a02d65aea00c74007d2f3d7c68ead416a5822fd5582`.

The effective `docs/stage7/statistical_execution_gate.json` on `main` identifies a governing reference SHA-256 of:

`ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`.

These are not equal. This record does not assume that the attached v2.1 comparison file silently supersedes the reference identity embedded in the effective production gate. Before any production cohort or final acceptance, an explicit reviewed governance update must identify the authoritative reference version and map the applicable amendments/decisions to it. Until then, reference identity for production is a blocker.

## Statistical and source identity blockers that remain open

1. `K_SPEC`: no accepted all-time-valid method for the three financial means under adaptive stopping; no approved finite-support proof or quantified tail/moment assumption.
2. Other required time-uniform components: quantile/mean-of-loss-probability candidates are not yet integrated and accepted; `P90_Held_Assets` production data identity/completeness and fail-closed acceptance are unresolved.
3. Gate A coverage: the current pinned map covers 25 scenarios and 25,205 fingerprints; non-C100 scenarios cover through N=1200, while only `C030_G030` has the authorized extension through N=2400.
4. Historical failed transition: `C030_G030 / P90_Final_Cash`, N=300 to N=600, changed by 1.5715059335%, above the strict <1% criterion, and remains `FAILED_NOT_REQUALIFIED`.
5. Termination/funding: the canonical initialization's reachability/termination properties for a PREP bike that cannot be funded have not been proved; no arbitrary close-date cap is to be introduced as a shortcut.
6. Stage 10: metadata/source identity and fidelity remain `PARTIAL`; topology/runtime measurement limitations remain explicitly recorded.
7. Stage 9C/Excel and final release: scoped C-1..C-6 evidence does not by itself constitute full Stage 13 acceptance. The complete AR/EN set plus `manifest.json` must be generated together and independently read back; P17 is not accepted and P18 remains blocked until evidence permits a new verdict.

## Candidate acceptance sequence

- Validate this candidate's seed-key and regression tests on its exact HEAD.
- Have an independent reviewer compare the exact diff with the controlling RNG contract and check that no unrelated model equations or historical data changed.
- Review and approve the replacement source identity and Golden/cohort strategy as a distinct, explicit decision.
- Do not run a production cohort/checkpoint until the effective statistical execution gate is separately changed to an accepted state through a reviewed, evidence-backed governance procedure.
- Only after all statistical/source/data blockers are closed, conduct authorized scenario/checkpoint runs in the approved doubling sequence and stop before unsupported Gate A coverage.
- Accept final delivery only after every required output, accounting and provenance check, full-suite test, independent audit, and P17/P18 release requirement passes.

## Realism model boundary

The reference-compliant baseline and a realism-calibrated business forecast are separate products. No market price, inflation series, maintenance rate, vacancy rate, default distribution, insurance cost or resale value is invented in this candidate. The separately prepared data specification lists the minimum evidence needed to calibrate a new version. Any such model change requires its own approval, source identity, test protocol, and out-of-sample validation.

## Final status

`CANDIDATE_WORK_IN_PROGRESS` — this branch contains bounded work only. No production simulation or new Golden generation was run by this record. `main`, canonical historical outputs and release status remain unchanged.

## Candidate verification evidence — 2026-10-25

The current code/test diff was exercised by candidate-only GitHub Actions (no production workflow was dispatched):

- [Stage 1 Run 40137686463](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40137686463), tested code head `1fb21be99eccf3a4bb96006bd41a169edd87dcf2`: **7 passed**. This includes the exact collection-level key digest, coupling across all configured recovery levels and cross-process reproducibility.
- [Candidate preflight Run 40137686458](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40137686458), same tested head: **158 passed, 1 skipped, 4 deselected** in the active acceptance subset; the four tests requiring Stage 5-generated fixtures were explicitly excluded, not counted as passed. The second deterministic regression group passed **164 tests with one warning**, covering `run_batch`/Stage 7 fail-closed checks, daily Excel serialization and Stage 13 assembler/audit-loader/pending-field checks.
- No Monte Carlo cohort, production Trial/checkpoint, Golden generation/extension, stability declaration, final workbook acceptance or Release was run by these candidate workflows.

The owner-authorized P17 report restoration and current P17/P18 revalidation documents are now also retained on this branch; their verdict remains **P17 = NOT_ACCEPTED; P18 = BLOCKED, no Release**. This restores review evidence on the candidate branch only, not on `main`.

## Exact current repository state

- `main` remains `c6e54349a5e94f65d5aa9f83141f225d777bb474`.
- This branch is candidate-only. It must not be merged while the RNG/source identity and Golden plan, reference SHA reconciliation, `K_SPEC`, incomplete Gate A coverage, historical failed transition, realism data, and final delivery acceptance remain unresolved.
