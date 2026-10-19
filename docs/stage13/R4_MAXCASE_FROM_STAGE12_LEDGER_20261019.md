# R4 — derive Stage 13 MaxCase from existing Stage 12 ledger

Date: 2026-10-19
Status: R4 design completed; row-level proof BLOCKED by missing local Parquet reader. No assembler change authorized or performed.

## Scope and invariants
Read-only use of already-completed official outputs only. No Monte Carlo, Trial, checkpoint, replay, source/data/Parquet rewrite, seed/RNG/sampling/cohort/threshold/trial-ID change, test/workflow change, manifest change, main/state change, merge, or release.

## R4 matrix

| Item | Current state | Governing reference / decision | Exact governing text or requirement | Judgment |
|---|---|---|---|---|
| Role selection | Candidate Stage 13 assembler implements MaxCase but no Stage 12 ledger reader. | Main `docs/governance/DECISIONS_LOG.md`, D-2026-10-10-03; `docs/governance/REFERENCE_AMENDMENTS.md`, Amendment-03. | MaxCase is the highest positive `Final_Net_Project_Equity`; ties choose the smallest `trial_id`; if no positive value exists, record `UNDEFINED_BUSINESS_RULE` and hold approval. | Rule defined; actual selected ID not yet proven. |
| Official daily source | Run `37964656154`, head `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`; source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`; seed `20270101`; schema `stage12-daily-accounting-v1`; 25 scenarios, 11,005 trials, 22,546,465 daily rows; global SHA `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`. | Main `docs/stage12/roll_forward_validation.json` blob `6084e8f68fa649fcf0726daa04f41ae9b0636706`; `closure_settlement_validation.json` blob `81bc3cd9c7666487b69b644dcc3291d0547c8e8b`. | Source identity and global dataset identity must match exactly. The validation reports say PASS for their stated checks only. | Identity is documented; row-level selected-ID/coverage proof pending. |
| C050_G000 archive | Artifact `11634501915`; ZIP SHA-256 `7d67097186dad801c6f0377a70decb5cf8dadea8f82a0b86956823a6a4191cf1`; member SHA-256 `6beecb837a3c6b71f34aedbeb958e8dd176cce3d60b2dfa1b95ee9bd57e6a380`; member size 128,155,763 bytes. | Same official roll-forward validation report. | Archive and member digests must match recorded artifact evidence before parsing. | ZIP/member hashes match the recorded evidence; no row values read yet. |
| Summary source for selection | Stage 12 daily Parquet provides daily accounting and `result_sha256`; selection requires exact final TrialResult metric and should not approximate it from daily rows. | Main `docs/stage13/R4_gatea_golden_fingerprint_bridge.md` blob `4fdff4a41c9610a9815f5adfbf23d6f1913971c5`; Stage 7/10 source artifacts and their identity metadata. | Verify exact source golden fingerprint, source SHA, scenario, trial ID and originating run; do not infer TrialResult metrics from daily approximations. | Selection must join official TrialResult summary metrics to Stage 12 daily rows by exact `(scenario_id, trial_id)`. |
| Completeness | Official aggregate reports 22,546,465 rows, 11,005 trials and no listed roll-forward/closure violations. | Stage 12 roll-forward and closure validation reports. | For each selected ID require one contiguous daily date sequence, full row count for that trial, one constant result fingerprint, no duplicate/missing dates, matching scenario/source/seed/schema and exact `trial_id`. | Aggregate completeness reported; MaxCase-specific completeness not yet proven. |
| Reader availability | Local runtime has neither `pyarrow` nor `fastparquet`; `pip install pyarrow` failed because package index DNS/network is unavailable. | Runtime environment observation on 2026-10-19. | Do not alter or rewrite the Parquet to work around a missing reader. | `BLOCKED_ENVIRONMENT`; use a controlled hosted runner with pinned dependencies and read-only artifact access, or an already-approved equivalent. |
| Protected changes | No new workflow or tests were changed for this R4. | Project rules: tests/workflows are protected and require separate explicit authorization; do not create wildcard/self-dispatch workflows. | Any temporary verifier must be pinned to one exact temporary branch, least privilege `contents: read`, read existing artifact IDs only, no model execution, no write access, and remove workflow only after its evidence is captured. | Workflow creation is a separate M5 approval gate. |
| Assembler | No changes made. | Candidate `scripts/stage13_assemble.py` blob `71e05034bafb551aea2949adc94013e8bb23d239`. | R4 and row-level proof must precede any assembler edit. | HOLD. |

## Required proof protocol
1. Use only the exact official Stage 7/Stage 10 TrialResult artifacts already approved for each scenario; verify their artifact/run IDs, hashes, source identity and each row's canonical result fingerprint. Do not use Stage 12 daily rows to approximate `Final_Net_Project_Equity`.
2. For each of the 25 scenarios, choose the row with maximum positive `Final_Net_Project_Equity`; among exact ties choose minimum integer `trial_id`. If no positive row exists, emit `UNDEFINED_BUSINESS_RULE` and block that scenario.
3. Read the matching official Stage 12 Parquet artifact for the same scenario and verify source SHA, seed, schema, artifact/member SHA, unique/contiguous trial IDs, exact selected-ID binding, full date continuity and complete rows, constant per-trial `result_sha256`, and consistency with the canonical result fingerprint.
4. Record per-scenario selected ID, metric value, trial-result source artifact ID/digest, daily artifact ID/digest, row count, first/last date, date-gap/duplicate counts, result SHA and exact test output. No output may be labelled PASS if any field is missing.
5. Only after this evidence is read back and independently checked may a second R4 authorize the minimal candidate assembler integration. Do not change tests/workflows without separate explicit authorization.

## Disposition
- Official Stage 12 source existence: VERIFIED at artifact/member identity level for C050_G000.
- MaxCase trial ID selection: MISSING_EVIDENCE.
- Complete daily rows for selected MaxCase: MISSING_EVIDENCE.
- Local pyarrow installation: BLOCKED by unavailable network/package index.
- Stage 13 assembler edit: HOLD pending row-level evidence and separate scope authorization.
- Canonical Stage 13 and final delivery: BLOCKED.
