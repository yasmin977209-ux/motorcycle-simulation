# R4 — Stability transition policy implementation
**Date:** 2026-10-17  
**Base main HEAD:** `647c19826b90d8224ce73ef9b90c306a45e03fb0`  
**Implementation branch base:** `e2b7ecb734ea3e9d121edac4ec79201e61404848` (governance-only branch head containing D-2026-10-17-06)  
**Normative reference SHA-256:** `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`  
**Scope:** Apply the owner-approved policy in D-2026-10-17-04, D-2026-10-17-05, and D-2026-10-17-06 without changing the approved reference, model engine, RNG, seed, or historical data. No production simulation is authorized by this R4.

## R4 matrix

| Item | Current implementation on main (evidence) | Reference / approved decision | Controlling text | Judgment |
|---|---|---|---|---|
| Minimum cohort incl. C100 | `constants.py` blob `88b3e7b5a509f8486597ac08dfc5acaf80d4d39b`: `C100_STATISTICAL_START_TRIALS=1`; `run_batch.py` blob `0418ddea818c194a5b582df94778fa5f13a3ecc4` rejects C100 unless exactly one trial; Stage 7 workflow blob `4bb3b8df6742f51087b45eed1b9200468f12ac60` sets `INITIAL_C100_TRIALS=1` and requires `len(results)==1`. | D-2026-10-17-04 and D-2026-10-17-06 on `tmp/cp-stability-transition-rule-20261017`. | “Every one of the 25 scenarios, including C100, must cover trial IDs 1..300”; “N=300 is coverage only”. | **K_CODE** — runtime restrictions contradict current owner decision. |
| First §2.5 comparison | `scripts/stage7_stability.py` blob `468b96b7b592a1ddd55cd4440962775632ab55a1` allows a first-point Gate A evaluation; there is no separate §2.5 transition evaluator. | D-2026-10-17-06, same policy branch. | “The first eligible §2.5 stability comparison is the actual per-scenario transition N=300 → N=600.” | **K_CODE** — N=300 must be recorded as coverage-only; first eligible pair is 300→600. |
| §2.5 metric set | `run_batch.py` `STABILITY_FIELDS` and the embedded `statistics(results)` in Stage 7 workflow each calculate only three equity/entitlement CI fields. `constants.py` already declares `REFERENCE_STABILITY_INDICATORS` as seven names, but no pairwise evaluator consumes them. | Reference §2.5 and D-2026-10-17-05/-06. | “كل المؤشرات التالية ... بين تشغيلتين متتاليتين”: P10/P50/P90 cumulative project profit, P90 final cash, probability of loss, P90 termination count, P90 held assets. | **K_CODE** — the seven-metric transition gate is missing and must be implemented separately from Gate A/Gate B. |
| Gate B P50 continuation | Main's `scripts/stage7_stability.py` does not implement the previously approved D-2026-10-12-01 P50 change trigger. | D-2026-10-12-01 in main DECISIONS_LOG.md, lines 136–157. | On non-C100 scenarios, compare P50 final equity only across actual 300→600 and 600→1200 transitions; change >5% (near-zero fallback per §2.5) requires continuing through N=2400. | **K_CODE** — implement as a separate Gate B continuation trigger; do not merge it with the seven §2.5 indicators or apply it to C100. The new first-pass stop rule ends a scenario when current applicable gates pass; only an actually observed P50 trigger forces N=2400. |
| Thresholds | Constants already hold `REFERENCE_EPSILON=1e-6`, `ABSOLUTE_EPSILON=1`, relative threshold `0.01`; the Gate A function intentionally ignores these arguments because Gate A is exact-golden identity. | Reference §2.5; D-2026-10-17-05/-06. | Relative change strictly below 1%; when `abs(old_value)<1e-6`, absolute difference strictly below 1. | **KEEP UNCHANGED** — implement the seven-metric rule without repurposing or weakening exact-Golden Gate A. |
| Stop at first passing transition | `constants.py` sets `STABILITY_CONSECUTIVE_CHECKS_REQUIRED=3`; `run_batch.py` and Stage 7 workflow inspect the last three checkpoint records before declaring stable. | D-2026-10-17-04/-05/-06. | “stop ... at its first passing checkpoint”; “A prior failed transition is not a permanent blocker.” | **K_CODE** — current transition must be evaluated with all currently applicable gates; historical failed transitions stay in history but do not impose a 3-pass streak. |
| C100 independent check | Current runner separately executes C100 `trial_id=2` after the one-row result; workflow does the same and persists equality proof, not a full TrialResult row for that extra verification run. | D-2026-10-17-04/-06; no-completed-trial-rerun guard in project policy. | C100 must cover IDs 1..300; completed trial IDs must not be rerun or relabelled. | **K_CODE + migration HOLD** — use two already-persisted rows for the deterministic equality proof; never rerun ID 2 as a side-channel. If an old checkpoint has only row 1 and only a proof for the past standalone ID-2 run (without its full result row), fail closed rather than silently rerun or synthesize row 2. |
| Old unit-test expectations | `tests/test_stage1.py` blob `c7318e938ca66828107dbdb799c6826edf1a159f` encodes C100=1, +50/400 and 3 consecutive checks; `tests/test_stage7_authoring.py` blob `6a4e11399e2c6b85e9dc240a0c669f395a639e66` asserts C100 n=1 and a three-checkpoint requirement. | Current owner-approved decisions D-2026-10-17-04/-05/-06. | Same approved clauses above. | **K_TEST** — these expected behaviors must be revised and replaced with regression checks for the approved policy, not altered merely to hide test failures. |
| Static Stage 1 workflow checks | `.github/workflows/stage1-verification.yml` blob `003cad09294a541a95cc427443413585f93b4975` asserts the unchanged model/constants-layer C100=1, +50 legacy model constants, minimum stop 400, three legacy checks, and C100 CI disabled. Its commit content remains byte-identical to `main`; the approved Stage 7 schedule is now in the orchestration layer rather than `constants.py`. | D-2026-10-17-04/-05/-06, scoped to Stage 7 sampling and stopping policy; pinned model `SOURCE_SHA` boundary. | Stage 7 scheduler must start every scenario at N=300 and use eligible doubling transitions; model constants/Stage 1 calendar, RNG, and contract invariants remain unchanged. | **KEEP UNCHANGED** — not a workflow defect in this CP: Stage 1 must continue checking the unchanged model constants. Do not modify `constants.py` or that `main`-triggered workflow to make its legacy model constants impersonate Stage 7 scheduler policy. |

## In-scope implementation plan

1. Define the N=300 all-scenario cohort and first-passing-transition rule in the Stage 7 orchestration layer (`scripts/stage7_stability.py`, `run_batch.py`, and the embedded Stage 7 workflow). **Do not modify `constants.py`**: it is a pinned model-source file included in the SOURCE_SHA boundary. Leave its legacy C100 start constant and sampling map unchanged, and do not raise SOURCE_SHA to absorb orchestration-only policy work.
2. Add a pure seven-indicator summary and pairwise comparator using NumPy linear quantiles, the approved cumulative-profit loss definition (`cumulative_project_profit < 0`), the reference epsilon branch, exact N-doubling adjacency, and fail-closed handling of missing/non-finite metrics.
3. In `run_batch.py` and the embedded Stage 7 workflow, record N=300 as coverage-only and compare 300→600 first; afterward evaluate every actual adjacent per-scenario transition. Overall stability can be true only when the current applicable §2.5 transition passes together with required Gate A and applicable Gate B checks. C100's existing separate deterministic-equality proof remains separate; C100 CI behavior is not silently changed by this R4.
4. Preserve all earlier transition records. Do not require three consecutive passes; a later eligible passing transition is allowed to establish current stability while old failure records remain intact.
5. Update stale unit/static assertions only to match this R4; add synthetic tests that do not run simulations. Use a branch-pinned, test-only workflow if needed; it must not run Monte Carlo, must include job timeout/minimal permissions, must not use `workflow_dispatch`, and must be removed after the evidence is collected.
6. Do not run production checkpoints. Main state still records `GATEA_PROVIDER_MISSING` and `SOURCE_SHA_DRIFT`; source identity, seed, RNG, historical cohort, and completed trial IDs remain immutable until their separate gates are resolved. No merge, Release, final delivery, or main edit is authorized by this CP.

## Gate table before implementation

| Gate | Required evidence | Present evidence | Status before code changes |
|---|---|---|---|
| R4 completeness | every conflicting code/test/workflow rule compared with the reference/owner decision | Matrix above, backed by current-main file/blob reads and approved D-2026-10-17-06 | **PASS — R4 prepared** |
| Correct seven §2.5 metrics | exact seven fields, cumulative sample definitions, quantile method, near-zero rule, transition adjacency | Reference §2.5 + constants/aggregator source read; evaluator absent from runtime code | **FAIL — K_CODE, in scope to fix** |
| Gate A | connected approved-golden provider with proven scenario/trial coverage and source identity | `main/state.json` explicitly says `GATEA_PROVIDER_MISSING` | **BLOCKED — no production run** |
| Source identity | live source tree matches pinned SHA without silent SOURCE_SHA bump | `main/state.json` documents `daily_engine.py` drift from `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b` | **BLOCKED — no production run** |
| Historical-ID integrity | no duplicate execution, no synthetic row identity, exact source/provenance | C100's previous independent ID-2 result was recorded as equality proof only, not a persisted TrialResult in the main runner state | **HOLD for migrating that old C100 checkpoint; fail closed if full row is unavailable** |

**Explicit non-claims:** This R4 is not a test result or stability result. No production simulations, Monte Carlo, or full pytest have been run as part of preparing it. The approved 300-trial all-scenario execution policy belongs to orchestration; `constants.py`, all model source files, RNG, seed, and historical data remain byte-identical to their pinned identity.

## Implementation and verification evidence — CP-STABILITY-POLICY-IMPL-20261017

**Result:** PASS for static + focused deterministic regression on the exact tested SHA only; production stability remains BLOCKED by independent gates.  
**Main base:** `647c19826b90d8224ce73ef9b90c306a45e03fb0`  
**Implementation branch:** `tmp/cp-stability-policy-impl-20261017`  
**Tested SHA:** `3aa5b67693b9ecca2a4a51cc7e2bf47f50b10843`

### Exact test evidence

- GitHub Actions Run `38989548728`: success — https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/38989548728
- Job `117268651135`: success.
- `98 passed in 0.87s`; no production simulation, Monte Carlo checkpoint, or historical trial replay was run.
- Static checks: `compileall` PASS; YAML parse for Stage 7 and Stage 1 PASS; embedded Stage 7 orchestrator AST PASS; branch pin, permissions, and timeout boundary checks PASS.
- Artifact `12083839056`, name `cp-stability-policy-test-evidence`; ZIP size **3,368 bytes**; archive SHA-256 `ee09ced3dd29afd24a8040622759a967147ea2e5e1c022d87a49b4346b482721`; expiration `2026-10-31T01:08:30Z`.
- Artifact inventory: `cp-stability-policy-evidence.json` (2,015 bytes) and `policy-test-results.xml` (12,866 bytes). The embedded manifest identifies tested SHA `3aa5b67693b9ecca2a4a51cc7e2bf47f50b10843`, outcome `success`, `production_simulation_executed=false`, `source_sha_changed=false`, and `rng_or_seed_changed=false`.

### Content inspection / source identity

The downloaded Artifact ZIP was independently listed and read. Its digest matches GitHub's Artifact metadata. The JUnit XML contains the successful focused-suite result; the manifest's per-file SHA-256 values match the tested source tree recorded by the job.

- `constants.py` remained byte-for-byte identical to `main` (Git blob `88b3e7b5a509f8486597ac08dfc5acaf80d4d39b`); SHA-256 `675df03f651ce64cf06a1d70c185905261fdfd1357a507f00ac6c43125fbd607`, **16,776 bytes**.
- `.github/workflows/stage1-verification.yml` remained byte-for-byte identical to `main` (Git blob `003cad09294a541a95cc427443413585f93b4975`); `tests/test_stage1.py` remained byte-for-byte identical to `main` (Git blob `c7318e938ca66828107dbdb799c6826edf1a159f`). This preserves the pinned model/constants source boundary and existing calendar/RNG checks.
- The changed policy lives in the scheduler/orchestration files, not the model engine, constants, RNG or historical datasets.
- Temporary verifier Workflow `.github/workflows/cp-stability-policy-verify.yml` was pinned to this exact branch, used `contents: read`, had a 15-minute job timeout, no `workflow_dispatch`, and did not run Monte Carlo. It was removed after evidence collection; the branch itself was retained.

### Verification-tool failures encountered and disposition

These early runs failed before pytest and are classified `WORKFLOW_DEFECT`, not code-test failures:

- Run `38989216866`: exact error `AssertionError: embedded Stage 7 Python entrypoint heredoc not found`; verifier regex incorrectly required the heredoc to be the end of the whole shell step.
- Run `38989389427`: exact error `AssertionError: embedded Stage 7 Python entrypoint heredoc not found`; the production workflow uses `cat > /tmp/stage7_orchestrator.py <<'PY'`, not `python - <<'PY'`.
- Run `38989450332`: exact Python error `AssertionError` at verifier line 40; the boundary assertion inspected the production workflow's trigger instead of the temporary verifier's own trigger.

Fixes: explicit cat-heredoc boundary extraction and separate parsing of the temporary verifier's own YAML. Run `38989548728` then passed all static checks and focused tests. No test was skipped or represented as PASS in place of a failed test.

### Remaining gates (not closed by this CP)

- **Gate A production provider: BLOCKED** — an approved-golden provider with proven fingerprint coverage and source identity is still not connected.
- **SOURCE_SHA drift: BLOCKED** — pre-existing difference in `daily_engine.py` versus `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`; this CP did not raise `SOURCE_SHA`.
- Stage 11 topology, Stage 13 assembler, D-2026-10-12-01 state reconciliation, G2 runtime risk and the complete seven-file delivery audit remain open.
- The successful run is not a production run, Gate A PASS, `SCENARIO_STABLE`, final-delivery approval or Release.

