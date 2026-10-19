# CP-SOURCE / Gate A — source identity and golden-provider read-only review

**Date:** 2026-10-19  
**Mode:** M3 read-only evidence review; no source, workflow, test, dataset, trial, or protected-state change.  
**Review branch:** `tmp/cp-session-continuity-20261017` (continuity evidence only)  
**Current main HEAD:** `647c19826b90d8224ce73ef9b90c306a45e03fb0`  
**Pinned `SOURCE_SHA`:** `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`  
**Stage 11 dataset identity blob:** `72a481d509d39820fba78732724fde4fa9f25134`  
**Stage 12 roll-forward validation blob:** `6084e8f68fa649fcf0726daa04f41ae9b0636706`

## R4 authority table

| Item | Current verified state | Authority / branch | Exact controlling evidence | R4 ruling |
|---|---|---|---|---|
| Pinned model source | 13 of the 14 Stage 7 model files have identical Git blob SHAs at pinned `SOURCE_SHA` and current `main`; `daily_engine.py` differs: pinned blob `6c4496c3e9a9b41668c3d93063ad31d96df5f878`, main blob `0d17d1923fbf95ba7f3e4b6ae695bfbf80f85964`. | main `647c19826b90d8224ce73ef9b90c306a45e03fb0`; candidate Stage 7 Workflow blob `514aff8bbde36e961f077469989b1245dff52c51`. | Candidate Workflow source check literally runs `git diff --quiet "${SOURCE_SHA}" HEAD -- "${MODEL_FILES[@]}"`; when unequal it prints `MODEL_SOURCE_DRIFT_DETECTED` and exits 1. | **Verified K_CODE / SOURCE_SHA_DRIFT blocker.** Do not change `SOURCE_SHA`, revert the model, mix datasets or run production without a separately authorized identity-preserving decision. This review did not execute that Workflow step. |
| Gate A acceptance | `scripts/stage7_stability.py` blob `468b96b7b592a1ddd55cd4440962775632ab55a1` requires expected/actual golden SHA-256, reference ID, and expected/actual source SHA. | Normative decision D-2026-10-10-01 in main governance log; `REFERENCE_AMENDMENTS.md` / Amendment-01. | Exact failure text in code: `approved exact-golden fingerprint and source identity evidence not supplied`; missing any evidence returns `status="BLOCKED"`, `checked=false`, `stable=false`. | **Rule contract verified**; no tolerance substitute is allowed. |
| Runtime Gate A caller | Candidate `stage7-full-run.yml` blob `514aff8bbde36e961f077469989b1245dff52c51` calls `evaluate_gate_a` with prior/current N and metrics, escalation multiplier and epsilons, but does not pass the five golden/source identity arguments. | Candidate only; current main state records `GATEA_PROVIDER_MISSING`. | In the exact caller, the keyword arguments `expected_golden_fingerprint_sha256`, `actual_fingerprint_sha256`, `golden_reference_id`, `expected_source_sha`, and `actual_source_sha` are absent. | **Verified WORKFLOW_DEFECT / GATEA_PROVIDER_MISSING.** The current code fails closed; do not call the production Gate A PASS. |
| Historical Gate A bridge evidence | Existing read-only bridge Run `38185460895` completed at branch `tmp/gatea-golden-fingerprint-bridge-20261011`, head `90073c8537b1f7f05ef9c0635b1a77a6dd8cae4f`, conclusion `success`; all 27 jobs succeeded. | [Run 38185460895](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/38185460895); workflow blob `7070f168e2c66ccffff5409d517aca25c86f9d0d). | Aggregate job log literals: `"status": "PASS"`, `"trials": 11005`, `"daily_rows": 22546465`, `"mismatches": 0`; actual and golden globals both `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`. | **PASS for this read-only historical comparison only.** It rehashes existing Stage 7/10 golden artifacts against Stage 12; it does not supply or connect runtime Gate A arguments. |
| Gate A artifact identity | Latest audit run artifact `11718779874`, ZIP digest `sha256:69f2886e001711b7e4319f510288e09177e40aa22990ef795d30ae119e553726`, with expiry `2026-11-10T23:47:54Z` as returned by GitHub. | Run `38185460895`, exact run metadata and artifact list. | The artifact is labelled `gatea-full-fingerprint-bridge-report`; 25 per-scenario evidence artifacts were also listed for this run. | Historical evidence is available for audit; it is **not assumed to be a durable provider** or bound into the production caller. |
| Golden coverage vs approved new checkpoint schedule | `docs/stage11/dataset_identity.json` says 25 scenarios / 11,005 canonical trials; Stage 7 range `[1,450]`; Stage 10 range `[451,550]`; source `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`; master seed `20270101`. | Dataset identity blob `72a481d509d39820fba78732724fde4fa9f25134`; D-2026-10-10-01 / Amendment-01. | The decision says non-C100 checkpoints escalate `300→600→1200→2400→4800→9600→...` and Gate A matches the approved reference/golden. The existing Stage 7/10 historical fingerprint bridge covers canonical IDs through 550 (C100 uses ID 1). | **UNDEFINED_BUSINESS_RULE / PENDING_APPROVAL for checkpoints beyond currently evidenced golden coverage.** The evidence does not establish an approved golden for IDs 551 onward. Do not manufacture hashes, extend coverage, invent a prefix-only rule, or infer permission from a prior audit PASS. Clarify an approved comparison/identity policy before any production extension. |
| Stage 12 historical ledger | Roll-forward validation is recorded `overall_result="PASS"`, 25 scenarios, 11,005 trials, 22,546,465 daily rows, official global SHA above. | `docs/stage12/roll_forward_validation.json`, blob `6084e8f68fa649fcf0726daa04f41ae9b0636706`. | The file ties the historical data to Run `37964656154` / head `0156c5f4272eb0ca7e32442657d0df9eaf4973d3` and pinned source SHA. | **Historical evidence verified as recorded.** It does not remove current source drift or substitute for a live Gate A provider. |

## Exact read-only Gate A run record

- Run: [38185460895](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/38185460895)
- Exact tested head: `90073c8537b1f7f05ef9c0635b1a77a6dd8cae4f`
- Jobs: `27/27 success` (unit parser test, 25 scenarios, aggregator).
- Scenario coverage: `25/25`; exact trial comparisons: `11,005/11,005`; daily rows: `22,546,465/22,546,465`; hash mismatches: `0`.
- Actual map SHA-256 = source-golden map SHA-256 = official CP12 global SHA-256: `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`.
- Full report artifact: `11718779874`, `sha256:69f2886e001711b7e4319f510288e09177e40aa22990ef795d30ae119e553726`.
- Historical Stage 10 metadata had a source-proven literal backslash+n suffix and an identity-summary formatting deviation; the audited bridge discloses these, validates them, and only normalizes the malformed suffix in memory. The immutable original artifacts were not edited.
- This was an existing read-only audit run, not launched by this CP and not a simulation/Monte Carlo/trial/checkpoint run.

## Classification and next permitted action

| Finding | Classification | Consequence | Minimal safe next action |
|---|---|---|---|
| `daily_engine.py` differs from the pinned source. | `K_CODE` / source identity blocker | Stage 7 source-boundary preflight will reject the current model-tree identity if executed at current HEAD; historic outputs remain tied to the old source SHA. | Preserve current SHA and data; obtain an explicit identity-preserving decision before any source pin/model-tree change or dataset extension. |
| Production caller does not provide approved exact-golden evidence. | `WORKFLOW_DEFECT` / `GATEA_PROVIDER_MISSING` | Runtime Gate A stays BLOCKED; no statistical stability claim is admissible. | Design/validate a provider using the existing trusted references only, once the checkpoint coverage rule and accepted provider/artifact identity are explicitly resolved; do not add golden coverage by inference. |
| Approved policy escalates past current documented golden range. | `UNDEFINED_BUSINESS_RULE / PENDING_APPROVAL` | An N=600-or-later full-prefix exact-golden PASS cannot be claimed from goldens documented only through N=550. | Obtain a scoped decision specifying the comparison contract and whether new golden coverage is authorized; until then keep the affected production extension blocked and continue independent tasks. |

## Boundary and status

No source, reference, test, workflow, state, historical artifact, Parquet, Trial ID, sample, seed, or production output was changed or generated in this review. `main` remains `647c19826b90d8224ce73ef9b90c306a45e03fb0`; `main/state.json` remains blob `2178260bb18efeb81437486f13b6d10cf5e85936`, stage `12-CLOSED`, repository status `FINAL_DELIVERY_BLOCKERS_OPEN`, and `sha_semantics=parent_state_commit_pointer`. The CP-R4 authoring-only test result remains independently verified at candidate SHA `09e66f203915609e3e5a199a11be6a1be890b1d6`; it does not authorize production execution or PR merge.

**Status:** `CP-SOURCE/GATE-A READ-ONLY REVIEW COMPLETE; PRODUCTION GATE A BLOCKED; SOURCE_SHA_DRIFT VERIFIED; PROJECT REMAINS PARTIAL`.
