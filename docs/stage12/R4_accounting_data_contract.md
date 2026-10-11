# CP-B2 R4 — Stage 12 accounting data contract canonicalization

Date: 2026-10-10  
Scope: contract and audit documentation only. No engine, tests, RNG, reference, workflow, or state.json changes.

## Required three-way comparison before change

| Item | main (HEAD 5185f51faef836a2884c904b8bb8feb775f5f6c2) | stage3b-preserved (HEAD 2e3aa381d833fe430d2aec42e98dd0d29918c3bf) | Binding reference | Judgment |
|---|---|---|---|---|
| Stage 12 contract | `docs/stage12/accounting_data_contract.json` absent from main. Actual roll-forward report `6084e8f68fa649fcf0726daa04f41ae9b0636706` and closure report `81bc3cd9c7666487b69b644dcc3291d0547c8e8b` both record PASS for 11,005 trials and 22,546,465 daily rows. | Contract absent; historical `state.json` is a Stage 9-era diagnostic record with a different source package SHA and cannot define Stage 12. | Reference §§14.3–14.4 define MASTER_SEED=20270101, SHA-256 RNG and stable trial identity; §§15.1–15.6 and 18.1–18.2 define Excel/source-of-truth and output requirements. | **DEVIATION:** current canonical Stage 12 contract missing from main. Add new v1.1 contract; preserve historical v1.0 unchanged. |
| Dataset schema and keys | Existing CP12-A contract on `tmp/stage12-contract-20261008` commit `6df051f680a43ff86a41d3cfab3c04bce40c2724` identifies daily accounting columns and primary key `(scenario_id, trial_id, date)`; materializer/aggregator code on the accepted Stage 12 branch implements the same schema plus `result_sha256`. | No Stage 12 schema/contract. Do not copy diagnostic code. | Reference §14 requires trial identities to remain fixed irrespective of scheduling; §18 requires trial outputs to remain identifiable and reproducible. | **MATCH** after carrying forward the established key/fields and recording the actual emitted `result_sha256` field. |
| Runtime topology | Historical v1.0 contract describes 45 chunks, max parallel 10, 30-minute job timeout and an estimated 22,850,782 rows; those values are superseded for the adopted Stage12 materialization topology. | No corresponding canonical topology. | Reference §19 requires execution from validated Python outputs; no business rule defines a 45-job workflow. User decision in `DECISIONS_LOG.md` (2026-10-09) adopts 25 scenario materialization jobs plus validate and aggregate. | **DEVIATION resolved in proposed v1.1:** 25 scenario-level materialization jobs plus validate and aggregate (27 jobs total), max parallel 25; timeouts 45 / 360 / 30 minutes. |
| Actual row/output evidence | CP12-B run `37964656154`, head `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`, original and reproduced global hash both `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`, 11,005 trials, 22,546,465 daily rows, zero retries. CP12-C / CP12-D both record zero violations over their full reported scopes. | No Stage 12 actual output evidence. | Reference §§14.3–14.4 require deterministic identity; §§15 and 18 require the final Excel/output package to derive from verified Python outputs. | **MATCH:** use actual, run-backed counts and preserve the old estimate only as historical metadata, not as actual. |

## R4 classification

- **DEVIATION:** canonical Stage 12 accounting data contract missing from main; historic v1.0 workflow description conflicts with the subsequently adopted topology.
- **MATCH:** source SHA, seed, aggregate identity, trial count and row count match the CP12-B/C/D records.
- **VIOLATION:** none found in the documentation-only CP-B2 scope.
- The old v1.0 contract at blob SHA `1915f6b568661b010781f193146546b070006e34` is referenced as immutable historical evidence and is not modified.
- No trials were re-run. No state update is part of this batch.

## CP-B2 proposed files

- `docs/stage12/accounting_data_contract.json` — canonical v1.1, with observed counts and the adopted topology.
- `docs/stage12/R4_accounting_data_contract.md` — this review.
