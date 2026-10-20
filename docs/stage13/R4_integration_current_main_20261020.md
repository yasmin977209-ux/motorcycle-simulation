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



## Stage 10 run-level failure — retained separately from artifact validation

The canonical Stage 10 run `37709936740` is **FAIL**, not PASS. Live run inspection shows 45 benchmark jobs succeeded and the only failed job was aggregate job `113098100249` (`aggregate-stage10`). Its exact error is `SyntaxError: unterminated string literal (detected at line 59)` in `scripts/stage10_aggregate.py`; the aggregate metrics artifact was consequently not produced. The Stage 10 run must remain recorded as failed.

This is classified `WORKFLOW_DEFECT`. The source-row audit now records that run-level failure and proceeds only with separate artifact-level checks: live artifact ID/name/run/digest/size, Stage 7/10 block metadata, per-trial hashes, scenario identity, and exact 11,005-row coverage. This can establish `PASS_SCOPED` for the existing individual artifacts if those checks pass; it cannot convert Run `37709936740` into a successful run or substitute for the missing aggregate verdict.

The first MaxCase source-audit attempt at HEAD `7ee40b22901e80a9db4226db13c43809019ed1b6` failed early with `RUN_CONCLUSION_MISMATCH` because it incorrectly required the failed Stage 10 run to have a success conclusion before checking its artifacts. That failure is preserved; the corrected script separates run-level and artifact-level status.



## R4 addendum — materialize a non-final MaxCase payload overlay from existing evidence

- New bounded script/workflow: `scripts/stage13_materialize_maxcase_payloads.py` and `.github/workflows/cp-stage13-maxcase-payloads-20261020.yml`.
- The script reruns only the read-only source-row audit, then validates each existing Stage 12 daily Parquet artifact against the live Run `37964656154`, the CP12B/CP12C file SHA reports, exact schema/identity, 11,005 TrialResult row hashes, and all daily-row continuity checks. It does not execute a simulation, Trial, or Checkpoint.
- For the five C100 scenarios, the selected MaxCase trial ID is 1 and matches existing P50/P10/P90/Loss payload IDs; the script reuses the exact P50 payload after checking its summary and common daily fields against the canonical TrialResult/Stage12 rows.
- For the other 20 scenarios, it builds only the `summary` and canonical daily record needed by the Stage 13 representative sheet from the selected TrialResult row and matching Stage 12 rows. It preserves the raw Stage 12 fields, adds exact aliases `Cash=Closing_Cash` and `Net_Equity=Closing_Equity`, and marks unavailable daily `Cumulative_Project_Profit`, `Partner1_Reinvestment_Balance`, and `Partner2_Reinvestment_Balance` as `PENDING_DATA_SOURCE`. It never substitutes `Retained_Earnings`, zero, or a guessed value.
- Output is a separately hashed JSON payload overlay plus per-scenario provenance and a manifest. The overlay is explicitly `PARTIAL`; no Excel workbook or final delivery package is built. This output cannot be accepted as final while those 20 payloads contain pending fields and other mandatory gates remain open.
- Any source artifact, TrialResult, daily-ledger, final-cash/equity, trial-ID, date, or hash mismatch fails closed and writes a failure report. All source files and historical artifacts remain unchanged.



## MaxCase source-row audit result — VERIFIED at tested code/data blobs, payload still blocked

- Workflow Run `39365226528`, conclusion `success`, tested HEAD `82b7101dabbe33c052e89f85882aa79efbee0052`; artifact `12238649038`, name `stage13-maxcase-source-audit-39365226528`, 478,795 bytes, API SHA-256 `702f9a8f4262a8d8f32c6d5f5d8b3f72b8f13143e80245f0d6f8c6c3aa2122cc`. Downloaded ZIP read-back matched that exact SHA-256 and size.
- Audit report says `integrity_status=PASS_SCOPED`, `payload_status=MISSING_EVIDENCE`: 25/25 scenarios covered, 11,005/11,005 canonical trial rows rehashed, 25 positive MaxCase selections, zero undefined selections, and no historical artifacts/data changed, no simulation/trial executed, no workbook built.
- MaxCase IDs (scenario order C100 G100/G070/G050/G030/G000; then C085, C070, C050, C030 each G100/G070/G050/G030/G000): `1,1,1,1,1; 439,464,207,53,408; 106,441,544,429,165; 172,7,543,122,60; 280,134,366,233,199`.
- All five C100 cases resolve to the only existing trial row and match an existing representative ID; 20 other scenarios require a new daily payload because the selected MaxCase IDs do not match the existing P10/P50/P90/Loss IDs. The current Stage 12 accounting contract lacks `Partner1_Reinvestment_Balance` and `Partner2_Reinvestment_Balance`; these fields cannot be fabricated.
- Consequently, source selection is now `PASS_SCOPED`, but a complete 185-sheet production workbook remains `BLOCKED / MISSING_EVIDENCE`. Existing Stage 7/10 aggregate TrialResult artifacts contain trial-level result rows, not the missing per-day MaxCase ledgers. Re-running production trials or checkpoints is outside this audit and has not been done.
- The source-audit code, assembler, Excel builder, five focused test files, both branch-scoped workflows, Stage 9A manifest, Stage 12 contract, and representative inventory have identical Git blob SHAs between the tested audit HEAD and current branch HEAD `3a716582b2e9b76fd86629b3725521b15745ce96`. The integration workflow at `f3dedf7545eb6388f59cdc8d89219941d607d7d2` passed `42 passed in 23.45s`; it tested the same code/test/data blobs but is not a run at the current commit SHA. Treat this as `PASS_SCOPED`, not a full current-HEAD suite pass.
- Historical Stage 10 run-level defect remains recorded separately: `WORKFLOW_DEFECT` (`SyntaxError: unterminated string literal at scripts/stage10_aggregate.py line 59`). The bounded source audit validated individual existing Stage 10 artifacts/rows independently; this does not convert the failed aggregate workflow into a successful run.



## Provenance correction — canonical manifest versus representative inventory

A further read-back comparison found exactly one artifact-ID mismatch between live `main`'s canonical `docs/stage9a/dataset_manifest.json` and the candidate's derived `docs/audits/stage9a_payload_inventory_20261020.json`: scenario `C050_G000`, canonical manifest artifact ID `11503191706`, inventory artifact ID `11503510055`; both list enrichment Run `37662891608`. The earlier audit verified the inventory artifact against the live artifact API but did not compare its ID to the canonical manifest mapping. Therefore it must not be described as a fully identity-matched canonical representative inventory.

The one-line candidate edit to the canonical manifest was reverted. The candidate manifest now has the exact live-main blob `e796fa2443493b607f1f9c60b58eb63607959c26`; no canonical historical manifest metadata is changed. The source-audit code now records `representative_inventory_provenance.status=CONFLICTED` and disables payload reuse for any scenario whose inventory artifact/run identity differs from the canonical manifest. Focused tests were added for both drift detection and exact-match acceptance; a new branch-scoped CI run was triggered by the test change, but its result has not yet been read back here.

Impact: the canonical TrialResult-based MaxCase selection and row fingerprint evidence remain `PASS_SCOPED`; the earlier count of five reusable payloads was based on four-role ID matching, but the candidate inventory/manifest mismatch is now separately visible and blocks any claim that the representative payload inventory is fully canonical. Final production payloads and delivery remain `BLOCKED / MISSING_EVIDENCE`.



## R4 — derive MaxCase cumulative project profit from canonical Retained_Earnings

| Field | Current state | Authority | Branch / base | Governing rule | Defect | Minimum change | Authority | Acceptance | Risk |
|---|---|---|---|---|---|---|---|---|---|
| MaxCase daily `Cumulative_Project_Profit` | `representative_daily_value` emits `PENDING_DATA_SOURCE` when the field is absent | Original approved reference §10.10 and Stage 12 contract | Candidate branch `tmp/cp-stage13-integration-20261020`, base `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`; pre-change assembler blob `2ab2a8e6c69da12d9ea8b3776510eb4ec5d2bf6e` | Reference explicitly defines `Cumulative_Project_Profit = Final_Retained_Earnings`; Stage 12 schema carries `Retained_Earnings` per daily row | `K_CODE` — known value is available under the canonical field name but the MaxCase adapter fails to map it | For MaxCase only, if `Cumulative_Project_Profit` is absent, return the row's `Retained_Earnings`; keep explicit `Cumulative_Project_Profit` precedence and keep missing partner memo balances pending | Authorized by the normative formula; no rule or data identity change | Regression tests prove fallback, explicit-value precedence, and that partner memo fields remain `PENDING_DATA_SOURCE`; integration workflow must pass | Low; wrong mapping could affect representative reports, mitigated by source-derived equality and focused tests |

The daily Stage 12 Parquet files contain all trials, so MaxCase daily rows can be extracted by trial ID from the historical dataset without rerunning simulations. This R4 changes only a deterministic field mapping in the candidate assembler; it does not write or alter historical Parquet, change SOURCE_SHA/seed/cohort, create production workbooks, or infer partner memo balances.



## R4 — extract MaxCase daily rows from the canonical Stage 12 Parquet artifacts

| Field | Current state | Authority | Source identity | Defect / work class | Minimum change | Acceptance | Risk |
|---|---|---|---|---|---|---|---|
| MaxCase daily payload | Stage 12 contains all 11,005 trials / 22,546,465 daily rows; Stage 13 needs the selected trial's daily series for each representative case | Stage 12 accounting contract; CP12B/CP12C reports; original reference §10.10 | Stage 12 Run `37964656154`, HEAD `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`; global SHA-256 `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`; Stage 9A source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`; seed `20270101` | `K_CODE` / data extraction: the prior audit stopped after selecting trial IDs and did not materialize their existing Stage 12 daily rows | Read-only extraction from the exact Stage 12 scenario Parquet artifact; verify API artifact ID/name/run/head/digest/size, CP12B and CP12C file SHA, schema and embedded identity, all trial-result hashes and daily date continuity using the existing Gate A bridge validator; compare selected trial's terminal values with its canonical TrialResult | All 25 scenarios, all 11,005 trial rows, full Stage 12 source files validated, and one selected MaxCase daily payload per scenario extracted. Payload sidecar records missing partner memo fields as missing; no values fabricated. No workbook is produced | Large read-only artifact downloads; mitigated by sequential temporary files, official SHA checks, and no writes to historical source data |

Field mapping authorized by the contracts/reference: `Closing_Cash → Cash`, `Closing_Equity → Net_Equity`, and `Retained_Earnings → Cumulative_Project_Profit` (reference §10.10 explicitly equates the latter two cumulative-profit concepts). `Partner1_Reinvestment_Balance` and `Partner2_Reinvestment_Balance` are not present in the Stage 12 daily schema and remain `PENDING_DATA_SOURCE`; do not derive them from aggregate cash or equity values. The extraction is an audit/intermediate artifact only and does not constitute acceptance of the seven deliverables.



## CI/read-back checkpoint — MaxCase daily mapping and extraction implementation

- Integration Run `39366628194` completed `success` at tested HEAD `c3b3ec72387739921b0d73680dec2bb5425424a8`; artifact `12239951234`, `stage13-integration-evidence-39366628194`, 5,096 bytes, SHA-256 `e0cbf7bde94ed5de443708b8dcdd9cf7fa03d2641f855b8527db011b1b3cea56`. Downloaded artifact read-back matched exact size and SHA. Pytest log: `50 passed in 24.57s`, exit code 0.
- Read-back confirms the assembler, Excel builder, all five focused test files, and integration workflow have identical Git blob SHAs at tested HEAD and current candidate HEAD `56e8c286b8be254b24f8bb8c2c4c26e18af04fd6`. This is `PASS_SCOPED` for those code/test blobs; it is not a full-repository pytest pass or production workbook acceptance.
- The MaxCase source audit now also reads the exact existing Stage 12 daily artifacts for each scenario, verifies artifact API digest/size and run/head identity, invokes the existing Gate A Stage 12 validator against CP12B/CP12C file hashes and every canonical TrialResult fingerprint, checks selected-trial final values/dates, and emits `stage13_maxcase_daily_payloads.json` as an intermediate evidence artifact. It does not build a workbook or modify source data.
- Latest source-audit Run `39367346036`, tested HEAD `56e8c286b8be254b24f8bb8c2c4c26e18af04fd6`, was `IN_PROGRESS` at the last status read. Its result and artifact have not yet been read back; no pass is claimed for this expanded Stage 12 extraction.
- The Stage 12 extraction maps `Closing_Cash → Cash`, `Closing_Equity → Net_Equity`, and `Retained_Earnings → Cumulative_Project_Profit`. The latter follows the original reference §10.10. Both partner memo balances remain missing because the canonical Stage 12 schema has no event-level inputs from which their transaction-level 70/30 floors and expansion deductions can be exactly reconstructed. They remain pending; no estimates or inferred substitutes are emitted.
- Current live `main` remains `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`; no PR, merge, release, or production simulation has been created or performed.



## R4 — rerun historical Stage 3 compatibility findings on current candidate code

| Item | Current state | Governing evidence | Classification | Minimum action | Acceptance | Risk |
|---|---|---|---|---|---|---|
| Legacy `daily_engine._create_contract` calls | Current `daily_engine.py` contains a direct compatibility wrapper delegating to `_new_contract`; historical raw pytest Run `38164248220` recorded five missing-method failures on an older tested SHA | Current main/candidate `daily_engine.py`; `tests/test_stage3_path_integration.py` | Historical finding is `REPORTED_ONLY` until current-HEAD targeted tests rerun; source byte-identity drift remains separate | Add a branch-pinned, read-only CI job for the five Stage 3 path tests and the existing Stage 3B / roll-forward tests | Exact tested HEAD recorded; all selected tests pass; no tests modified and no production run or checkpoint executed | Unit tests include a single deterministic trial fixture; they do not invoke production Monte Carlo or write historical data |

The job is strictly a regression test of existing tests against current candidate code. It does not remove the known `SOURCE_SHA_DRIFT` finding or authorize a source identity change.



## Live status reconciliation — Stage 9C re-audit is now PASS_SCOPED; the older report text is historical

Live `main/state.json` blob `2178260bb18efeb81437486f13b6d10cf5e85936` records `full_stage9c_status=PASS`, since 2026-10-12, based on `Stage9C_reaudit_C1_to_C6`, superseding the earlier CP-D-only status. This status was merged by PR `#38` at merge commit `74b103cd782c9e75e210a090c94fbcb4b01844c4`; the PR changed only `state.json` and documents an evidence-only read-only reassessment. The current main HEAD remains `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.

Recorded re-audit evidence: the canonical Stage 9A subset has 9,005/9,005 exact trial hash matches across 25 scenarios, zero hash mismatches, 20/20 aggregate gates, and 18,449,224 daily rows counted from the existing identity-matched Stage 12 ledger; the full Stage 12 superset has 22,546,465 daily rows with zero roll-forward and closure/balance violations. Existing CP-D evidence is 500/500 exact XLSX comparisons, 185 sheets, zero formula cells and zero Excel error cells. No trials, data, tests, or workflows were changed in that re-audit.

Therefore classify Stage 9C C-1..C-6 as `PASS_SCOPED` based on the merged state and cited existing runs, not as an open technical blocker. Keep the old `docs/stage9c/STAGE9C_REPORT.md` PARTIAL verdict as historical evidence; it has not been rewritten. Documentation reconciliation remains `MISSING_EVIDENCE` because the re-audit R4 report was recorded as `repository_committed=false` in state and is not part of PR #38. The older CP-D statement that the daily ledger was unavailable is superseded by the later full-scope ledger re-audit, not erased.

This does not clear Gate A provider integration, `SOURCE_SHA_DRIFT`, Stage 11 topology, MaxCase partner memo source fields, or final seven-file acceptance.



## Read-back results — Stage 12 MaxCase daily extraction and Stage 3 compatibility

### Stage 12 MaxCase extraction

- Run `39367346036`, conclusion `success`, tested HEAD `56e8c286b8be254b24f8bb8c2c4c26e18af04fd6`.
- Artifact `12239369983`, `stage13-maxcase-source-audit-39367346036`, ZIP size 1,567,864 bytes, SHA-256 `f3e036ef1c88fc188633b784da12f76b32c41d3fe3283c768a0c3ea1f4b669e9`; downloaded read-back matched exact digest and size.
- Embedded `stage13_maxcase_source_audit.json`: 1,088,172 bytes, SHA-256 `eafcc583375b7f85e6c2682744bd173ca29fa196132df83716104a1a4311053d`.
- Embedded `stage13_maxcase_daily_payloads.json`: 28,105,275 bytes, SHA-256 `36b6fbb2f32978112f938a4d116e21ab4e039c20dd18d197a6657191615ade7f`.
- Result: `integrity_status=PASS_SCOPED`, `payload_status=MISSING_EVIDENCE`; 25/25 scenarios; 11,005/11,005 trial-result fingerprints rehashed; 25/25 Stage 12 artifacts validated; 22,546,465/22,546,465 daily rows validated; zero fingerprint mismatches; 25 positive MaxCase selections; 52,541 selected MaxCase daily rows extracted. The sidecar contains no partner memo balance values and marks both as `MISSING_EVIDENCE`.
- Independent read-back of the sidecar confirmed for all 25 selected trials: every daily row has the selected `trial_id`, canonical source SHA, constant `result_sha256`, contiguous date range from 2027-01-01 through the selected final close date, and terminal Cash/Equity/Cumulative_Project_Profit exactly match the canonical TrialResult summary. No simulation, trial rerun, checkpoint, workbook build, or historical data modification occurred.
- The canonical manifest/inventory mismatch remains explicit: scenario `C050_G000` inventory artifact ID `11503510055` differs from canonical manifest ID `11503191706`; this prevents claiming that the *entire representative payload inventory* is identity-matched. It does not affect the newly extracted Stage 12 MaxCase daily rows, whose source files are bound to CP12B/CP12C hashes and canonical TrialResult hashes.
- Resulting status: MaxCase selection and daily-series extraction `PASS_SCOPED`; final workbook and seven-file delivery remain `BLOCKED / MISSING_EVIDENCE` until the two partner memo balances are supplied from a trusted identity-matched event-level source or an authoritative rule/source resolves the gap.

### Stage 3 compatibility regressions

- Run `39367690224`, conclusion `success`, tested HEAD `66f138c1431ded40048ab24561b7ac076eb3f405`.
- Artifact `12240271068`, `stage3-compat-evidence-39367690224`, 1,178 bytes, SHA-256 `1382312a428fb279012fd792dc71cd6cef9cddd3ef9be9a39b7ec69987ba316f`; downloaded read-back matched exact digest and size.
- Pytest: `12 passed in 9.12s`, exit code 0 across `tests/test_stage3_path_integration.py`, `tests/test_stage3b.py`, and `tests/test_stage3b_rollforward.py`. Tested code/test/workflow blobs are identical to the current candidate branch.
- This targeted PASS supersedes the old missing-`_create_contract` and two targeted Stage 3B failure observations for the tested current blobs. The historical repository-wide raw pytest Run `38164248220` remains a historical non-PASS; this scoped run does not relabel it or claim full-repository pytest PASS. `SOURCE_SHA_DRIFT` remains open.



## Independent local read-back of the MaxCase sidecar (not creator-report reuse)

Downloaded the exact workflow artifact `12239369983` and independently parsed the embedded JSON using Python's JSON/date/hash libraries. This check did not invoke the creator script or trust its status fields.

- Outer ZIP: 1,567,864 bytes; SHA-256 `f3e036ef1c88fc188633b784da12f76b32c41d3fe3283c768a0c3ea1f4b669e9`, matching the GitHub artifact API digest.
- Sidecar: 25 scenarios; 52,541 rows total. Every scenario has a nonempty daily series; dates are contiguous from `2027-01-01` to the selected final close date; every row has the same selected trial ID, source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, seed `20270101`, and one constant TrialResult hash; final Cash, Net_Equity, and Cumulative_Project_Profit equal that scenario's selected summary.
- The independent row checks above passed for all 25 scenarios. Both partner memo fields are absent from every row, as explicitly declared by the sidecar; this is a known acceptance gap, not a successful field-level acceptance.
- The nested creator report has SHA-256 `eafcc583375b7f85e6c2682744bd173ca29fa196132df83716104a1a4311053d`; the sidecar has SHA-256 `36b6fbb2f32978112f938a4d116e21ab4e039c20dd18d197a6657191615ade7f`.
- Canonical identity still has one distinct representative artifact ID in `C050_G000` (inventory `11503510055` vs manifest `11503191706`). The manifest-referenced artifact is downloadable and distinct by API/archive digest; no substitution or manifest edit was made. Resolve provenance by comparing the original run/producer metadata and the nested archive contents under an explicit identity policy; do not choose one ID by recency or name.
- Current branch read-back at documentation update: candidate HEAD `1df233596672dd38dc4feb4f385faf2a3cdc15a3`; live main HEAD remains `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`. No PR, merge, release, or production simulation.



## Source-of-truth hash and memo-field derivability check

- The uploaded original reference `المرجع_النهائي_الموحد_المعتمد.md` was available byte-for-byte at `/mnt/data`; actual size 271,496 bytes and SHA-256 `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`. This matches the expected original-reference hash exactly (`VERIFIED`). This is the original file's hash, not the merged Project Source file hash.
- Read-only inspection of live `main/docs/stage12/accounting_data_contract.json` (blob `dd3f7f102389def92df16af3b0732b77dd66df6d`) confirms the schema has daily aggregate `cash_inflows`, `cash_outflows`, `ar_collections`, and asset roll-forward fields, but no partner memo balance fields or eligible-inflow event breakdown. The authoritative `partner_equity.py` logic adds integer-floor 70%/30% allocations only for specifically eligible cash events and subtracts the full eligible expansion spend from Partner 1's memo balance. Aggregate daily inflows/outflows cannot identify all eligible event classes or the exact timing of expansion deductions.
- Therefore the two memo balances cannot be exactly reconstructed from the current Stage 12 daily schema without an additional trusted identity-matched event-level artifact or an authoritative approved derivation contract. The gap is `MISSING_EVIDENCE`, not an undefined rule and not permission to approximate. No code was changed to estimate either balance.

## R4 — resolve C050_G000 artifact/run provenance discrepancy (read-only evidence; manifest unchanged)

| Field | Current state | Reference / decision | Branch and SHA | Governing evidence | Defect class | Minimum change | Authority | Acceptance criterion | Risk |
|---|---|---|---|---|---|---|---|---|---|
| Stage 9A representative artifact `C050_G000` | `CONFLICTED`: live manifest maps artifact ID `11503191706` but records enrichment Run `37662891608`; the artifact API identifies `11503191706` as produced by Run `37660610243` | Live `main/docs/stage9a/dataset_manifest.json`, blob `e796fa2443493b607f1f9c60b58eb63607959c26`; GitHub artifact/run metadata for IDs `11503191706` and `11503510055` | Audit-only; candidate `tmp/cp-stage13-integration-20261020`, base `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`, pre-write HEAD `124e175228e161d2ef106b50459bde8e715189a7` | Artifact `11503191706` → Run `37660610243`, branch `tmp/stage9a-06-enrich-20261007-v2`, producer HEAD `43e320abb79c3db82bdb70b8c6dece883ea7676d`; Artifact `11503510055` → Run `37662891608`, branch `tmp/stage9a-06-enrich-20261007-v3`, producer HEAD `6128b22864bb171ba49ec15dbb42439a6513c30c`; both workflow runs report `success` | `DATA/PROVENANCE` plus historical `WORKFLOW_DEFECT` on the v2 path | Documentation-only: record the verified producer and archive-content comparison. Do not rewrite the manifest, substitute artifact IDs, alter source/cohort/Trial IDs, or regenerate data in this step | Documentation-only write on the candidate branch is in scope. Changing canonical manifest identity or historical data remains protected and is not inferred from general delegation | Re-fetch and read back the report; verify file blob and commit; keep identity gate blocked until an authoritative identity decision/update is permitted and committed | Low for documentation; high if the manifest were silently changed because downstream provenance and Golden coverage could be misbound |

### Independent artifact read-back

- Artifact `11503191706`: Run `37660610243`, successful; API size `17,786,146` bytes; API SHA-256 `f575044fb6a50cb5ed71d6303c40bd77841a6d38b633c105e560a4731e0a94f9`; producer head `43e320abb79c3db82bdb70b8c6dece883ea7676d`.
- Artifact `11503510055`: Run `37662891608`, successful; API size `17,787,110` bytes; API SHA-256 `111eb7a2abd7b85625a02c55ee6f3140a14644ef253141bfdc3f8fc5ae4c287d`; producer head `6128b22864bb171ba49ec15dbb42439a6513c30c`.
- Both ZIPs were downloaded and hashed locally; actual byte counts and SHA-256 values match the artifact API values. Each ZIP contains one `C050_G000.tar.gz` member. Both inner archives contain the same eight regular files plus directory entries.
- Compared each regular file by streaming SHA-256 after decompressing the inner tar. Seven payload/data files are byte-identical across the two artifacts: `daily_distribution.parquet` (137,290 bytes; `caf8de98e7e907b01cb87ee2cfc879293a3acb740290f0d2a8ab6867ebb13cd3`), `trial_results.parquet` (28,825 bytes; `09c223d8348f93a5c5e9246a409614d6345a76b224ff65f865c6bdbaea5fbbe8`), `trial_fingerprints.json` (35,824 bytes; `82cb7a2725944edc3b749bcc722d22040459baac2db6c68f3c0ddde98b0db8f6`), and all four representative JSONs: P10 (332,102,108 bytes; `3191b3def023762e42e23d9a8a73235e5e78b94757d17b691f19f4e37ab477d5`), P50 (342,536,957 bytes; `5b377dbd4868cbb165a6925916051c375ad0c031636224e3b08560196656b3e8`), P90 (356,570,015 bytes; `7742dccd6ac8433542cb577e583310891b07104fb2af895a663705d70c2886c4`), Loss (314,218,180 bytes; `34be00c541604e6bb13e80b3e10ae6f95109bdc3ce76d64661f58f81f484164c`).
- The only regular-file content difference is `scenario_metadata.json`: the manifest-referenced artifact has 887 bytes, SHA-256 `21e2f33603e21346ae84873f372d39e301f399a0f449eb5db8e195e742d51735`, and `"log_events": true`; the v3 artifact has 911 bytes, SHA-256 `a143c3fb7f2cee8ab625b0beb40295ede2c5879975d08f455e59b85406004cab`, and `"log_events": "representative_trials_only"`. Scenario/source/cohort fields, selected representative IDs, counts, date bounds, block fingerprints and TrialResult fingerprints match.
- Root cause verified in workflow/code read-back: original control branch script blob `e92381ddebef4c8792702e4d8a6aba6ef67b0614` contains `log_events=True` and `"log_events": True`. The v2 workflow's `Checkout enrichment control branch` step explicitly checks out `tmp/stage9a-06-enrich-20261007` (original branch), despite its v2 run HEAD being `43e320abb79c3db82bdb70b8c6dece883ea7676d`; therefore its save-and-copy step used the original script, explaining artifact `11503191706`'s metadata. The v2 branch script blob `eac3a51af6d31ab0ab9fddda688114a62fb3e7a4` already contained representative-only logic, but the workflow checkout ref did not use it.
- The v3 workflow at producer HEAD `6128b22864bb171ba49ec15dbb42439a6513c30c` checks out the v3 control branch; its script blob `dfb27e7623f42e9ef1d81f3d6752ddd3de269d8d` uses representative-only event logging and writes the matching metadata string. This is consistent with artifact `11503510055` and the manifest's recorded Run ID `37662891608`.
- Finding: the artifact/run pairing recorded in the manifest is demonstrably internally inconsistent. Content evidence strongly suggests `11503510055` is the artifact produced by the manifest-listed Run `37662891608`, and that its only archived payload difference from `11503191706` is the event-logging metadata field. Nevertheless, no manifest ID substitution is made here: canonical identity repair remains a protected provenance change. Status stays `CONFLICTED / PENDING_APPROVAL` until the authorized identity record is reconciled. No historical Parquet, TrialResult, fingerprints, source SHA, seed, cohort, tests, or workflow was modified; no simulation or trial was rerun.

## R4 addendum — verify whether trusted partner-memo daily values exist for selected MaxCase trials

| Field | Current state | Reference / decision | Branch and SHA | Governing evidence | Defect class | Minimum change | Authority | Acceptance criterion | Risk |
|---|---|---|---|---|---|---|---|---|---|
| Daily Partner 1/2 memo balances for selected MaxCase rows | \`MISSING_EVIDENCE\` for the 20 non-C100 scenarios where MaxCase trial IDs do not equal any saved P10/P50/P90/Loss representative ID | Stage 7 official source artifact; Stage 9A enrichment archive/schema; approved Amendment-03 MaxCase selection | Candidate \`tmp/cp-stage13-integration-20261020\`; pre-write HEAD \`37161ad038ea4e7f3c842eba87696ad73b17c0d4\`; canonical source SHA remains \`f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b\` | Stage 7 Run \`37225915321\`, artifact \`11312813109\`, producer HEAD \`e0b2fab6710833774937d778097363d7a8ee8e59\`; Stage 9A Run \`37662891608\`, artifact \`11503510055\`; MaxCase selection/source audit Run \`39367346036\` | \`DATA/PROVENANCE\` / \`MISSING_EVIDENCE\` | Read-only inventory only. Do not derive balances from aggregates, populate zero, mutate historical data, or rerun completed trials. Keep affected rows explicitly pending until a trusted identity-matched event-level source or an approved exact derivation contract is available | Authorized to inspect existing artifacts and document gaps; not authorized to rerun trials or invent an accounting derivation | Verify source artifact digest, its actual member list/logging metadata, representative IDs and MaxCase selection; maintain a fail-closed missing-data marker | High if invented values affect the PARTNER/DAILY books; low for the read-only inspection |

### Source artifact and role-ID read-back

- Official Stage 7 artifact API metadata for \`11312813109\` confirms name \`stage7-blocks-C050_G000-1\`, Run \`37225915321\`, branch \`tmp/stage7-full-run-20261004\`, producer HEAD \`e0b2fab6710833774937d778097363d7a8ee8e59\`, size 52,239 bytes, SHA-256 \`b1fc0e25efe8e41226ca6082ef2fd391f7b3a8351e7c5dfdd1ca8604b098384a\`. The downloaded ZIP read-back matched that size and digest. It contains four block Parquet files and four corresponding metadata JSON files; the metadata for each block declares \`log_events: false\`. The archive contains no per-day partner-memo ledger or event log.
- The matching-run Stage 9A archive \`11503510055\` has \`scenario_metadata.json\` with \`representative_trials_only\`. Its representative JSON structure carries daily Partner 1/2 memo balances and event log for the four saved roles, but it does not store those per-day ledgers for every trial. Its \`daily_distribution.parquet\` stores aggregate metrics, not the selected trial's partner-memo balance time series.
- For \`C050_G000\`, Stage 9A metadata lists \`P10=131\`, \`P50=29\`, \`P90=18\`, \`Loss=304\`; the approved source audit selects MaxCase \`trial_id=165\`. The selected ID is not one of those four roles, so the archived representative ledger/event log cannot be reused for its memo balances. The MaxCase source audit independently records that 20 non-C100 scenarios have this non-overlap; only the five C100 scenarios reuse a representative trial because each has the single canonical trial ID 1.
- This verifies an actual source-coverage gap; it is not evidence that memo balances are zero or that the accounting rule is undefined. Stage 12 aggregate daily rows cannot reconstruct the eligible-event classifications and Partner 1 expansion deductions. No permitted read-only source examined here fills this gap.
- **Correction to the preliminary action in the opening R4 table:** the earlier proposal to change the C050_G000 manifest artifact ID was not retained or applied; the candidate manifest was read back at the live-main blob. This later provenance addendum supersedes that preliminary proposed action: no manifest identity change is made without the separate protected provenance reconciliation. The only write in these two addenda is to this candidate-branch R4 report.



## R4 addendum — independent review of the historical Gate A provider candidate (2026-10-20)

**Scope:** read-only review of an already-existing provider branch and its workflow artifact. This is not a change to Gate A policy, Golden coverage, the production workflow, tests, source identity, or trial data.

| Item | Current state | Governing reference / decision | Branch and SHA | Evidence | Classification | Minimum change | Authority | Acceptance criterion | Risk |
|---|---|---|---|---|---|---|---|---|---|
| Main production Gate A provider | `BLOCKED`: main state says `production_golden_provider_connected=false` and `production_gate_a_status=BLOCKED_GOLDEN_PROVIDER_MISSING` | Live `main/state.json` blob `2178260bb18efeb81437486f13b6d10cf5e85936`; main decisions log blob `df4910e6a86bcce84f6b71d6d260913800474f95`; D-2026-10-10-01 establishes exact reference/golden matching, but does not itself accept a provider implementation | Main HEAD `6a218ebe0fccf210ec18f3552b141afbdd1a49ef` | Re-read state and governance decision log at this review | `PENDING_APPROVAL` / `MISSING_EVIDENCE` for promoting candidate provider into the effective governance state | Do not alter main; retain fail-closed runtime behavior while provider authority and workflow integration are unresolved | General delegation permits continued review, not a silent identity change or production trial/checkpoint run | An owner-authorized, current-main decision covers the precise provider Golden map and identity exception; current-main state and implementation are revalidated without executing trials | High if a candidate Golden is silently promoted or a production checkpoint starts without trusted Gate A evidence |
| Existing provider candidate preflight | `PASS_SCOPED` for that candidate's read-only validation only; not accepted as main Gate A | Candidate provider pins historical run/artifact SHA identities; however candidate decision text does not substitute for an effective decision on main | Branch `tmp/cp-gatea-provider-bind-20261016`, tested HEAD `cb2f603aacd93b910093d497deeea43710e7b0d3`; Run `38830875732`; artifact `12016903462` | Run conclusion success. ZIP size 1,719 bytes, SHA-256 `72f122bc2a78ab079f6c7064c45d78d40b6e9463b83454a1366e32138c0359d6`. Read-back files: `gatea_provider_preflight_report.json` 4,017 bytes, SHA-256 `5e200622ab0ed79dccf8a0abf0d9908c227680fb2e954f86dfd9927f9cd73f22`; `source_identity_exception_report.json` 995 bytes, SHA-256 `9c0a98ae2d7d18621ab8177733a51ee4be0d0140a39db0b32b5beff9aa3badbc` | `PASS_SCOPED` only | No provider/workflow code ported in this CP | Read-only preflight ran no Monte Carlo, trial generation, or dataset/Parquet mutation; the run is not evidence of final delivery acceptance | Re-fetch and re-validate the same exact run/artifact and code blobs after proper authority is established | The preflight reports a 25-scenario map of 25,205 fingerprints: 20 non-C100 scenarios at 1..1200, five C100 scenarios at trial 1, and C030_G030 at 1..2400. Its source-map SHA-256 is `0fbe3aa87a253f9527953c77b0a122871c9344f75ece6c8a49da99b2a85c1ce1`; source label remains `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`; source commit is `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`. These values bind the candidate artifact; they do not resolve decision authority | Risk is high if this scoped PASS is relabelled as current production Gate A acceptance |
| Golden extension authority and coverage | `CONFLICTED / PENDING_APPROVAL`: candidate code refers to decision `D-2026-10-15-10` and extension Run `38662076725` / artifact `11940485523`, but that decision was not found in the live main decisions log or the reviewed provider-branch decisions log. Main also lacks candidate decision `D-2026-10-14-01`; the latter exists only in `tmp/cp-golden-provider-20261014` as candidate text claiming owner approval | Authority order prohibits inferring approval from a candidate branch's `APPROVED BY PROJECT OWNER` label. The effective main decision log contains neither D-2026-10-14-01 nor D-2026-10-15-10 | Main HEAD `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`; candidate decision log `tmp/cp-golden-provider-20261014` blob `d6a7ecd15e7335800dc8b2865e0a4fef6d5e9c70`; provider candidate `cb2f603aacd93b910093d497deeea43710e7b0d3` | Current main/state continues to list provider missing; read-only provider report itself lists extension Decision ID D-2026-10-15-10 and the associated run/artifact | `DATA/PROVENANCE` + `PENDING_APPROVAL` | Do not rewrite `SOURCE_SHA`, the 25,205 map, Golden artifacts, state, or decisions log; do not reconnect the candidate until scope/authority is reconciled | No specific owner authorization for this provider coverage extension or protected Stage 7 workflow modification is established in the currently effective main source. Broad “do everything” delegation does not override explicit protected-action constraints | The exact decision and approval scope are established from an owner-approved/effective record, the extension artifact is revalidated by run/head/content digest, and source identity is checked independently | High: silently accepting a candidate's own claimed approval can turn candidate-derived fingerprints into the production reference |
| Stage 7 workflow integration | `NOT_AUTHORIZED` for promotion from this CP: the provider branch modifies `.github/workflows/stage7-full-run.yml`, whose workflow has write permissions and a simulation matrix; binding a preflight there can affect production execution behavior | R4 + specific approval required for workflow changes; no production run permitted before Gate A/provider authority and all preconditions are proven | Provider candidate HEAD `cb2f603aacd93b910093d497deeea43710e7b0d3`; modified workflow blob `9081567f1e59430b530f922edcb3f4f067f50d89` versus main blob `4bb3b8df6742f51087b45eed1b9200468f12ac60` | Diff shows newly inserted source-identity exception and live provider preflight before the simulation matrix | `WORKFLOW_DEFECT` is not asserted as a code defect; the classification here is protected workflow integration pending its specific authorization | Keep existing main workflow unchanged; no production workflow trigger or simulation initiated | Separate R4 and scope-specific approval for workflow modification, followed by a non-production contract verification before any authorized production use | High due to matrix simulation, branch-ref state management, and write-capable permissions |

### Independent read-back and exact interpretation

- The provider Run `38830875732` returned `success` on the exact candidate HEAD above. Its artifact was downloaded and read back; the ZIP size/digest and embedded JSON sizes/hashes match the GitHub artifact metadata.
- The preflight JSON itself reports `status=PASS`, `workflow_or_monte_carlo_executed=false`, `trial_generation_executed=false`, `historical_dataset_modified=false`, and `parquet_modified=false`. This independently supports only that the candidate provider can load/validate its pinned fingerprint inventory in that run environment.
- The separate source-identity report allows exactly one byte-identical additive `_create_contract` adapter over the pinned source tree; the stripped candidate `daily_engine.py` SHA matches its pinned bytes. It also preserves a separate historical full-pytest failure (`3 failed, 384 passed, 1 skipped`) from replay Run `38461464864`. That failure was not erased or converted to PASS by the provider-verification workflow's targeted checks.
- Important scope discrepancy: provider candidate code and its report depend on the 1,200-record C030_G030 extension under `D-2026-10-15-10`, but no such decision entry appears in the effective main decision log or in the inspected provider-branch decision log. `D-2026-10-14-01` is also not in main. Their presence/claims in candidate artifacts are `REPORTED_ONLY`, not a reason to override the active `GATEA_PROVIDER_MISSING` blocker. The later C100-golden candidate contains another decision, `D-2026-10-17-07`, but it too is absent from main; no use is made of that candidate decision here.
- No code, tests, workflows, source identity labels, Golden manifests, historical datasets, or trial outputs were changed in this review. No workflow was triggered. Main remains untouched. Gate A production remains `BLOCKED`; the final seven-file delivery remains separately blocked by the previously recorded MaxCase partner-memo source gap and other parent gates.


## R4 addendum — independent read-back of the C100 Gate A extension artifact (2026-10-20)

### R4 before the documentation-only write

| Field | Current state | Reference / decision | Branch and SHA | Governing text / evidence | Defect class | Minimum change | Authority | Acceptance criterion | Risk |
|---|---|---|---|---|---|---|---|---|---|
| C100 extension payload | \`PASS_SCOPED\` for 2,995 extension-record hash/coverage checks; combined Golden acceptance remains \`CONFLICTED / PENDING_APPROVAL\` | D-2026-10-17-07 is present only in candidate decision text, not in effective \`main/docs/governance/DECISIONS_LOG.md\`; existing D-2026-10-13-02 is a narrow source-adapter exception, not approval of this Golden extension | Source candidate branch \`tmp/cp-gatea-c100-resume-20261017\`, Run \`39004726976\`, tested HEAD \`52d5d92831abc4de5ed8e01c91291acf6d37f0b8\`; current audit branch \`tmp/cp-stage13-integration-20261020\`, HEAD before write \`c6f3fba64207ad2f3e7adffb9c0bd6147609676c\`; main HEAD \`6a218ebe0fccf210ec18f3552b141afbdd1a49ef\` | Run API says success (one job); artifact \`12091571204\`, ZIP 197,117 bytes, SHA-256 \`2cec72b62e72bb99120594ad6621c431f0e4148b706a13eae72c9528bc92ea19\`; independent parsing/re-hashing described below | \`DATA/PROVENANCE\` + \`PENDING_APPROVAL\` | Append an audit record only; do not port the provider, modify source/workflow/tests, change identity records, or accept a checkpoint | Read-only artifact revalidation is in scope; Golden promotion/integration remains out of scope until governing authority is effective and independently verified | Recomputed per-record SHA values, unique keys, exact C100 coverage, source blob identity; preserve explicit gaps about the base map and effective approval | High if record-level PASS_SCOPED is promoted to production Gate A or if the declared combined map digest is misrepresented as independently reproduced |

### Independently verified payload

- Run \`39004726976\` is completed with conclusion \`success\` on branch \`tmp/cp-gatea-c100-resume-20261017\`, tested HEAD \`52d5d92831abc4de5ed8e01c91291acf6d37f0b8\`; its sole job and the focused continuation-test, pinned-source-closure, generation, artifact-upload, and output-boundary steps report success. The workflow runs the producer under a detached worktree at source commit \`0156c5f4272eb0ca7e32442657d0df9eaf4973d3\`, rather than using the candidate worktree's model files.
- The downloaded artifact has \`gatea-c100-golden-continuation\` identity ID \`12091571204\`; ZIP size and SHA-256 match the live artifact metadata. Embedded \`c100_golden_extension.json\`: 3,515,092 bytes; SHA-256 \`c2ac869f5bce0d3531226027fc26d38f407b62389a76c7e06f66613010eed1a8\`.
- Independent re-hashing of the embedded \`trial_result\` in every extension record using the Stage 10 canonical JSON contract produced **2,995/2,995 exact result-hash matches**, zero duplicate scenario/trial keys, and zero record identity/hash errors. Each of five C100 scenarios has exactly 599 records, trial IDs \`2..600\`; each row's embedded scenario/trial identity, source SHA \`f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b\`, source commit \`0156c5f4272eb0ca7e32442657d0df9eaf4973d3\`, seed \`20270101\`, and schema label match the declared scope.
- Recomputed ordered-map digest over those 2,995 extension rows is \`a9850a0dc2cda16d8c89df52bf9715203d9cc9cc5fbffbd6792f13d90b6dcb46\`, exactly matching the artifact's declared extension digest. Independently queried GitHub tree objects show all 14 named model-source file blobs are byte-identical between \`SOURCE_SHA\` and producer source commit \`0156c5f4272eb0ca7e32442657d0df9eaf4973d3\`; workflow source confirms execution used that pinned source worktree.
- **Important limit:** the combined digest \`ddc84093a971bbc769ad60e6ee34b2a5ff7b82bcacc89207d94f9f1effd75eb8\` and 25,205-row base-map digest \`0fbe3aa87a253f9527953c77b0a122871c9344f75ece6c8a49da99b2a85c1ce1\` are present in artifact reports, but this extension ZIP does not contain the base map's 25,205 individual fingerprints. This audit therefore does **not** claim to have independently reproduced either base-map or combined-map digest.
- The artifact itself explicitly reports \`COMPLETE_PENDING_INDEPENDENT_ARTIFACT_AUDIT\`, \`production_checkpoint_accepted=false\`, and \`overall_gate_a_or_stability_accepted=false\`. This audit upgrades only the individual extension-content checks to \`PASS_SCOPED\`, not the production Golden provider or Gate A.
- The current \`main/state.json\` still records \`GATEA_PROVIDER_MISSING\`; current \`main/docs/governance/DECISIONS_LOG.md\` does not contain D-2026-10-14-01, D-2026-10-15-10, or D-2026-10-17-07. A successful candidate workflow and a candidate decision label do not establish effective approval. No code, test, workflow, source identity label, historical Parquet, seven-file delivery, or \`main\` state was changed in this CP; this step ran no simulation or trial generation.

