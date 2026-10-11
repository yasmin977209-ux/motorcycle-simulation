# CP-B2 R4 — Stage 12 accounting data contract canonicalization

Date: 2026-10-10. Scope: new contract/report documentation only; no engine, tests, RNG, reference, workflow, or state.json changes.

## Three-way comparison completed before the proposed change

| Item | main (HEAD 5185f51faef836a2884c904b8bb8feb775f5f6c2) | stage3b-preserved (HEAD 2e3aa381d833fe430d2aec42e98dd0d29918c3bf) | Binding reference | Judgment |
|---|---|---|---|---|
| Canonical Stage 12 contract | docs/stage12/accounting_data_contract.json absent. Current state and DECISIONS_LOG.md record the user-approved 25 + validate + aggregate topology as pending canonical documentation. | Contract and Stage 12 ledger absent; state is Stage 9-era diagnostic history with source-package SHA c7429d1a31037e98201a05ed98b62c9c68118b2fda89064804d2d2cea2dfed79. | §§10.6, 12.17, 14.7, 15.3–15.6, 18.1–18.2 define accounting/roll-forward, daily distribution, Excel and Parquet/SQLite output requirements; they do not define GitHub job topology. | DEVIATION: the official updated contract is missing from main. Create a new versioned file; do not rewrite the historic contract. |
| Actual daily ledger | Main has CP-12-C roll-forward validation PASS: 25 scenarios, 11005 trials, 22546465 daily rows; aggregate SHA matches. CP-12-D closure/settlement validation also PASS on the same source identity and row count. | No Stage 12 ledger nor Stage 12 validations. | §10.6 requires the cash, AR, gross-assets, accumulated-depreciation and equity roll-forwards; §12 M17 requires daily balance equality; §18.2 specifies zero accounting balance difference and complete output quality. | MATCH: actual counts and validation records support recording 22546465 rows; replace the historical estimate in the new contract with this observed value. |
| Schema/keys | Historic CP-12-A contract has 37 required fields; primary key (scenario_id, trial_id, date); duplicate/missing records FAIL. Main validation schema is stage12-daily-accounting-v1. | No compatible Stage 12 schema evidence. | §§10, 12 and 18 require daily accounting fields and repeatable trial outputs; field names were inherited from historic contract rather than invented in this CP. | MATCH: preserve all 37 fields, primary key and fail policy unchanged. |
| Workflow topology | User decision in DECISIONS_LOG.md adopts 25 scenario materialization jobs + separate validation and aggregation jobs, total 27; Run 37964656154 recorded 25 artifacts, no retries, exact global SHA. | No equivalent topology; do not copy historical workflow code. | Reference does not prescribe CI job counts; current topology is from the explicit user decision, not inferred from the reference. | MATCH to user decision. Document the accepted topology only; no workflow change. |
| Historical design | Current main has no canonical contract but does have actual run and validation evidence. | Stage 9-only diagnostic state; different source identity. | §0.1 prohibits inventing rules; historic records must remain distinguishable from current source of truth. | DEVIATION resolved in this branch by creating a new v2 contract with provenance to v1. |

### R4 classification

- **DEVIATION:** official Stage 12 accounting contract v2 missing from main.
- **MATCH:** actual Stage 12 validation is PASS and its row count / source identity match the current recorded run.
- **VIOLATION:** none found in CP-B2 scope.
- Historical v1 source is preserved unchanged on branch tmp/stage12-contract-20261008, commit 6df051f680a43ff86a41d3cfab3c04bce40c2724, blob SHA 1915f6b568661b010781f193146546b070006e34. Its 22850782 daily rows and 45-job / 10-parallel / 30-minute design were estimates/design assumptions, not actual observed row count or the adopted workflow topology.
- Authorization timing is explicitly recorded as **RETROSPECTIVE_USER_AUTHORIZATION**; this contract does not claim authorization existed before Run 37964656154.
- No trial rerun. No state.json update. No engine, tests, RNG, reference or workflow changes.

## Contract gate evidence

| Gate | Result | Evidence |
|---|---|---|
| Source identity | PASS | SOURCE_SHA f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b, MASTER_SEED 20270101, global aggregate SHA 7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44. |
| Materialization | PASS | Run 37964656154; 25 scenario Parquet files; 22546465 rows; 11005 trials; retries=0; original/reproduced aggregate SHA matches. |
| Roll-forward | PASS | docs/stage12/roll_forward_validation.json, overall_result PASS; 22546465 rows checked. |
| Closure/settlement | PASS | docs/stage12/closure_settlement_validation.json, overall_result PASS; same 25 scenarios, 11005 trials and 22546465 rows. |
| Job topology | PASS | Accepted exact pinned workflow stage12-b3-25jobs; 25 materialize + 1 validate + 1 aggregate; max-parallel 25; timeouts 360/45/30 minutes. |
| Contract coverage | PASS | 37 required fields, primary key (scenario_id, trial_id, date), duplicate/missing policy FAIL, Parquet format retained. |
| Stage 9C 20-point gate | NOT CLAIMED | This contract does not upgrade or adjudicate Stage 9C; CP-D handles that gate under its separate condition. |

## Proposed files

- docs/stage12/accounting_data_contract.json
- docs/stage12/R4_accounting_data_contract.md
