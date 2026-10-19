# R4 — temporary read-only MaxCase/Stage 12 verifier

Date: 2026-10-19
Status: AUTHORIZED FOR ONE TEMPORARY READ-ONLY WORKFLOW; no assembler change yet.

## R4 matrix

| Item | Current state | Governing reference / decision | Exact requirement | Judgment |
|---|---|---|---|---|
| Workflow scope | Local Parquet reader unavailable; existing Stage 12 archive and validation reports are identified. | User's explicit M3 + scoped M5 authorization dated 2026-10-19; prior `docs/stage13/R4_MAXCASE_FROM_STAGE12_LEDGER_20261019.md`. | One temporary workflow on one pinned temporary branch; read only existing Stage 7/10/12 artifacts; no Trial/Monte Carlo/replay/data mutation. | AUTHORIZED within stated scope. |
| Token permissions | Artifact download needs the Actions API; repository file identity needs contents API. | GitHub Actions permission model; least-privilege rule. | `contents: read` and `actions: read` only; no write permissions, no secrets, no self-dispatch, no wildcard branch. | Read-only; `actions: read` is additionally required to fetch existing workflow artifacts. |
| Official source runs | Stage 7 Run `37225915321`, head `e0b2fab6710833774937d778097363d7a8ee8e59`; Stage 10 Run `37709936740`, live head `ca73f2df37baacebbcad965fc5f433f129675820`; Stage 12 Run `37964656154`, head `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`. | Main `docs/stage13/R4_gatea_golden_fingerprint_bridge.md`; Stage 9A manifest; Stage 12 roll-forward and closure reports. | Verify run/head/source identity and artifact identity; no production simulation. | Existing official evidence sources identified; per-row MaxCase proof pending. |
| MaxCase rule | No selected trial IDs have been verified yet. | D-2026-10-10-03 / Amendment-03, as recorded in the prior R4. | Highest positive `Final_Net_Project_Equity`; exact ties choose smallest integer `trial_id`; no positive row means `UNDEFINED_BUSINESS_RULE` and scenario hold. | Must implement as read-only analysis only; no rule/role change. |
| Daily completeness | Stage 12 reports 25 scenarios, 11,005 trials, 22,546,465 rows, global SHA-256 `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`. | Main `docs/stage12/roll_forward_validation.json` and `closure_settlement_validation.json`. | Verify every scenario's exact Parquet content hash, schema/identity, contiguous trial IDs, full per-trial date sequence, no duplicate/missing dates, constant `result_sha256`; compare the selected trial's summary fingerprint to its Stage 12 rows. | Pending hosted row-level verification. |
| Protected boundaries | No changes to main/state/reference/source/data/Parquet, no new trial, no Gate A production run. | Project protected-action list and scoped M5. | Keep workflow isolated to one temporary branch; delete workflow after evidence and verify absent; record all evidence append-only. | Enforced. |
| Assembler | Candidate `scripts/stage13_assemble.py` remains unchanged at blob `71e05034bafb551aea2949adc94013e8bb23d239`. | Prior R4 and user's scoped authorization. | No assembler edit until the row-level evidence is complete and a follow-up R4 is written. | HOLD. |

## Execution contract

- Temporary branch: `tmp/cp-maxcase-ledger-verify-20261019`, created from the verified Stage 13 candidate commit `c21b295cb3c421708e90e1f114a36d1c36b9e5dd`.
- Workflow path: `.github/workflows/cp-maxcase-ledger-readonly-verify.yml`; push-only trigger pinned to that exact branch; permissions `contents: read`, `actions: read`; no workflow_dispatch.
- Read only existing official Stage 7/10/12 artifacts. No engine invocation, Trial, Monte Carlo, checkpoint, replay, sampling, seed/RNG, threshold, cohort, trial ID, golden, source, or Parquet mutation.
- Save per-scenario selected IDs, official summary metric and result fingerprint, artifact/run provenance, ZIP/member SHA-256, all-trial daily row counts, date spans, gaps/duplicates, and exact output status to a workflow evidence artifact.
- If any source identity, artifact digest, schema, metric, or row coverage conflicts, stop and report the literal mismatch; do not edit the assembler.
- After evidence is collected, remove this single temporary workflow and verify it is absent before proceeding.
