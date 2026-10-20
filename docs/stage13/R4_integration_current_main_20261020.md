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

