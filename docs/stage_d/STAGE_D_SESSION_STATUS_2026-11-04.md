# Stage D Session Status — 2026-11-04

Repository: yasmin977209-ux/motorcycle-simulation
Working branch: tmp/d1-rebuild-20261101
Integrity audit workflow tested SHA: 9196b332b068a0db232420dcdf684f25542db34a

## Live stage disposition

- D0: PASS_SCOPED_WITH_LIMITATIONS (retained; no reopen).
- D1: PASS_SCOPED_WITH_LIMITATIONS (Run 41900246597, tested SHA d323300abaa361413091b3062e3417db62c18f56; 34 tests passed).
- D2: PASS_SCOPED_WITH_LIMITATIONS (Run 41900246597; Number Registry verified).
- D3 candidate Artifact 13288779998 integrity: PASS_SCOPED; D3-18 NOT_RUN; D3 gate BLOCKED_MISSING_EVIDENCE; integrity audit Run 41911722372.
- D4: NOT_STARTED; candidate D3 has not passed its delivery gate.
- D5: existing Artifact 13264003231 remains historical/unchanged; do not treat it as rebuilt from candidate D3.
- D6: prior independent audit remains BLOCKED; do not infer D6 closure from D3/D4 changes.
- E0–E6: NOT_STARTED.

## Candidate evidence

- D3 source Run: 41754147172; source SHA: 3325fd961005c2c47de071d25904a748af7a21a6.
- Candidate Artifact: 13288779998; size 535567142; SHA-256 e49b206d8d80034b1dc0cb284bfee76d81f9e9759e2459b1608fad2f5c933ffe.
- Financial Registry audit: Run 41900246587, tested SHA d323300abaa361413091b3062e3417db62c18f56, PASS_SCOPED.
- Governing reference v2.4.0 SHA-256: 225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b.
- Historical execution reference v2.3 SHA-256: e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f.

## Preserved limitations and prohibitions

- Full Logging: 105 representative keys only; C100 Golden: NOT_RUN.
- Five historical 48K accounting fields remain MISSING_EVIDENCE and must never be inferred or zero-filled: Accounts_Receivable, Accumulated_Depreciation, Gross_Bike_Assets, Guarantee_Claim_Receivable, Total_Assets.
- Financial Gate A PASS_SCOPED; Production Gate A NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS.
- Gate B at N=2400 FAIL_SCOPED (10/10); Stability NOT_CONVERGED (0/60); N=4800 NOT_EXECUTED.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, source/cohort/seed/Trial identity change.
- No historical Artifact or manifest was modified. No main write, merge, Release or final-acceptance declaration.
