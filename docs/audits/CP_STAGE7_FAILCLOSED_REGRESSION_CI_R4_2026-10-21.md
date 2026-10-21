# R4 — Candidate-only regression CI for Stage 7 fail-closed guards — 2026-10-21

- Base/main HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- Candidate branch: `tmp/cp-stage7-failclosed-type-guards-20261021`.
- Code tested: `scripts/stage7_stability.py` blob `13872f6aa9405bc72532d32756979dc2c7e8695d`; `run_batch.py` blob `3acc9bdc27694b2fef3925e05f4eaba5a110ddef`.
- Test commit before CI declaration: `a3e03da48a73e885244abd56ceba3d9fe51db97e`; test blob `27e2f796b3ee7b7bec5ee00c749878b855939daf`.
- Scope: add a candidate-branch-only workflow that installs pinned repo requirements, compiles only the relevant modules, and runs `tests/test_run_batch.py`. It checks out `github.sha` (not main or a moving branch).
- Test coverage: approved integer doubling checkpoints; rejection of fractional/integral floats, strings, bool, None, and missing N; actual Boolean acceptance; rejection of string/number/None Gate B stability values across each of the three fields.
- Workflow restrictions: read-only GitHub token (`contents: read`); trigger only on this candidate branch; no workflow dispatch into `stage7-full-run`, no Monte Carlo, no Trial/Checkpoint, no Golden lookup/expansion, no Parquet writing.
- Exact scope requested by owner and accepted in chat on 2026-10-21: maintain `tests/test_run_batch.py` candidate-only and run focused regression tests without changing main. This R4 records the additional technical execution needed to validate those tests.
- Acceptance: a successful run on an exact SHA containing both code and test changes. If Actions are disabled or the run cannot execute, status must stay `NOT_CI_VALIDATED`.
- Excluded: other tests, any production workflow, `state.json`, source SHA, model/data/cohort/trial identities, main, merge, PR closure, release, delivery acceptance.


## Exact-SHA CI result

- GitHub Actions Run: `39675160043`; URL: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39675160043
- Tested commit SHA: `17d91b3f4ea8bc8579edf017de81e91199d107ae`; conclusion `success`; status `completed`.
- All job steps passed: checkout of exact SHA, Python setup, dependency installation, compile of `run_batch.py` and `scripts/stage7_stability.py`, and `python -m pytest -q tests/test_run_batch.py`.
- This is candidate-only focused CI evidence. It does not authorize merge, production simulation, Gate A, or delivery acceptance.
