# R4 — Baseline control for four Stage 5 artifact-dependent acceptance tests — 2026-10-22

## Purpose and identity

- Base/current main HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- Candidate branch: `tmp/cp-stage5-full-suite-baseline-20261022`.
- Classification: `K_TEST_BASELINE / READ-ONLY CONTROL`.
- No production code or test source is changed. The only added files are this R4 and a branch-only verification workflow.
- Source test file at main: `tests/test_acceptance_16_v2.py`, blob `a93dba6435e0561f82600617ba6c658999409d59`.

## Observed failures in Stage 13 full-suite candidate

Full candidate Run `39685754846` reported `4 failed, 429 passed, 1 skipped`. All four failed tests are in `tests/test_acceptance_16_v2.py`:
- `test_127_تطابق_التسلسلي_والمتوازي`: missing `results_stage5/worker_equivalence_manifest.json`.
- `test_159_اختيار_التكرار_التمثيلي_حسب_Final_Net_Project_Equity_فقط`: missing `results_stage5/trials_summary.parquet`.
- `test_160_التكرارات_التوضيحية_الاربعة_تنتج_فعليا`: missing `results_stage5/trials_summary.parquet`.
- `test_161_DAILY_DISTRIBUTION_لكل_يوم_تقويمي_بلا_فجوات`: missing `results_stage5/daily_distribution.parquet`.

The current main recursive Git tree contains the test file but no `results_stage5/` paths or any of the three referenced output files. This suggests an external/generated-fixture dependency, but a control run must verify test behavior on main's unchanged source before calling the failures pre-existing.

## Exact allowed control

A candidate-only workflow will:
1. Checkout the exact SHA based directly on main.
2. Install `requirements.txt`.
3. Compile `tests/test_acceptance_16_v2.py`.
4. Run exactly the four named tests selected by `pytest -k`.
5. Upload stdout/JUnit and source identity even on failure.
It must not generate or download Stage 5 production data, run Monte Carlo or simulation, mutate repository tests, or skip/fix failures.

## Interpretation

- If the four tests fail with the same missing-file exceptions on this main-based candidate, classify them as existing fixture/data-environment failures outside the Stage 13 code diff; retain the Stage 13 full-suite result as `429 passed, 4 failed, 1 skipped`, not a full PASS.
- If main-based control passes, inspect exact tested files and fixture setup to determine whether the Stage 13 branch introduced a test-environment interaction.
- Do not create empty or fake Parquet files and do not alter assertions simply to make the run pass.

## Status

`PENDING_CONTROL_RUN`. This CP is diagnostic only; it does not amend main, generate production data, or accept the Stage 13 delivery.


## Baseline-control read-back

- Control Run `39686434487`, tested SHA `08d1ebedb0d970a9cde7afea5aebcebd4ed8a29f`, result `failure` as expected: exactly the four selected tests failed with the same missing-file paths; `159 deselected`; runtime `0.74s`. URL: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39686434487.
- The control branch is based directly on main. Test blob remained exactly `a93dba6435e0561f82600617ba6c658999409d59`; the identity artifact records no `results_stage5/` paths in the tested Git tree and `stage13_assembler_present=false`.
- Evidence artifact `12386996668`, name `stage5-acceptance-fixture-baseline`, size 4,587 bytes, API SHA-256 `aae5a1314d87a572c086b216fca91c9dbe6b598e0a16755d142dda02de3a93d9`. Downloaded ZIP matched the API digest; it contains the complete test log, JUnit XML, and source identity record.
- Classification: `BASELINE_TEST_FIXTURE_DEFECT_CONFIRMED`. These four full-suite failures are not introduced by the Stage 13 candidate. They must remain recorded; do not fabricate missing files or alter the assertions without a separate test-fixture repair scope.
- No simulation, Trial, Checkpoint, production data generation, source/test mutation, or main change occurred.
