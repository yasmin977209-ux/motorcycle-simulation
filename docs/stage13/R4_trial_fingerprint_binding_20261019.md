# R4 — Stage 13 adaptive per-trial fingerprint binding

- Date: 2026-10-19
- CP: `CP-STAGE13-TRIAL-FINGERPRINT-BINDING-2026-10-19`
- Candidate branch before change: `tmp/cp-stage13-adaptive-assembler-20261017`
- Candidate HEAD before change: `aba7766a7ac7fe3ce94946e1d9024de4852a0afd`
- Main HEAD: `647c19826b90d8224ce73ef9b90c306a45e03fb0`
- Normative reference SHA-256: `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`
- Scope authority: the owner-authorized Stage 13 adaptive assembler CP and synthetic regression scope recorded in `docs/stage13/R4_adaptive_cohort_assembler_20261017.md`. This R4 narrows to validating each adaptive trial digest against its TrialResult values. It does not authorize workflow edits, production runs, main changes, data/trial mutation, merge or Release.

## R4 — before change

| العنصر | الحالي | المرجع/القرار والفرع | النص الحاكم | الحكم |
|---|---|---|---|---|
| Per-trial digest binding | `scripts/stage13_assemble.py` blob `c082dbe7ce59233449e9a3af383840834234bbda`, function `_validate_adaptive_cohort`, accepts any 64-character lowercase SHA-256 in `row["result_sha256"]`; it then builds the ordered aggregate map from that field without recomputing it from the numeric TrialResult fields. The synthetic fixture hashes only `"synthetic|scenario|trial_id"`, independent of the outcome values. | Existing source-backed hash definitions on `main`: `scripts/stage7_run_trial_block.py` blob `33527f198bafadcb7ac8d06b2a72e142deb268ac` and `scripts/stage12_gateb_n600_audit.py` blob `dd9b4c738e065f4f62139efe131df75c37f41dac`. | Stage 7 computes SHA-256 over the canonical JSON of `asdict(TrialResult)`; the Stage 12 `row_sha` uses the same UTF-8 JSON encoding, sorted keys, compact separators, `default=str`. The Stage 13 adaptive R4 requires trial identities/fingerprints to remain bound and rejects missing/invalid per-result hashes. | **K_CODE — candidate-only integrity gap:** the aggregate digest commits to supplied per-row hash strings, but those strings are not proven to commit to the actual row values. A row metric could change while retaining its old digest, and a manifest built from those detached digests would still satisfy the current aggregate-map comparison. This is source inspection, not evidence that any production artifact was tampered with. |
| Adaptive input schema | Adaptive trial rows require `scenario_id`, `trial_id`, metric fields and `result_sha256`; the existing validator does not enforce the exact TrialResult field set. | `monte_carlo.py` at main blob `a8c3603487f92d3e15c3d754ce3faee3580a5f46`, `TrialResult` dataclass, and the exact source-backed hash implementation above. | The hash must be recomputed from the 18 canonical TrialResult fields (excluding the separate `result_sha256` field). | **K_CODE:** add exact field-set validation for adaptive row payloads and recompute the digest before including it in the ordered map. Do not hash the digest into itself or invent an alternate encoding. |
| Scope and test gate | Existing adaptive synthetic Run `38995349182` passed on tested SHA `3fdcdf8d006eff8f4a8fabb9ea2feb5c70c81633`; this does not include the new hash-binding assertion. The previously approved temporary workflow was removed after that evidence was inspected. | Owner-authorized Stage 13 adaptive candidate CP; current branch `tmp/cp-stage13-adaptive-assembler-20261017`. | Focused synthetic tests only; no production Monte Carlo/trials/checkpoints. Do not change workflow files without separately scoped authorization. | Code/test changes are candidate-only. Re-running tests is **PENDING** unless a permitted branch-pinned execution path is available; do not claim a pass from the prior SHA/run. |

## Minimal candidate change proposed

1. Define the exact 18 TrialResult field names from the source-backed dataclass.
2. For every adaptive row, require those fields plus exactly one separate `result_sha256` field.
3. Recompute SHA-256 from the canonical JSON of only the 18 TrialResult fields using the existing source serialization contract. Reject a mismatch before building `ordered_trial_hash_map_sha256`.
4. Update synthetic fixture rows to include the full TrialResult schema and compute digests using the same canonical algorithm.
5. Add a synthetic regression test that changes an outcome field without changing the digest and expects fail-closed rejection.
6. Inspect/read back the candidate diff. Do not alter thresholds, stop counts, cohort IDs, source SHA, seed/RNG, any completed trial, data/Parquet, reference, main, state.json on main, Workflows, PR state, or Release.

## Acceptance and status

- A correct row digest is recomputed from the exact TrialResult values and contributes to the ordered hash map.
- Any tampered TrialResult value with a stale digest is rejected, as are missing/extra result fields and malformed digests.
- Existing synthetic adaptive tests and the new regression must pass on the exact amended candidate SHA before this CP can be called tested.
- The previous `38995349182` success remains historical evidence for its exact earlier SHA only.
- No production execution or protected-state changes are authorized by this R4.

**Pre-change status: R4 RECORDED; implementation not yet changed.**
