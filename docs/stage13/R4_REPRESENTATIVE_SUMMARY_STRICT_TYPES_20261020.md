# R4 — strict representative-summary field types

**Date:** 2026-10-20  
**Mode:** Candidate-only validator hardening. No test/workflow edits, source/data changes, production run, or workbook build.

## R4 record

| Item | Current state | Governing source | Branch / SHA | Defect class | Minimum change | Authority | Acceptance | Risk |
|---|---|---|---|---|---|---|---|---|
| Representative summary value comparison | `_validate_representatives` compares payload values to the canonical TrialResult row using value equality, except for booleans. Python considers `1.0 == 1` true; an integer-money field could therefore be represented as a float in a payload and still pass the binding check. | Original reference and project accounting rule requiring integer YER; live `monte_carlo.TrialResult` schema in `monte_carlo.py` blob `a8c3603487f92d3e15c3d754ce3faee3580a5f46` types currency/count fields as `int` and collection probability as `float`. | Candidate `tmp/cp-stage13-integration-20261020`; main remains `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`; current assembler blob `4472547232ffef95d15c864b7bf1128a6f868301`. | `K_CODE` | Require both exact Python type equality and value equality for every payload summary field against the canonical TrialResult row. Do not coerce or round values. | Narrow validator correction under engineering delegation; tests/workflows are not changed because test changes require separate scoped authorization. | Existing focused Stage 13 synthetic/compatibility suite passes on the exact changed SHA; existing test cases cover representative row binding and financial drift. Run evidence must be read back by exact SHA. | Low: JSON summaries and Parquet TrialResult records are serialized from the same TrialResult field types; strict type equality prevents numerically-equal but schema-inconsistent payload values. Failing closed is preferable to silently accepting floats as money. |

## Required behavior

- Keep exact schema equality and Trial ID binding.
- For each field in the representative summary, require `type(actual_value) is type(expected_value)` and `actual_value == expected_value`; no special numeric coercion.
- Keep current financial integer selection rules, approved five-role contract, and fail-closed behavior.
- The only changed source file will be `scripts/stage13_assemble.py`; no tests, Workflows, references, manifests, historical data, source identity, cohort, trial IDs, or `main` are changed.

## Status at R4 creation

**Not yet applied.** Test/read-back status pending. This does not clear Gate A, source byte identity drift, unresolved Stage 11 topology, C050_G000 R4-scope conflict, missing daily Partner memo source fields, final file acceptance, or Release authorization.
