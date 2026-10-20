# R4 — Stage 13 integration and canonical payload inventory

- Date: 2026-10-20
- Working branch: `tmp/cp-stage13-integration-20261020`
- Current main HEAD verified live: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`
- Working-branch starting point: `c1b13c9f096140b1a4ef6f85614a14ebdd01a8a0` (current-main descendant containing the bounded DAILY fix and its regression test)
- Normative reference SHA-256 expected by project: `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`
- Current main source identity: `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b` (pinned identity; this CP does not change it)

## Authorization and boundaries

The user directly instructed on 2026-10-20: “افوضك لتقوم بكلما يلزم بدون اي شرط لأي أذن منفصل”. This CP interprets that as authorization for the bounded branch-only code/test integration and a temporary branch-pinned **synthetic verification workflow** described below. It does not authorize or perform production Monte Carlo, trial/checkpoint generation, historical data mutation, changing SOURCE_SHA/seed/RNG/sampling/cohort/trial IDs, editing main directly, merging/closing a PR, accepting final delivery, or creating a Release.

## R4 before change

| Item | Current state | Classification | Minimum change | Acceptance |
|---|---|---|---|---|
| Stage 13 assembler | `scripts/stage13_assemble.py` is absent from current main. The reviewed candidate is `tmp/cp-stage13-excel-compat-20261017`, blob `71e05034bafb551aea2949adc94013e8bb23d239`. | `K_CODE` | Port the reviewed assembler onto this isolated branch; preserve explicit fail-closed cohort validation. | Focused synthetic tests pass on exact new HEAD; no production cohort is assembled. |
| Excel architecture | Main `scripts/excel_builder.py` combines orchestration and worksheet construction; approved D-2026-10-10-04 names it as orchestrator and `scripts/stage13_assemble.py` as assembler. Reviewed adapter blob: `8dec3578a8221a6b12fb0915103cb09664f20a96`. | `K_CODE` | Port the adapter and preserve public legacy imports. Export `DATE_FMT` and `FINANCE_FMT` from the adapter because the already-added DAILY regression test imports them there. | Focused compatibility and Stage 9C precision tests pass. |
| DAILY dictionary serialization | Fixed on the working ancestor in commit `c1b13c9f096140b1a4ef6f85614a14ebdd01a8a0`; regression file `tests/test_excel_daily_serialization.py` is already present. | `K_CODE` | Preserve the mapping-to-header-ordered-value conversion through the assembler split. | The exact regression runs against the integrated branch source, including round-trip checks. |
| C050_G000 provenance | Main manifest blob `e796fa2443493b607f1f9c60b58eb63607959c26` points at artifact `11503191706`, which belongs to Run `37660610243`, not the manifest's recorded enrichment Run `37662891608`. The matching-run artifact is `11503510055`, size `17,787,110` bytes, SHA-256 `111eb7a2abd7b85625a02c55ee6f3140a14644ef253141bfdc3f8fc5ae4c287d`, from branch `tmp/stage9a-06-enrich-20261007-v3`, HEAD `6128b22864bb171ba49ec15dbb42439a6513c30c`. | `DATA/PROVENANCE` | Change only the artifact ID in this branch to `11503510055`; preserve source, trial IDs, data, and global identity. Do not edit main. | Read back the exact manifest blob and recheck all 25 artifact IDs/digests against live artifact metadata. |
| Representative payload coverage | Read-only inventory of all 25 canonical Stage 9A enrichment artifacts found exactly four role JSONs per scenario: P10/P50/P90/Loss. All 25 archive SHA-256 values matched GitHub artifact digests after using the corrected C050_G000 artifact. Every summary trial ID matched the per-scenario `representative_trials` metadata; each daily array had rows with only that same trial ID. No archive contained MaxCase. Detailed inventory is recorded in `stage9a_payload_inventory_20261020.json`. | `MISSING_EVIDENCE / POSSIBLE_SOURCE-CONTRACT_MISMATCH` | Do not fabricate MaxCase or reduce the approved five-role contract. Derive MaxCase from trusted canonical TrialResult and daily-ledger evidence under approved Amendment-03; fail closed if no positive value exists. | Every selected MaxCase trial ID must be derived from the approved 11,005-trial cohort and its daily records must be sourced from identity-matched existing evidence; no trial rerun. |
| Test path | Candidate synthetic evidence exists only for its earlier tested SHA; the current integration SHA has no test result yet. | `MISSING_EVIDENCE` | Add one temporary push-only workflow pinned to this exact branch; run only compile and focused synthetic/compatibility tests. | Inspect Run and artifact on exact HEAD; remove the temporary workflow in a cleanup commit after evidence inspection. |

## Workflow contract

- Exact path: `.github/workflows/cp-stage13-integration-verify-20261020.yml`.
- Push-only, exact branch `tmp/cp-stage13-integration-20261020`, path-filtered to the workflow, Stage 13 assembler/orchestrator, and focused test files.
- Read-only token permissions; assert checkout HEAD equals `GITHUB_SHA`; job timeout is explicit.
- Install repository requirements; run Python compilation and focused tests for Stage 13 assembly, adaptive mode fail-closed validation, legacy API imports, DAILY serialization, and Stage 9C precision compatibility.
- No data artifact download, production workbook build, Monte Carlo, Trial, or Checkpoint in this workflow.
- Upload inspectable test logs, JUnit XML, environment/dependency inventory, tested HEAD, and SHA-256 values. Inspect the actual artifact before classifying the test gate.
- Remove this temporary workflow from the candidate branch only after successful read-back of Run/Artifact evidence. Do not remove the source/test branch or change main.

## Test matrix

- Reproduction: the pre-fix DAILY writer passed dictionary keys to `write_table` as row values; the isolated red/green check previously showed that the regression fails on the old writer and passes on the fix. That local harness is not a substitute for testing the real repository module.
- Fix: `tests/test_excel_daily_serialization.py` against the integrated adapter/assembler.
- Regression: `tests/test_stage13_assembler.py`, `tests/test_excel_builder_adaptive_mode.py`, `tests/test_excel_builder_legacy_compat.py`, and `tests/test_excel_builder_precision.py`.
- Wider suite: deferred until the focused tests pass; no production workflow is run.

## Additional read-only source-identity finding

A live content comparison of `daily_engine.py` at main HEAD `6a218ebe0fccf210ec18f3552b141afbdd1a49ef` against the pinned source commit `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b` found exactly 11 inserted lines and no deletions. The only difference is the historical compatibility wrapper `_create_contract(...)` delegating directly to `_new_contract(...)`; the main and pinned `monte_carlo.py` blobs are identical (`a8c3603487f92d3e15c3d754ce3faee3580a5f46`). GitHub code search found the added alias in `daily_engine.py` and a reference from the older `tests/test_stage3_path_integration.py`; no production caller was found in the search result set.

This narrows the observed cause but does **not** remove the byte-identity drift. The wrapper's apparent delegation is not by itself a formal identity-preserving decision or numerical equivalence proof. Classification remains `CONFLICTED / PENDING_APPROVAL` for canonical source identity. Do not change `SOURCE_SHA`, remove the wrapper, alter tests, or use this observation to certify historical outputs.

## Known independent blockers that remain

- Production Gate A provider remains blocked until approved golden/source identity evidence is wired into the production caller.
- Main `daily_engine.py` differs from the pinned source commit; no source SHA bump or identity reinterpretation is made here.
- Stage 11 topology/source-recorded-head discrepancy remains unresolved.
- Stage 9C historical PARTIAL report versus later recorded PASS must be reconciled without erasing historical evidence.
- The seven final delivery files and their 185-sheet/content/accounting acceptance checks remain unaccepted.

## Business-rule conflict — production representative assembly is CONFLICTED

The uploaded original normative reference was read locally and its SHA-256 was recomputed from its actual bytes: `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479` (match). Its §14.6 explicitly defines **four** illustrative representative trials per scenario: P50, P10, P90, and Loss Case. The approved-looking state entry for D-2026-10-10-03 lists a fifth role, MaxCase, and count 5. The original reference is higher authority than the decision/state record under the project hierarchy; the conflicting fifth-role requirement must not be silently applied or removed in code.

The artifact inventory independently confirms all 25 official Stage 9A archives contain exactly the four roles defined in §14.6. This is consistent with the original reference and does not supply evidence that MaxCase is an approved fifth deliverable role.

- Classification: `CONFLICTED` / `PENDING_APPROVAL` for the fifth-role contract.
- Blocked action: deriving or inserting MaxCase payloads and accepting a production workbook against a five-role contract.
- Allowed independent work: preserve and test the DAILY serializer, validate provenance mapping, run synthetic code/compatibility tests, and inspect source evidence without creating production outputs.
- Resolution path: the project owner must approve an explicit amendment to the normative reference or an authoritative replacement decision that clearly resolves the four-versus-five-role conflict. A general instruction to continue engineering does not authorize changing business rules.
- Until resolved, synthetic tests on the candidate assembler are technical-only; they do not approve the fifth role, establish production stability, or authorize final delivery.



## Correction addendum — Amendment-03 read-back supersedes preliminary conflict finding

**Correction time:** 2026-10-20. The earlier “Business-rule conflict” section above was incomplete because it had not yet checked the live normative amendment register. It is retained as historical audit trail but is **superseded by this addendum**.

Live `main` `docs/governance/REFERENCE_AMENDMENTS.md` blob `b4eab80bf657d72e9e49d14db81d2baf0a462d77` has front matter `status: APPROVED_NORMATIVE_AMENDMENTS` and explicitly states that, within the defined scope, the updated text applies when it conflicts with the original. Amendment-03 expressly adopts five representative roles (P50, P10, P90, LossCase, MaxCase), defines LossCase as the smallest absolute `Final_Net_Project_Equity`, MaxCase as the highest positive `Final_Net_Project_Equity`, and says that absence of a positive value yields `UNDEFINED_BUSINESS_RULE` rather than a fabricated substitute. This is an approved normative amendment, not an inference from a candidate branch or a state label.

Accordingly:
- The five-role contract is **AUTHORIZED_BY_AMENDMENT_03**; the preliminary conflict classification is withdrawn for this scope.
- The verified Stage 9A package finding remains: `MISSING_EVIDENCE` for the fifth MaxCase payload in the 25 current enrichment archives.
- Deriving MaxCase from identity-matched canonical TrialResult rows is now an allowed read-only derivation path. It must use the approved 11,005-trial cohort, select the highest **positive** `Final_Net_Project_Equity` with the smallest `trial_id` tie-break, and bind the chosen trial's daily ledger rows to the same source identity. If no positive value exists, fail closed as `UNDEFINED_BUSINESS_RULE`.
- No production trial is rerun, no source/seed/RNG/cohort identity is changed, and no final workbook is produced until the remaining mandatory gates and acceptance checks pass.

## Acceptance status at R4 creation

- Code changes: pending.
- Exact-branch focused tests and artifact read-back: pending.
- Canonical MaxCase derivation: MISSING_EVIDENCE until the read-only derivation and exact identity checks are completed; the five-role rule is authorized by Amendment-03.
- Main/state: unchanged by this CP.
- Merge, final delivery acceptance, and Release: not performed.


## R4 addendum — read-only MaxCase source-row audit

- Purpose: derive the selected MaxCase trial ID per scenario from already completed canonical TrialResult artifacts and compare it with existing representative payload IDs.
- Pinned inputs: Stage 7 Run 37225915321 / HEAD e0b2fab6710833774937d778097363d7a8ee8e59; Stage 10 Run 37709936740 / HEAD ca73f2df37baacebbcad965fc5f433f129675820; Stage 12 reference Run 37964656154 / HEAD 0156c5f4272eb0ca7e32442657d0df9eaf4973d3.
- Bounded files: `scripts/stage13_maxcase_source_audit.py` and `.github/workflows/cp-stage13-maxcase-source-audit-20261020.yml`. The workflow is branch-pinned, read-only, and consumes existing Stage 7/10 artifact packages only. It does not run trials or build a workbook.
- It verifies live run identity, artifact IDs/names/digests/sizes, official block fingerprints, per-trial hashes, scenario keys, and contiguous trial IDs. It uses the Stage 9A representative inventory to compare MaxCase against existing P10/P50/P90/Loss payload IDs.
- Selection follows approved Amendment-03: highest positive `final_net_project_equity`, tie-break lowest `trial_id`. If no positive value exists, report `UNDEFINED_BUSINESS_RULE`; do not substitute another case.
- The output is an audit JSON only. It must not synthesize missing partner memo balances or claim payload completeness when fields are absent from the Stage 12 daily contract. Source/seed/cohort/trial IDs and historical artifacts remain unchanged.


## Existing Gate A bridge evidence read-back

- Run: `38185460895`, conclusion `success`, tested HEAD `90073c8537b1f7f05ef9c0635b1a77a6dd8cae4f`.
- Aggregate artifact: `11718779874`, `gatea-full-fingerprint-bridge-report`, 5,891 bytes, SHA-256 `69f2886e001711b7e4319f510288e09177e40aa22990ef795d30ae119e553726`.
- Artifact report: `status=PASS`; 11,005 exact trial comparisons and row rehashes; 22,546,465 actual daily rows equal expected; 0 hash mismatches; actual and official ordered trial-hash-map SHA-256 both `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`; 25 scenario reports all PASS; historical artifacts/data unchanged; no simulation/trial executed.
- Read-back comparison confirmed the workflow, bridge script, aggregate script, parser test, Stage 9A manifest, and Stage 12 accounting contract blobs are identical between that tested HEAD and live main. Therefore this is `PASS_SCOPED` for the exact source-data fingerprint bridge and matching code blobs, not a transfer of whole-branch PASS.
- This evidence confirms source-data row identity but does not connect a production Gate A provider or clear the separate source-file byte-identity finding.



## R4 addendum — explicit missing-data markers for derived MaxCase rows

The earlier candidate R4 `docs/stage13/R4_P16_P17_P18_MAXCASE_SCOPE_20261020.md` (branch `tmp/cp-maxcase-loader-20261020`, builder blob `34dbcd8fc484eb30568b6a8ec7c2ec207ffa6aa1`) explicitly authorizes candidate-only handling in which missing MaxCase daily partner balances and daily cumulative-project-profit values are labelled `PENDING_DATA_SOURCE`, never filled with zero or substituted from retained earnings. Port that narrow behavior into the separated assembler and add a regression test. The validator may skip only the daily cumulative-profit terminal comparison when the MaxCase row explicitly carries `PENDING_DATA_SOURCE`; final cash, final equity, operating net profit, trial identity, date sequence, and summary equality remain enforced. No production workbook is built.

