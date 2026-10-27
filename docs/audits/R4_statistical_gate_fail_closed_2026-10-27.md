# R4 — Statistical execution gate fail-closed defect (before repair)

- Date: 2026-10-27
- Classification: `R4 / K_CODE`
- Baseline `main` HEAD read before repair: `c6e54349a5e94f65d5aa9f83141f225d777bb474`.
- Failing tested source: `d08e2e7843a23c8ebea00080e8e2b362b97d6787`.
- Observed workflow run: [40531094349](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40531094349), job `122283775598`.
- Actual command: `python -m pytest -q tests`.
- Exit code: `1`.
- Recorded summary: `1 failed, 572 passed, 1 skipped, 1 warning in 290.27s`.
- Failing test: `tests/test_golden_provider_workflow_integration.py::test_statistical_gate_cannot_be_cleared_by_status_string_alone`.
- Failure: the test changed the contract status to `ACCEPTED_FOR_PRODUCTION`, set all three execution authorization fields to `True`, and changed every component status to `PASS`; `statistical_execution_status(path)` returned `authorized=True`, violating the test's `assert result["authorized"] is False`.
- The run produced no artifacts. The S6 matrix and aggregation jobs were skipped because preflight failed.
- No production trials, Monte Carlo checkpoint, source identity, RNG, historical dataset, Golden map, or release state is changed by this R4 record.

## Required minimal repair

Keep the test unchanged. In production code, a component's status string must not override its unresolved `blockers` or `implementation_gap`. The acceptance check must fail closed when any required component retains either field with unresolved content. This record captures the failure before repair; subsequent repair evidence must be appended separately and must not erase this result.

## Governing clauses read

- `0.20`: no result without actual execution evidence.
- `0.25`: preserve source/cohort identity and historical evidence.
- `2.5`, `14.2`, `14.11`, `21.2`, `21.3`: checkpoint schedule, sequential inference, Gate A/B and convergence restrictions.
- `21.5`, `23.5`, `25.6`: evidence manifests, workflow execution, source identity and historical separation.

Reference file SHA-256 verified locally: `e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f`.
