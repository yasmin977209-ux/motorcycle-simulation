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


## Post-run and artifact read-back — 2026-10-21

**Disposition update:** the earlier `MISSING_EVIDENCE` finding for the synthetic test run is resolved. The *synthetic assembly-contract CI gate only* is now `PASS_SCOPED`; Stage 13 production assembly remains `BLOCKED / CONFLICTED` because the authoritative five-role-to-payload mapping is not resolved.

- Workflow: `.github/workflows/cp-path4-stage13-guard-20261021.yml`; exact relevant Run [39504576649](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39504576649); event `push`; branch `tmp/cp-path4-stage13-guard-20261021`; conclusion `success`; status `completed`; attempt 1. Run `head_sha` = tested SHA = checkout SHA in job log = `6156462460b3b6a7fb192e675e3d162c59b71f98`.
- Job ID `118910224676`, `Synthetic Stage 13 contract only`: all substantive steps succeeded, including exact-SHA checkout, dependency installation, compile of both Stage 13 modules, focused test, evidence generation, artifact upload, and exit-code gate.
- Test output: `17 passed in 0.54s`; JUnit: 17 tests, 0 failures, 0 errors, 0 skipped; saved test exit code `0`.
- Artifact: [cp4-stage13-contract-evidence — ID 12301484458](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39504576649/artifacts/12301484458). GitHub API size 1,679 bytes; SHA-256 digest `acf6e4b77d18f23fd10f5870e8c3b6a76c805b2bf8e4f63c434b05be255ae353`; downloaded local ZIP size 1,679 bytes and recalculated SHA-256 exactly matched the API digest. Artifact contained `evidence.json`, `junit.xml`, `pytest.txt`, and `test-exit-code.txt`; all were read. Artifact retention expiry: `2026-11-03T21:58:43Z`.
- Recomputed raw-byte SHA-256 for each source/test/workflow file fetched at the exact tested SHA; all match the artifact's `evidence.json` values: `scripts/excel_builder.py` = `33d492c8a855e43c6e44c98dfcbecbfaac020bcc0503b5526fde69bb573eb7aa`; `scripts/stage13_assemble.py` = `67f9890b5ea06f93a404e84edab233e4ff5b1af9e37c9caea004dde032708f9f`; `tests/test_stage13_assembly_contract.py` = `11615cca91cb4e7875d90b9c0b178a22992a5c0f8b719e6566521919d348595a`; workflow = `998b912cb9a7e4967f85b8cf0345b5d1ee7d9256bf8e7f14b1af08eb1d5fab2c`.
- Other earlier CP4 runs belong to earlier candidate SHAs; the selected Run is the one whose exact head is the latest tested code/test SHA. Comparing that SHA to current branch head shows the only later changes are this audit addendum and `docs/PROJECT_CONTINUITY.md`; executable/test/workflow paths have not changed since the successful run.
- `main` remains exactly `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- **Scope limit:** the 17 tests exercise synthetic mapping validation, strict scenario/trial bindings, role-contract fail-closed behavior, and injected synthetic 185-sheet structure/read-back. They do not build or validate the canonical production cohort. No production workbook, Monte Carlo, trial, checkpoint, manifest, Parquet, SOURCE_SHA, seed/RNG, cohort, or reference was changed or run.
- **Remaining hold:** the five-role contract expects `P10/P50/P90/LossCase/MaxCase`; existing V3 evidence has P10/P50/P90/Loss, and the owner’s V3 selection resolves provenance preference only, not the meaning of the role names or the missing MaxCase payload. Do not infer an alias/selector or start a canonical workbook build until approved payload evidence resolves it. The separate V3 `log_events` vs Gate A bridge conflict also remains.
