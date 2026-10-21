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
