# D1–D2 Documentation Reconciliation Addendum — 2026-11-01

Repository: `yasmin977209-ux/motorcycle-simulation`  
Working branch: `tmp/d1-rebuild-20261101`  
Baseline HEAD checked before this documentation-only update: `b2ebce62491c7602c71b5312b7ea24986bbb89f4`  
`main` at check time: `c6e54349a5e94f65d5aa9f83141f225d777bb474`  
Scope: append-only clarification of D1/D2 historical records. No source, artifact, business rule, identity, trial, or simulation data changed.

## 1. D1 — historical BLOCKED snapshots and current scoped closure

The following files are retained unchanged as historical audit snapshots:
- `docs/stage_d/D1_REBUILD_AUDIT_2026-11-01.json` — records the earlier pre-publication disposition.
- `docs/stage_d/D1_BUILDER_AUDIT.json` — records the earlier builder/pre-publication disposition.
- `docs/stage_d/D1_REBUILD_DESIGN_2026-11-01.md` — design-time classification, not a current closure record.

Their earlier `BLOCKED` fields are not the current D1 disposition. The later append-only correction already present in `docs/stage_d/D1_REBUILD_CLOSURE_2026-11-01.md` (section “D1 status corrected from BLOCKED to PASS_SCOPED_WITH_LIMITATIONS after successful reference publication”) explicitly supersedes the earlier BLOCKED status while preserving it historically. This addendum makes that precedence explicit; it does not rewrite or delete the historical JSON snapshots.

Current scoped validation evidence:
- D1 source validation Run [41344529037](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41344529037): SUCCESS; 25 passed, 9 skipped.
- Combined D1/D2 source validation Run [41344528986](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41344528986): SUCCESS; 34 passed, 0 failed, 0 skipped.
- Both runs tested source SHA `de12b42ee371ec12675b1110facd6d2da25eb781`.
- GitHub compare from that tested SHA to pre-update branch HEAD `b2ebce62491c7602c71b5312b7ea24986bbb89f4` shows only three D3 output/report files added; no D1 or D2 source or registry files changed in that interval.

Disposition: D1 remains `PASS_SCOPED_WITH_LIMITATIONS`. The old BLOCKED JSON snapshots remain `REPORTED_ONLY` as historical audit states, not current stage status. No claim of unqualified/full project acceptance is made.

## 2. D2 — registry evidence reconciliation

The older registry triple in the initial completion record (Run `41333300530`, registry SHA-256 `47e72ecae6f8c9f8cff3c8599909c42bf5e8a4ddaa3d3bceb0be764717b7b321`, blob `ba7ead51a67b244ebfcb87d35be59dbaf62fccfc`, registry-containing commit `50673bf094c38e8a73de2980df719df2963a3dc6`) is retained as valid historical evidence for that earlier registry generation. It is not the latest D2 registry evidence and must not be presented as the current registry triple.

Latest D2 completion record:
- Completion workflow Run [41335321803](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41335321803): SUCCESS.
- Registry path: `results/number_registry.json`.
- Registry-containing commit: `cc94985454d6e5971947e53c8e0a2782ad2de12d`.
- Latest registry SHA-256: `743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87`.
- Git blob SHA-1: `8cf17de488c623f96c1961ca91d682fbbc7733d6`.
- Size: `24,137,036` bytes.
- Final raw readback commit recorded for the registry: `46c86795d64311b53106fb0b7a79f8bcde116112`.
- Artifact produced by the completion run: [13094379705](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41335321803/artifacts/13094379705).
- Follow-up combined D1/D2 validation: Run `41344528986`, SUCCESS, 34 passed, 0 failed, 0 skipped, tested SHA `de12b42ee371ec12675b1110facd6d2da25eb781`.

Accordingly, the appended older registry table entries in the D2 matrix and ledger are historical, not deleted or silently rewritten. The current evidence triple is the `743ffcc...` / `8cf17d...` / `cc949854...` record above, with the final raw-readback commit separately identified as `46c86795...`. The D2 canonical audit JSON already contains the latest SHA-256, blob SHA-1, size and workflow ID `41335321803`.

Disposition: D2 remains `PASS_SCOPED_WITH_LIMITATIONS`. This reconciliation does not upgrade Full Logging beyond 105 representative keys, does not mark normalized 105/105 statuses verified, does not run C100 Golden revalidation, and does not alter any financial/production/Gate B/Stability/N=4800 status.

## 3. Invariants preserved

- Financial Gate A: `PASS_SCOPED` only.
- Production Gate A: `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`.
- Gate B N=2400: `FAIL_SCOPED (10/10)`.
- Stability: `NOT_CONVERGED (0/60)`.
- N=4800: `NOT_EXECUTED`.
- Full Logging: 105 representative keys only; normalized status remains `NOT_VERIFIED_105_OF_105`.
- C100 Golden revalidation: `NOT_RUN`.
- The five missing fields remain `MISSING_EVIDENCE`, with no inference or zero-fill: `Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Total_Assets`.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, main update, merge, or Release was performed or authorized by this addendum.
- D3 remains `BLOCKED_MISSING_EVIDENCE`; D4–D6 and E0–E6 remain `NOT_STARTED`.

## 4. Audit trail

This is an append-only reconciliation note. Earlier audit files, hashes, commits, workflow records and historical dispositions are preserved. This addendum does not claim its own remote evidence triple until its post-commit GitHub readback is completed.
