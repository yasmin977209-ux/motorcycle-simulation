# R4 — Full repository regression pass for Stage 13 candidate — 2026-10-22

## Scope

- Current-main base at candidate creation: `7621ddefe6c971e9eb231eb2a987519c86a2cb51`.
- Candidate branch: `tmp/cp-stage13-clean-current-main-20261022`.
- Stage 13 source/test focused CI passed 54 tests on SHA `0a5c793f342266c1e0df91d3ca131e5cb2376ab7`, Run `39694032014`.
- This addendum authorizes a broader deterministic regression pass on the isolated candidate because `scripts/excel_builder.py` is replaced by the reviewed orchestration wrapper plus `scripts/stage13_assemble.py`. The test run is read-only with respect to production artifacts.
- Type: `K_TEST + K_WORKFLOW / CANDIDATE-ONLY`.

## Question

Do other repository tests import public or private names from the previous `scripts/excel_builder.py` implementation, or rely on behavior affected by the Stage 13 orchestrator extraction?

## Execution

A push-only workflow scoped to this branch will:
1. Check out exactly `github.sha`.
2. Install `requirements.txt`.
3. Run compile checks for the Stage 13 assembler/orchestrator/source-audit modules.
4. Run the repository's existing test suite via `python -m pytest -q tests`.
5. Upload only text test logs/JUnit summary and report the exact candidate SHA.

The workflow must not run any Monte Carlo batch, production simulation, Trial, Checkpoint, full P16 build, canonical artifact download, or workbook build from project data. Existing tests may create temporary synthetic fixtures in the runner's ephemeral workspace only.

## Acceptance

- If all tests pass, record the exact count and elapsed time with the run SHA and source/test blob IDs.
- If tests fail, retain the complete failure list and classify each failure as changed-file regression, unrelated baseline failure, or environment/workflow issue. Do not hide failures or rewrite tests simply to force green.
- A passing run is software regression evidence only, not Stage 13 production acceptance or overall final delivery acceptance.

## Explicit exclusions

No additional source, test, data, manifest, reference, policy, source SHA, seed/RNG, cohort/trial IDs, historical artifacts, main writes, merges, or releases. This R4 does not enable production workbook generation while missing Partner 1/Partner 2 memo balance inputs and C050_G000 provenance are unresolved.

## Status

`PENDING_FULL_SUITE_RUN`.


## Exact-SHA full-suite result

- Run: `39694421445`; tested SHA `f4d8dc0c304a5edc9592cde858f4fe756ba42f0c`; URL https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39694421445.
- Final result: **432 passed, 4 failed, 1 skipped in 243.13 seconds**; Python compilation and focused Stage 13 tests remained successful.
- Evidence artifact: `12390027512`, ZIP SHA-256 `785d96fec1092442e0f587376f56940b324f36c568213d3745c433669dc745a4`.
- Exact tested code blobs recorded by the workflow: assembler `47fc1828dfb0d298aa4528f58b558bf012882076`; Excel entrypoint `c5db5f1113294224d371e98bab2edd7b015a30d2`; MaxCase audit helper `f7835b5a6f2584f9a0679a496b565a5a229f6b4c`.
- All four failures are in `tests/test_acceptance_16_v2.py` and fail with `FileNotFoundError` for absent `results_stage5/worker_equivalence_manifest.json`, `results_stage5/trials_summary.parquet`, and `results_stage5/daily_distribution.parquet` (tests 127, 159, 160, 161). These files are not in the clean checkout/tree and are not produced by the Stage 13 test workflow. This run therefore cannot be described as a full-suite PASS; the observed failure class is `MISSING_TEST_FIXTURE_OR_EXTERNAL_STAGE5_ARTIFACT`, not a demonstrated Stage 13 implementation regression. The four failures remain visible and are not suppressed.
- Focused Stage 13 regression remains `54 passed` on exact SHA `0a5c793f342266c1e0df91d3ca131e5cb2376ab7`, Run `39694032014`. That scoped result is distinct from the non-passing repository-wide run.
- Disposition: `PASS_FOCUSED_STAGE13 / FULL_SUITE_NONPASS_DUE_MISSING_STAGE5_FIXTURES`. No tests were edited to mask these failures. Do not claim repository-wide CI green.


## Independent pre-port baseline confirmation

- Baseline-control Run `39686434487` on branch `tmp/cp-stage5-full-suite-baseline-20261022`, tested SHA `08d1ebedb0d970a9cde7afea5aebcebd4ed8a29f`, ran the four Acceptance 16 tests independently before the Stage 13 assembler was present; it failed on the same four missing Stage 5 paths. Run URL: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39686434487.
- Baseline-control artifact `12386996668`, SHA-256 `aae5a1314d87a572c086b216fca91c9dbe6b598e0a16755d142dda02de3a93d9`, contains `source_identity.json` stating `stage13_assembler_present=false`, `stage5_fixture_paths_in_git=[]`, and `production_data_generated=false`, `simulation_trials_or_checkpoints_run=false`.
- Its JUnit recorded 4/4 failures, all `FileNotFoundError` for those same paths. This is independent evidence the full-suite failures predate the Stage 13 port, not a new regression. No fixture/data was synthesized or inserted.
