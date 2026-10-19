# CP — Stage 13 adaptive cohort: C100 policy conflict and Gate B evidence-state review

**Date:** 2026-10-19  
**Mode:** Read-only R4 review; no Stage 13 code/test/workflow changes.

## Live identities at review

- `main` HEAD: `647c19826b90d8224ce73ef9b90c306a45e03fb0`.
- Main `state.json` blob: `2178260bb18efeb81437486f13b6d10cf5e85936`; `12-CLOSED / FINAL_DELIVERY_BLOCKERS_OPEN`; source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`.
- Candidate: `tmp/cp-stage13-excel-compat-20261017`, HEAD `4fa2c633162b0134a48cfc2ccbf2b6b948108ae0`, base main above, compare 14 ahead / 0 behind, ten changed paths.
- Candidate `scripts/stage13_assemble.py` blob: `7561f73340ac45b0f4ab71b677c33b771eac008b`.
- Candidate `tests/test_stage13_assembler.py` blob: `f707dc9af12f01ca705b225f4a34df570f85210d`.
- Candidate `scripts/excel_builder.py` blob: `8dec3578a8221a6b12fb0915103cb09664f20a96`.
- Governance source: main `docs/governance/DECISIONS_LOG.md` blob `df4910e6a86bcce84f6b71d6d260913800474f95`; Amendments blob `b4eab80bf657d72e9e49d14db81d2baf0a462d77`.

## R4 — finding 1: adaptive Stage 13 treats C100 as a 600+ CI cohort

| Item | Candidate state | Governing decision / branch | Ruling |
|---|---|---|---|
| C100 adaptive trial coverage | `_validate_adaptive_cohort` requires `stable_at_n` to be an integer `>=600` for every scenario (assembler lines 867–879). It then requires contiguous IDs `1..stable_at_n` and an adaptive history beginning `N=300` then `600,1200,…` (lines 924–929). The synthetic helper defaults every scenario—including C100—to 600 trials; the test inventory explicitly covers that assumption. | Main `DECISIONS_LOG.md`, D-2026-10-10-01 (normative) says: “C100=1 ... بلا CI وبـtrial_id/بذور مختلفة”; the other scenarios C085/C070/C050/C030 start at 300 and double. Main Stage 7 Workflow blob `4bb3b8df6742f51087b45eed1b9200468f12ac60` sets `INITIAL_C100_TRIALS: "1"`, asserts “C100 primary sample must remain n=1”, and performs an independent verification using `trial_id=2` and a different seed. These are current main-branch evidence, not candidate business rules. | **Candidate `K_CODE/K_SPEC` conflict, proven by source comparison.** The Stage 13 adaptive validator rejects the normative C100 shape and instead demands CI-shaped coverage/history. A separate C100 determinism-evidence field does not remove the conflict because the same validator still requires at least 600 rows and checkpoint history. No actual production cohort corruption is inferred. |

### Protected boundary / decision required

Do not silently alter cohort semantics, trial-ID ranges, or sampling requirements. The existing project instructions make cohort and trial identity a protected area requiring separate scope approval. The next corrective change should be a narrowly scoped correction that makes the Stage 13 validator and synthetic fixture respect D-2026-10-10-01's C100=1 primary result plus independent trial-2 determinism proof, while keeping C100 outside CI and not mixing trial 2 into the primary cohort. This report does **not** authorize that edit or any trial/data generation. Obtain the required explicit scope authorization before touching those constraints.

## R4 — finding 2: ambiguous Gate B status handling in adaptive checkpoint history

At candidate lines 946–979, `gate_b_status` may be one of `PASS/FAIL/PENDING/BLOCKED`. Evidence reference/SHA is required only for PASS or FAIL. A non-final checkpoint whose Gate B status is PENDING/BLOCKED can continue through the history validator because the continuation rejection only checks a claimed `SCENARIO_STABLE` or the “all gates passed but first stop” condition. Final status still must pass.

D-2026-10-10-01 requires Gate B's CI criteria and three consecutive checkpoints to establish stability; D-2026-10-11-01/-02 also say missing/mismatched required analytical evidence must be held and must not claim Gate B PASS. But the records reviewed do not explicitly specify whether a missing historical `gate_b_status` at a non-final checkpoint should invalidate the entire later cohort or be treated as an evaluable failed checkpoint. Therefore this part is **`UNDEFINED_BUSINESS_RULE/PENDING_APPROVAL`**, not a proven permission to reinterpret or change the continuation contract. Preserve the current behavior until the owner issues a scoped ruling; in no case may PENDING/BLOCKED be represented as PASS.

## Verification and immutable boundaries

- The most recent R4 documents on this candidate already record that the workflow-authorization notes conflict: `OWNER_SCOPE_AUTHORIZATION_20261017.md` describes an exact-branch synthetic test workflow, while `R4_clean_main_excel_compat_20261017.md` says that prior workflow approval is not reused on this branch. The conflict remains unresolved. No workflow was created, edited or triggered to get around it.
- The earlier Run `38995349182` belongs to its own older tested SHA `3fdcdf8d006eff8f4a8fabb9ea2feb5c70c81633`; it does not certify current candidate HEAD `4fa2c633162b0134a48cfc2ccbf2b6b948108ae0`. No runtime test or workbook build on current HEAD is verified.
- Static positive observations remain limited to source inspection: per-trial digests are recomputed against the exact row fields; scenario parameters are checked against the scenario ID; Gate A checkpoint statuses are required to be PASS; final workbook source requires 185 exact sheet names/order and physical no-formula/no-Excel-error inspection. No workbook was built in this CP.
- No change to main, state, reference, source SHA, master seed/RNG, sampling/threshold/cohort/trial IDs, historical data/Parquet, or production artifact; no simulation/CLI/Trial/Checkpoint, merge, PR closure, or Release. PR #46 remains a separate open/draft/unmerged continuity PR.

## Disposition

**`STAGE13_READ_ONLY_R4_COMPLETE; C100_POLICY_CONFLICT_REQUIRES_SCOPED_AUTHORIZATION; GATE_B_PENDING/BLOCKED_SEMANTICS_PENDING_APPROVAL; CANDIDATE_NOT_RUNTIME_VERIFIED; NOT_READY_TO_MERGE`.**

Next permitted work: continue independent source-identity-neutral review. Correcting C100 validation requires specific scope authorization; the Gate B pending/blocked history semantics require a written owner decision before code changes.
