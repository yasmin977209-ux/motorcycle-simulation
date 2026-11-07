# D6 Independent Post-Write Audit

- Workflow_Status: SUCCESS
- Audit_Status: PASS_SCOPED_WITH_LIMITATIONS
- Stage_Disposition: PASS_SCOPED_WITH_LIMITATIONS
- Final_Acceptance: NOT_ACCEPTED
- Disposition: PASS_SCOPED_WITH_LIMITATIONS
- D5 Artifact: 13582441423 / Run 42393413807
- D6 Run: 42403657899
- Tested SHA: 42922d06637b7fad1d36c412e2253423f9367f34
- Classification: T2_INTERIM / NOT_FINAL_BLOCKED

| Check | Status | Detail |
|---|---|---|
| auditor_unit_tests | PASS | Focused D6 auditor unit suite completed before this audit step. |
| d5_artifact_download | PASS | Workflow verified exact pinned GitHub Artifact metadata, digest, and downloaded byte size before invoking auditor. |
| artifact_outer | PASS |  |
| zip_inventory_crc_paths | PASS |  |
| manifest_sha256sums | PASS |  |
| identities_gates | PASS |  |
| excel_175_180_182 | PASS_SCOPED | Exact-head acceptance tests checked workbook inventory, numeric parity, daily round-trip, representative partner balances and exact-rational financial cells; duplicate full XML scanning is intentionally not repeated. |
| docx_files | PASS_SCOPED | Per-file DOCX parse, T2, §17.3 substance, OOXML directionality and resolution of every explicit Number Registry ID; full numeric-token lineage remains a separate acceptance test. |
| docx_number_registry_traceability | PASS_SCOPED | Every explicit NR-/D2D- identifier in DOCX resolves against the pinned Number Registry/extension; this does not claim every numeric token is registry-backed or execute Test 176. |
| docx_rendering | PASS_SCOPED | Each DOCX was rendered in a separate LibreOffice process with an isolated profile and 120-second timeout; both summaries must be 2–3 pages. |
| docx_176 | EXECUTED_ON_EXACT_HEAD |  |
| acceptance_test_execution | PASS |  |
| test_175 | EXECUTED_ON_EXACT_HEAD | D6 independently verified 185 worksheets per workbook, matching worksheet order, cross-workbook numeric parity, and rejected formula/error cells. This is scoped evidence, not a claim that the separately numbered historical test suite was invoked. |
| test_176 | EXECUTED_ON_EXACT_HEAD | The full historical acceptance contract was not executed by this D6 audit. Related scoped checks, if any, are reported separately and are not substituted. |
| test_179 | EXECUTED_ON_EXACT_HEAD | The full historical acceptance contract was not executed by this D6 audit. Related scoped checks, if any, are reported separately and are not substituted. |
| test_180 | EXECUTED_ON_EXACT_HEAD | The full historical acceptance contract was not executed by this D6 audit. Related scoped checks, if any, are reported separately and are not substituted. |
| test_181 | EXECUTED_ON_EXACT_HEAD | The full historical acceptance contract was not executed by this D6 audit. Related scoped checks, if any, are reported separately and are not substituted. |
| test_183 | EXECUTED_ON_EXACT_HEAD | The full historical acceptance contract was not executed by this D6 audit. Related scoped checks, if any, are reported separately and are not substituted. |
| test_182 | EXECUTED_ON_EXACT_HEAD | Exact registry-value comparisons were performed for the financial cells resolved by the pinned Registry. Any mismatch blocks this scoped result; this is not a claim that the separate historical acceptance test was invoked. |
| test_186 | EXECUTED_ON_EXACT_HEAD | D6 verified the exact outer GitHub Artifact fingerprint, inner package fingerprint, eight-member ZIP inventory, CRC/path safety, manifest member hashes, and SHA256SUMS coverage. This is scoped package evidence, not a claim that the separately numbered historical test suite was invoked. |

## Preserved gate states

- financial_gate_a: PASS_SCOPED
- production_gate_a: NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS
- gate_b_n2400: FAIL_SCOPED (10/10)
- stability: NOT_CONVERGED (0/60)
- n4800: NOT_EXECUTED
- c100_golden: NOT_RUN

## Limitations

- Test 176 is bound to the exact D4 build outputs and D5 package members through D4 report-manifest SHA, D4 build-output SHA values and D5 package-manifest SHA values.
- DOCX rendering and directionality are checked independently in this D6 job; rendering does not imply visual review of every page.
- Acceptance tests 175, 176, 179, 180, 181, 182, 183 and 186 executed on this exact D6 run and SHA; individual outcomes are retained in ACCEPTANCE_TEST_EXECUTION.json.
- Test 181 source partner daily balances are not recreated; missing historical 48K evidence remains missing.
- No full 177-unique-test suite, Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main write, merge, Release or final acceptance.

D6 is not P17 acceptance, FINAL_ACCEPTED, CONVERGED, or release authorization.
