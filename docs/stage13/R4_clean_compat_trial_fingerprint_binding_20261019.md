# R4 — Stage 13 clean-main compatibility candidate: per-trial digest binding

- Date: 2026-10-19
- Candidate branch before change: `tmp/cp-stage13-excel-compat-20261017`
- Candidate HEAD before change: `d253490a1627c0e453f4bf647b64369addee4dbc`
- Base/main: `647c19826b90d8224ce73ef9b90c306a45e03fb0`
- Normative reference SHA-256: `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`
- Scope: candidate-only Stage 13 adaptive cohort fingerprint validation and synthetic regression tests, under the existing Stage 13 assembler/Excel compatibility R4. No workflow edits, runtime execution, production simulation, source/RNG/seed/sampling changes, historical data changes, main changes, merge or Release.

## R4 — before change

| العنصر | الحالي | المرجع/القرار والفرع | النص الحاكم | الحكم |
|---|---|---|---|---|
| Per-trial digest binding | Candidate assembler blob `c082dbe7ce59233449e9a3af383840834234bbda` validates the lowercase SHA-256 shape of each adaptive row's `result_sha256`, then aggregates those supplied strings without recomputing them from the row's TrialResult fields. Its adaptive synthetic fixture uses a digest of scenario/trial ID independent of result values. | Main source-backed definitions: `scripts/stage7_run_trial_block.py` blob `33527f198bafadcb7ac8d06b2a72e142deb268ac`; `scripts/stage12_gateb_n600_audit.py` blob `dd9b4c738e065f4f62139efe131df75c37f41dac`; `monte_carlo.py` blob `a8c3603487f92d3e15c3d754ce3faee3580a5f46`. | SHA-256 is computed over canonical JSON of the exact `TrialResult` dataclass / same source-defined row payload using UTF-8, sorted keys, compact separators and `default=str`. The Stage 13 adaptive contract requires per-trial fingerprints and the ordered trial-hash map to be consistent with the actual trial values. | **K_CODE:** the aggregate map can be internally consistent while a supplied row digest is detached from its financial values. No production tampering is inferred. |
| Trial-result schema | Test blob `eb8e87be963665bf856ef35e92f1a21601f92128` builds abbreviated synthetic TrialResult-like rows and synthetic identifiers, not source-defined TrialResult digests. | `monte_carlo.TrialResult` and source hashing on main. | For the adaptive mode, require exactly the 18 defined result fields plus a separate `result_sha256`; recompute before including the row in the ordered map. | **K_CODE/K_TEST:** extend the fail-closed validator and synthetic fixtures; no business rule or threshold changes. |
| Test/workflow scope | Existing candidate R4 allows focused synthetic tests, but the prior temporary workflow-authorization records conflict about whether that workflow can be reused on this branch. | `docs/stage13/OWNER_SCOPE_AUTHORIZATION_20261017.md` vs `docs/stage13/R4_clean_main_excel_compat_20261017.md` on this candidate branch. | No workflow edit until the record conflict is resolved by a clear scoped decision. | Code/test edits only. Exact-head runtime test status will remain PENDING/BLOCKED unless an already-authorized path is available. |

## Minimal change

1. Add the 18-field TrialResult schema and source-compatible digest recomputation to the assembler.
2. Fail closed on missing/extra fields and digest mismatch before calculating the aggregate map.
3. Update synthetic adaptive rows to use a real `monte_carlo.TrialResult` object and matching source hash serializer.
4. Add regressions for changed outcome with stale digest and missing TrialResult field.
5. Do not change the workflow files, public Excel API, worksheet order/content, cohort identity, source/seed/RNG, historical data, main or main state.

## Acceptance

Correct synthetic rows must pass; changed values with stale hashes, missing fields, or extra fields must fail closed. The code/test read-back alone is not runtime verification. Do not claim PASS until the exact amended candidate SHA is tested through an explicitly permitted path. The prior Run `38995349182` remains evidence only for its earlier exact SHA.

**Pre-change status: R4 recorded; candidate implementation not yet modified.**
