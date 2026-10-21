# R4 — Candidate-only regression CI for Gate B near-zero threshold — 2026-10-21

- Base/main HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- Candidate branch: `tmp/cp-gateb-ci-near-zero-20261021`.
- Code tested: `run_batch.py` blob `00ae8901af5e57799c31680fa54a06ffb7a1997c`.
- Test commit before CI declaration: `bb37fae659b1baf00d1322d32e07a1b5af41a807`; test blob `17a9b07e739243c1bb052b5c6b46385a207d0800`.
- Scope: add a candidate-branch-only workflow that installs repository requirements, compiles `run_batch.py` and `scripts/stage7_stability.py`, and runs only `tests/test_run_batch.py`. It checks out exact `github.sha`.
- Coverage: positive/negative means inside the strict near-zero boundary, exact boundary behavior, relative epsilon for ordinary means, and a deterministic synthetic counterexample where half-CI lies between the corrected relative limit and the old absolute floor.
- Workflow restrictions: read-only token (`contents: read`); this branch only; no production workflow, no Monte Carlo, no Trial/Checkpoint, no Golden expansion, no Parquet writing.
- Owner authorized focused tests and all necessary work on temporary branches. This R4 limits this workflow to deterministic local unit-test evidence only.
- Acceptance: successful run against the exact SHA containing code and tests. If Actions cannot run, report `NOT_CI_VALIDATED`.
- Excluded: unrelated tests, production workflow, main, source SHA, state, model/data/cohort/trial identity, merge, PR closure, release, delivery acceptance.


## Exact-SHA CI result

- GitHub Actions Run: `39675170837`; URL: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39675170837
- Tested commit SHA: `7b16d5f96e801156a77d1a2975ec8f0fc1f3edfc`; conclusion `success`; status `completed`.
- All job steps passed: checkout of exact SHA, Python setup, dependency installation, compile of target modules, and `python -m pytest -q tests/test_run_batch.py`.
- Test coverage checks negative and positive near-zero means, the exact epsilon boundary, a non-near-zero mean of 10, and a synthetic half-CI which lies between the old absolute floor and the correct relative limit.
- This is candidate-only focused CI; it is not a production Gate B checkpoint or statistical acceptance.
