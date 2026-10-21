# R4 — Integrated Stage 7/Gate B fail-closed fixes — 2026-10-21

## Scope, baseline, and authority

- Repository: `yasmin977209-ux/motorcycle-simulation`
- Base `main` HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`
- Candidate branch: `tmp/cp-stage7-gateb-guards-integration-20261021`
- Classification: `K_CODE + K_TEST + K_WORKFLOW (candidate-only, focused deterministic verification)`
- Owner authorization: explicit in conversation on 2026-10-21 to continue all necessary project work after being asked to add candidate-only regression tests; no authorization to merge to `main`, change production identity/data, run Monte Carlo/Trials/Checkpoints, or release.

## Baseline defects (live source)

1. `scripts/stage7_stability.py` base blob `468b96b7b592a1ddd55cd4440962775632ab55a1`: `int(raw_n)` silently converts `300.9` to `300` and accepts boolean `True` as an integer checkpoint.
2. `run_batch.py` base blob `0418ddea818c194a5b582df94778fa5f13a3ecc4`: Gate B uses `bool(current_metrics[field_name]["stable"])`; nonempty string `"False"` therefore becomes true.
3. The same `run_batch.py` blob uses `max(CI_ABSOLUTE_EPSILON, CI_RELATIVE_TOLERANCE * abs(mean))` for every mean. At mean 10 this chooses limit 1 instead of the relative limit 0.1.

## Minimal integrated changes

- Require checkpoint `N` to be an actual Python `int`; reject floats, strings, booleans, `None`, and missing fields with `ValueError`. Existing valid integer checkpoint and legacy-intermediate behavior remains.
- In Gate B, require `stable` fields to be actual booleans; reject values including `"False"`, 0, 1, and `None`.
- Use the authoritative existing near-zero branch: `abs(mean) < constants.REFERENCE_EPSILON` means `CI_ABSOLUTE_EPSILON`; otherwise use `CI_RELATIVE_TOLERANCE * abs(mean)`. Keep the strict comparison `half_ci < limit`.
- Add focused deterministic tests in `tests/test_run_batch.py` for both changes.
- Add one candidate-branch-only GitHub Actions workflow that installs requirements, compiles the two relevant modules, and runs only `tests/test_run_batch.py` against `github.sha` with read-only repository permission.

## Explicit exclusions

No main writes, merge, PR closure, release, production workflow dispatch, simulation, Monte Carlo, Trial/Checkpoint, Golden/provider/source-SHA edits, random seeds/RNG, cohort/trial IDs, Parquet, historical artifacts, manifests, other tests, or policy changes. This CP does not define or change the stop/consecutive-transition rule and does not implement Confidence Sequences.

## Acceptance criteria

1. Valid integer checkpoints 300/600/1200/2400 and existing integer intermediate-history classification retain their prior behavior.
2. Malformed/missing N inputs fail closed.
3. Gate B accepts only actual `bool` values for all three metrics.
4. Near-zero mean on either side uses absolute epsilon; the exact boundary uses relative epsilon; ordinary mean 10 uses 0.1 relative limit.
5. A synthetic mean-10 sample with half-CI between 0.1 and 1 is unstable under the corrected rule.
6. Exact-SHA focused CI passes.
7. Confirm by compare/read-back that only the R4, two production source files, one test file, one candidate-only workflow, and continuity entry change.

## Status

`PENDING_VALIDATION`. No acceptance claim should be made until the exact combined candidate SHA passes CI and code/test blobs are read back.


## Exact-SHA integrated regression result

- Candidate CI Run: `39675573231`; URL: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39675573231
- Exact tested SHA: `04ac00d0163ca2ee352863141f09d7e3c1074645`; status `completed`, conclusion `success`.
- All steps passed: exact-SHA checkout, Python setup, requirements install, compilation, and focused `tests/test_run_batch.py`.
- Read-back before recording result: `run_batch.py` blob `bc6c3f7d3fbba742ab1f3d2c7dbaee5e827220f6`; `scripts/stage7_stability.py` blob `13872f6aa9405bc72532d32756979dc2c7e8695d`; `tests/test_run_batch.py` blob `476c2ab5e76d4b3c960f3f9a0df5a80f753486c4`.
- This is scoped candidate CI for the changed code and tests, not production Stage 7 execution, not a historical checkpoint, not Gate A acceptance, and not overall statistical stability.
- Disposition: `PASS_FOCUSED_INTEGRATED_CI`; no main write, merge, production run, or release.
