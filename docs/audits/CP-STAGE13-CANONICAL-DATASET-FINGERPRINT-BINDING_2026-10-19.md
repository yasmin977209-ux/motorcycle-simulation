# CP Stage 13 — canonical fingerprint binding (2026-10-19)

## Result
Candidate-only implementation and tests were written and read back. Runtime verification is **PENDING/BLOCKED**; no tests or workbook generation were run. No Workflow was changed or triggered.

## Current identities
- Candidate: `tmp/cp-stage13-excel-compat-20261017`, HEAD `adfc04dd5a2b633c64515a0b4e4f7ae7b5ca1156`.
- Main: `7c41ac64c4b599f4e1d6a50be055f82cdd87a7b5`; common base `647c19826b90d8224ce73ef9b90c306a45e03fb0`. Candidate compares as diverged, 22 ahead / 2 behind. Not rebased or merged.
- As-read-back candidate blobs: `scripts/stage13_assemble.py` `4cb4632fe787c92ee87190769bbbf05b65b61416`; `tests/test_stage13_assembler.py` `976ebc8365db7f2380f15317c677990e34a1269c`.
- Pre-edit R4: `docs/stage13/R4_canonical_dataset_fingerprint_binding_20261019.md`, blob `a9aff6985109fa66ca0bfd0ec72445dfcceeed57`.
- Trusted Stage 11 identity blob: `72a481d509d39820fba78732724fde4fa9f25134`. Main state remains blob `2178260bb18efeb81437486f13b6d10cf5e85936`, stage `12-CLOSED`, `FINAL_DELIVERY_BLOCKERS_OPEN`, source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`.

## Finding and correction
Canonical mode previously checked source label, scenario/Trial ID coverage and 11,005 rows, but not whether financial/result values matched the approved per-scenario hashes. A changed value could retain its scenario and Trial ID and pass structural checks. Classification: `K_CODE`; no assertion that historic data is corrupted.

The candidate now verifies the exact Git blob of the pinned `docs/stage11/dataset_identity.json`, validates its provenance/count/coverage, and computes per-scenario fingerprints using the existing Stage 7/10/12 canonicalization. C100 scenarios compare against their single-trial `scenario_fingerprint_stage9a`; non-C100 compare IDs 1..550 against `combined_dataset_fingerprint_sha256_stage10`. The 9,005-trial Stage 9A global SHA remains only provenance for that baseline and is not treated as a fingerprint for all 11,005 trials. Enforcement applies only to canonical mode; sample, demo and adaptive modes remain separate.

A read-back review caught and corrected the recorded Run ID values being strings rather than integers. Synthetic test definitions cover pinned identity, altered identity rejection, canonical float/newline hashing, matching data, mutated financial value rejection, and canonical-path integration. 30 test functions are present with no duplicate names based on source inspection; this is not a test run.

## Authorization and blockers
The branch's owner-authorization note and clean-main R4 disagree on whether a temporary test Workflow can be reused. The project rule does not treat a candidate-branch statement alone as proof of owner approval, so pytest and physical workbook inspection remain pending. No Workflow was created/edited/triggered. No `main`, state, reference, source/seed/RNG, sampling/cohort/trial IDs, historic data, production output, merge or Release changed.

Next step: resolve the exact-branch test-workflow authorization or use a verified already-approved non-workflow path; then test the exact candidate SHA and inspect the workbook/artifacts. Do not merge or create a Release.
