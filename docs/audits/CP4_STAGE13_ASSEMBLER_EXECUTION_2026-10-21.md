# CP4 — Stage 13 assembly-contract execution report — 2026-10-21

**Status:** `PARTIAL / MISSING_EVIDENCE / CONFLICTED`  
**Base/main:** `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`  
**Pre-continuity candidate code/test SHA:** `6156462460b3b6a7fb192e675e3d162c59b71f98`  
**Branch:** `tmp/cp-path4-stage13-guard-20261021`  
**No main changes; the continuity commit after the candidate changes is documentation-only.**

## R4 and minimum engineering scope

- Pre-change record: `docs/audits/CP4_STAGE13_ASSEMBLER_R4_2026-10-21.md`, blob SHA `8b91ae6755c46f15eb5912bc79823606837d105b`.
- New assembler boundary and pure validation helpers: `scripts/stage13_assemble.py`, blob SHA `b459d0c6a99e50f545c25a09ca38cf1329f6ea6d`.
- Orchestrator adapter: `scripts/excel_builder.py`, blob SHA `daaaacb2e43954b77b01fdab7ef0dfa5b69e42d4`.
- Synthetic contract tests: `tests/test_stage13_assembly_contract.py`, blob SHA `bb59c1af2a80fa7dbebe617e767308d904968f2c`.
- Temporary branch-pinned workflow: `.github/workflows/cp-path4-stage13-guard-20261021.yml`.
- Live comparison showed the candidate remains a descendant of the exact main base and contains no manifest or historical-data file change. The assembler now owns ordered sheet assembly and post-save XLSX inventory/formula/error/hash checks, through injected helpers. The orchestrator validates role assignments and payload identity before workbook construction.

## Fail-closed representative contract

- Required roles follow the current recorded five-role set: `P10`, `P50`, `P90`, `LossCase`, `MaxCase`.
- The implementation rejects non-exact role keys, bool/float/non-positive trial IDs, missing/duplicate canonical bindings, summary/daily scenario or trial mismatches, incomplete or duplicate payload labels, and absent role-to-payload mapping.
- No MaxCase selector, alias from `Loss`, new payload filename, or manifest amendment was inferred. Consequently current canonical inputs are expected to remain blocked until their five-role assignments and payload mapping are resolved against authoritative evidence. This is intentional, not evidence that the actual artifact has passed the five-role contract.

## Validation / Runs / Artifacts

| Criterion | Status | Evidence |
|---|---|---|
| R4 before edits | PASS_SCOPED | R4 report above |
| Candidate branch/base/path inventory | VERIFIED | Live main-to-branch compare; branch based on exact main SHA |
| Synthetic tests run locally | NOT_RUN | No local repository checkout/dependency environment available |
| GitHub Actions Run ID / conclusion / tested SHA | MISSING_EVIDENCE | Combined commit-status query on the candidate returned an empty status list; exact workflow-run listing was not available via the connected GitHub action surface |
| Artifact `cp4-stage13-contract-evidence` and hashes | MISSING_EVIDENCE | Run and artifact contents have not been read back |
| Production workbook build and 185-sheet real artifact | NOT_STARTED | No production input or output was opened/generated in this CP |

No PASS is claimed for synthetic CI. The branch workflow is present, but its Run and artifact must be read back against the exact tested SHA before the test gate can be upgraded.

## Protected evidence unchanged

No changes to `main`, source/reference bytes, `SOURCE_SHA`, seed/RNG, cohort, trial IDs, dataset manifest, V3 metadata, Parquet, historical trial evidence, Gate A bridge, or delivery files. No production Monte Carlo, trial, checkpoint, workbook build, merge, or Release.

## Remaining blockers and next permitted action

1. Read back the exact run and artifact for the branch's last code/test SHA, including compile outcome, every test result, `tested_sha`, artifact identity, bytes, and hash.
2. Resolve the five-role assignment and role-to-payload mapping by owner/governing evidence before any canonical workbook build. The temporary V3 provenance decision does not settle `log_events` compatibility with the Gate A bridge, which remains conflicted/blocked.
3. Keep Stage 9C historical disposition `PARTIAL`; final delivery `NOT_ACCEPTED`; Release `BLOCKED / NOT_AUTHORIZED`.
