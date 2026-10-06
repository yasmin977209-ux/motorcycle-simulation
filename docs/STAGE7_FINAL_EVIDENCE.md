# Stage 7 F4 Final Evidence

## Identity

- Run ID: `37482745008`
- Branch: `tmp/wf-002f6-f4safe-20261006`
- Commit: `9fa357e83a07544d070eb717a945257ce9954d6f`
- Verified at: `2026-10-06T15:19:16Z`

## F4 Results

- Simulation jobs: **25/25 success**.
- Restore evidence: **25/25** with `COUNT>0`.
- `derived == stored`: **25/25**.
- Official fingerprint match: **25/25**.
- State integrity errors: **0**.
- State branches: **25/25 v2 unchanged**.
- C100 golden match: **true**.

## C100 Golden Values

- `Final_Net_Project_Equity`: `209671000`
- `Partner1_Final_Entitlement`: `146769700`
- `Partner2_Final_Entitlement`: `62901300`
- `final_close_date`: `2033-01-06`

These values matched across the five C100 scenarios in F4.

## Official Stage 7 Artifacts

The official 25-scenario artifact set is referenced from Run `37225915321`. F4 restored using the explicit official artifact identities and verified the resulting fingerprints against the prior official checkpoint fingerprints.

## State Branch Consistency

All 25 Stage 7 state branches were checked by F4 with schema `stage7_state_v2`; the resulting state identities remained internally consistent and no `StateIntegrityError` occurred.
