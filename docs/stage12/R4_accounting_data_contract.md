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

## Current R4 refresh — 2026-10-11 (post-CP-B1 main)

This section is an additive current-state review. The 2026-10-10 R4 record above is preserved verbatim as historical evidence; its comparison baseline was `main@5185f51faef836a2884c904b8bb8feb775f5f6c2` and must not be mistaken for the current main snapshot.

**Live comparison identity**
- Current `refs/heads/main`: `601d8cf92ee64a64d1ac0a53d31d32c84ee830e3` (verified immediately before this update).
- Proposed contract source: PR #18 head `9eb3a89f77048e2d727d5c7ae1117c0d03ba61c6`, contract v1.1.
- `stage3b-preserved`: `2e3aa381d833fe430d2aec42e98dd0d29918c3bf`; diagnostic evidence only. The `docs/stage12` path is absent there, so it cannot supply the current accounting contract.
- Binding reference used for this review: `المرجع_النهائي_الموحد_المعتمد.md`; local-file SHA-256 `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`.
- Live `main/state.json` records CP-B1 complete, CP-B2 next, and CP-D still pending. The state file is not changed by this documentation proposal.

### Current three-way R4 comparison

| Item | current main | `stage3b-preserved` | binding reference / accepted evidence | judgment |
|---|---|---|---|---|
| Canonical Stage 12 contract | `docs/stage12/accounting_data_contract.json` and this R4 file are absent from current `main`; existing roll-forward and closure reports remain present. | No Stage 12 contract; the branch is diagnostic and its Stage 9-era state cannot define current Stage 12. | The reference defines accounting roll-forward requirements in §10.6, deterministic identity in §§14.3–14.4, the separate daily statistical output in §14.7, and output/quality requirements in §§15.1–15.6 and 18.1–18.2; it does not prescribe these GitHub file paths. | **DEVIATION** — a canonical contract is still missing from main. |
| Daily ledger schema | No canonical contract in main; current validation reports identify schema `stage12-daily-accounting-v1`. | No Stage 12 schema. | Accepted producer/aggregator evidence emits the 38 fields in v1.1 order, including `result_sha256`; types match the producer; only `Final_Close_Date` is nullable. Primary key: `(scenario_id, trial_id, date)`; `result_sha256` remains constant within each `(scenario_id, trial_id)`. | **MATCH** — proposed v1.1 schema matches the observed producer schema. |
| Dataset identity and observed counts | Current reports record `source_sha=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, seed `20270101`, global SHA `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`, 25 scenarios, 11,005 trials and 22,546,465 daily rows. | No comparable accepted Stage 12 output evidence. | §§14.3–14.4 govern deterministic identity. Run 37964656154 reports original/reproduced global SHA equality and zero retries; observed counts in v1.1 agree with validation reports. | **MATCH** — observed provenance/counts agree; no trial rerun is requested. |
| Accounting validation | `roll_forward_validation.json` (blob `6084e8f68fa649fcf0726daa04f41ae9b0636706`) and `closure_settlement_validation.json` (blob `81bc3cd9c7666487b69b644dcc3291d0547c8e8b`) each record `overall_result=PASS` and zero reported violations. | No Stage 12 validation outputs. | §10.6 requires roll-forward consistency; §§18.1–18.2 cover output requirements and quality. | **MATCH** for the reported validation scopes only; this does not assert the separate Stage 9C 20-point gate. |
| Accepted workflow topology | Current governance decision log records D3: 25 scenario materialization jobs plus validate and aggregate, 27 total. | No corresponding canonical topology. | User decision in `docs/governance/DECISIONS_LOG.md` dated 2026-10-09 accepts that topology; the reference does not define the historical 45-job design as a business rule. | **MATCH** — proposed v1.1 records 25 + 1 + 1 jobs, max parallel 25, and job timeouts 45/360/30 minutes. |
| Statistical-policy metadata | Current `docs/governance/DECISIONS_LOG.md`, D-2026-10-10-01, records the approved new policy as doubling from 300 (300→600→1200→2400→4800→9600→…), with no ceiling; it supersedes the previous +50 model for new execution. | The diagnostic branch does not override current governance decisions. | The approved current decision is authoritative for future execution. The dataset was produced by Run 37964656154 on 2026-10-09, before the decision dated 2026-10-10. | **DEVIATION requiring explicit disposition** — contract v1.1 `dataset_identity.stability_policy` says +50 and accepted N=550, conflicting with the later normative policy if read as current policy. This proposal preserves the field as historical dataset provenance and does not silently rewrite the decision log or observed dataset. It must not be used to claim future sampling-policy compliance. |
| Reference traceability | The 2026-10-10 R4 section cited its then-current base SHA and is preserved as historical. | Diagnostic branch provides no current reference substitute. | Direct check of the binding reference found no §12.17 heading/reference; relevant sections are §10.6, §§14.3–14.4, §14.7, §§15.1–15.6, the Chapter 16 acceptance inventory, and §§18.1–18.2. | **MATCH** — use these actual sections; do not cite a nonexistent §12.17. |

### Current R4 classification and disposition

- **MATCH:** v1.1's 38-field order, types, nullability, key, fingerprint metadata, Parquet representation, accepted 27-job topology, and recorded run/count/hash evidence match the current producer/validation evidence in the scoped review.
- **DEVIATION:** the canonical contract is absent from current main until merged.
- **DEVIATION requiring review:** `dataset_identity.stability_policy` records +50/550 while D-2026-10-10-01 is the newer normative policy for new execution. This CP preserves the observed dataset identity and exposes the conflict; it does not decide to alter the governance decision, replay data, or amend the accepted output identity.
- **VIOLATION:** no additional runtime violation is asserted by this documentation-only change. This is **not a CP-B2 PASS** and does not close the policy discrepancy or the independent CP-D gate.
- No engine, test, RNG, source reference, workflow, or `state.json` changes are included. No trial was rerun. The CP-B2 proposal remains for explicit review, with the policy discrepancy visible.

