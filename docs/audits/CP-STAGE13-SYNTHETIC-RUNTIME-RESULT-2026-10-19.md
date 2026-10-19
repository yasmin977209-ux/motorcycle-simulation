# CP — Stage 13 synthetic runtime result and fixture-contract finding

**Date:** 2026-10-19  
**Status:** `RUNTIME_VALIDATION_FAILED / K_TEST_FIXTURE_CONTRACT_DRIFT`; no PASS claim.

## Exact run and artifact

- Workflow: `.github/workflows/cp-stage13-synthetic-compat-verify.yml`, temporary and scoped under owner authorization.
- Run: [39299680243](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39299680243), event `push`, branch `tmp/cp-stage13-excel-compat-20261017`, tested SHA `027e452e3af5a27de9f465b96c00255efa46e4f2`.
- Job `synthetic-verify`: ID `118221265867`; final conclusion `failure`.
- Artifact: ID `12209789284`, name `stage13-synthetic-compat-027e452e3af5a27de9f465b96c00255efa46e4f2`, 2,310 bytes, archive SHA-256 `4e741458667417697ae44c09f639a2dc2003d94d2893afc50204204f918ec170`. It was downloaded and opened; members are only `pytest.log` (6,363 bytes; SHA-256 `b32a20773100f099ab610e9d88f5829db3d9224cfecfb1b9df005bf878fbce86`) and `scope-metadata.json` (610 bytes; SHA-256 `81597c7b24faab5a04c291606e92173c8f50a251a0e8b597f89bcf2b9ada1d0b`). The workbook and synthetic audit JSON were not produced because the audit step failed early.
- Exact pytest result: **2 failed, 9 passed, 1 warning in 0.47s**.

## Failure analysis

Both test failures occur before their intended workbook/assignment assertions:

1. `test_assemble_185_sheets_and_five_representative_roles` fails with the literal error `RuntimeError: REPRESENTATIVE_DAILY_TRIAL_MISMATCH: C100_G100/P10`.
2. `test_incorrect_recorded_representative_trial_id_is_rejected` fails because the same daily-payload error is raised before the test reaches the intentionally corrupted P50 assignment.

The existing synthetic helper `tests/test_stage13_assembler.py::demo_data()` creates daily rows without `trial_id`, while the current validator correctly requires every daily row's `trial_id` to be an exact `int` matching the selected representative. The custom synthetic workbook/audit step called this validator on the same fixture and stopped for the same reason.

**Independent contract check:** a real Stage 9A `C050_G000` representative JSON was streamed read-only from the downloaded archive. Its daily records do contain integer `trial_id` values (the inspected P10 daily rows use `trial_id=131`). This supports classifying the observed test failure as `K_TEST / SYNTHETIC_FIXTURE_CONTRACT_DRIFT`, not proof of a real-payload defect. It does not by itself prove full Stage 13 runtime acceptance.

## Disposition

- Preserve Run `39299680243` as a historical failed validation; do not overwrite or relabel it.
- No test file was modified. Correcting `demo_data()` to stamp each daily row with its parent representative's `trial_id` requires a separate explicit approval because test modifications are protected. A corrected in-memory fixture could also be used for a separately authorized synthetic-only run, but must not conceal this failed run.
- The temporary workflow was removed after the exact run and artifact were inspected, as required by `OWNER_SCOPE_AUTHORIZATION_20261017.md`. Removal commit: `598488c2530c120d0f71fdf86322d3c7594b8145`. The branch itself remains.
- Stage 10 `write_json` remains only `ISOLATED_FUNCTION_CHECK_PASS` on candidate `47bcd45076f9a264307a30e5cddae51855ff2a42`; no repository test or Actions run was performed for that SHA.
- Candidate-only C050_G000 artifact-ID correction remains: manifest blob `ec0d4749f86c6f81d743dbb071f92e9f0eddef3d`, mapping the recorded Run `37662891608` to its Artifact `11503510055`. Main manifest and state are unchanged.
- Normative MaxCase selection is confirmed, but a distinct missing MaxCase still lacks a full daily payload in the inspected four-role source packages. No Trial was replayed, no daily rows were synthesized, and no payload was relabeled.

## Boundary

No production/historical dataset, Parquet data, model source, seed/RNG/sampling, cohort, trial IDs, reference, main, state, tests, merge, delivery acceptance or Release was changed. No Monte Carlo, Trial, Checkpoint or production workbook was run. Overall status remains `FINAL_DELIVERY_BLOCKERS_OPEN`.

The continuity ledger `docs/PROJECT_CONTINUITY.md` is not amended here because a prior append for a code CP was blocked by platform safety; no bypass was attempted. Register this report in `docs/continuity/SESSION_OUTPUTS.jsonl` after read-back.
