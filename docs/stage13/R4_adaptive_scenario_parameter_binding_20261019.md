# R4 — Stage 13 adaptive scenario/parameter identity binding

- Date: 2026-10-19
- CP: CP-STAGE13-ADAPTIVE-SCENARIO-PARAMETER-BINDING
- Candidate branch: `tmp/cp-stage13-excel-compat-20261017`
- Candidate HEAD before change: `c627b94230ccadca7552c835959a4299a10ac70e`
- Required base/main HEAD: `647c19826b90d8224ce73ef9b90c306a45e03fb0`
- Normative reference SHA-256: `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`
- Current source blobs: assembler `1548d4393cd79922abfd570f1c9a90454d7e40fe`; tests `68c64ea6a63c12b0cbc8602db44cdfa15d23c094`; main `monte_carlo.py` `a8c3603487f92d3e15c3d754ce3faee3580a5f46`.

## R4 — before change

| Item | Current state | Governing source/decision and branch | Controlling text | Ruling |
|---|---|---|---|---|
| Scenario/parameter identity | `_validate_mode_and_identity` checks that each row's `scenario_id` matches the enclosing scenario key. `_validate_adaptive_cohort` validates the 18-field row schema and recomputes the row digest, but it does not check that `collection_probability` and `recovery_rate_pct` encode that scenario. | Original reference §14.1, SHA-256 above; main `monte_carlo.py` `TrialResult` schema. | The scenario matrix identifies the collection probability and guarantee-recovery percentage in the scenario ID; e.g. C085_G100 is 0.85/100. `TrialResult` stores `scenario_id`, `collection_probability`, and `recovery_rate_pct` as separate fields. | `K_CODE`: a row can be labeled with one scenario while its actual parameter fields encode another. A correctly recomputed row SHA and internally consistent ordered-map fields do not establish this semantic correspondence. No evidence of actual production data corruption is inferred. |
| Adaptive digest | The digest is over the exact 18 fields and is checked before a trial hash is included in the ordered map. | Existing R4 fingerprint-binding correction on this candidate. | Keep the canonical JSON digest; this CP must not weaken the digest/schema check. | Preserve. |
| Scope and test boundary | Stage 13 candidate-only assembler and synthetic test files; no production test workflow is being changed. | Existing Stage 13 R4 bounds code/assembler and synthetic regression changes; the compatibility branch's workflow authorization records conflict, so no workflow edit or trigger is in this scope. | Validate structural identity fail-closed; do not alter source SHA, seed/RNG, cohort, sample policy, historical data, main, workflow, merge or Release. | A narrow source/test correction is within the Stage 13 assembler regression scope; exact-head runtime execution remains `PENDING/BLOCKED` until a non-conflicting approved path exists. |

## Minimal authorized correction

For adaptive rows only, derive the expected collection probability and recovery percentage from the known scenario identifier and reject any row whose parameter values do not match. Reject booleans, non-numeric/non-finite collection probabilities, or non-integer/boolean recovery values rather than accepting Python's permissive equality behavior. Keep the exact TrialResult field set and digest recomputation intact.

Add synthetic regression coverage for a wrong collection probability and a wrong recovery percentage with the row digest and aggregate map recomputed consistently. This proves the validator rejects semantic mismatch rather than merely relying on a stale hash. Do not run simulation or generate trials to construct these fixtures.

## Acceptance criteria

1. All 25 known scenario IDs resolve to the parameter values specified by §14.1.
2. Correct synthetic adaptive rows remain accepted by existing validation; a scenario/parameter mismatch fails with a stable, explicit error before workbook creation.
3. Existing per-trial schema/digest validation and ordered-map comparisons remain unchanged.
4. No workbook is accepted on the strength of a claimed Gate A reference alone; this CP does not connect a provider or declare Gate A PASS.
5. No workflow file, main, state.json, source, seed/RNG, threshold, cohort IDs, historic Parquet/data, production trial, merge or Release is changed.

## Execution status before change

R4 is recorded before any implementation edit. Candidate code/test edits may proceed within the stated scope, but exact-head pytest remains pending: the available records conflict about whether the temporary test workflow approval applies to this branch. Do not edit/create/trigger a workflow to work around that conflict.
