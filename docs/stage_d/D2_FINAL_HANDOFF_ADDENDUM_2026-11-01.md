# D2 Final Handoff Addendum — 2026-11-01

This append-only addendum supersedes the older D2 run reference in the previous handoff section without deleting or rewriting that history.

## Verified final D2 disposition

- D2: `PASS_SCOPED_WITH_LIMITATIONS`.
- Definitive workflow: [Run 41326662869](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41326662869) — `SUCCESS`.
- Exact-head validated commit: `96a07b52485733115cf93875440ea99369a94fdb`.
- Working branch: `tmp/d1-rebuild-20261101`.
- `main`: `c6e54349a5e94f65d5aa9f83141f225d777bb474`, unchanged.
- Registry: 2,640 explicit entries; 1,000 daily series; 2,086,550 addressable Daily Distribution points; 24,136,918 bytes.
- Exact registry SHA-256: `b271cb638c89f6ff14e22e1cfbf5f4d7acc803e00a89eef7ff716ed386b89e3e`.
- Git blob SHA-1: `81e8c7cedcec1e75f86f00a198d93c82f1c4e99b`.
- Registry URL: https://github.com/yasmin977209-ux/motorcycle-simulation/blob/96a07b52485733115cf93875440ea99369a94fdb/results/number_registry.json

## Limitations retained

- Full Logging: 105 representative keys only; 105 normalized statuses remain `NOT_VERIFIED`.
- C100 remains separate under `CROSS_COHORT_DETERMINISTIC_REUSE`; Golden revalidation `NOT_RUN`.
- Gate A financial `PASS_SCOPED`; production Gate A `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`.
- Gate B N=2400 `FAIL_SCOPED (10/10)`; Stability `NOT_CONVERGED (0/60)`; N=4800 `NOT_EXECUTED`.
- The five historical accounting fields remain `MISSING_EVIDENCE`; do not infer, backfill or zero-fill.
- No Trial, Simulation, Monte Carlo or N expansion was run. D3 has not started.


## Final D2 resolver and canonical-audit correction — 2026-11-01

- Definitive corrected D2 workflow: [Run 41328486239](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41328486239) — SUCCESS.
- Registry commit and exact-head/raw-readback SHA: c5e9c862c161dea89651d27e3a4eb5f5f35211ad.
- Current registry URL: https://github.com/yasmin977209-ux/motorcycle-simulation/blob/c5e9c862c161dea89651d27e3a4eb5f5f35211ad/results/number_registry.json
- Registry SHA-256: d8c701d0fc35cbd1566ebced5ccc4f40bb3dafe538d020dd7c89b1ec326c66bb.
- Git blob SHA-1: 824803e8543fff7c628586bd37ea6e3f706cf9ba.
- Registry size: 24,137,036 bytes.
- Coverage remains 2,640 explicit entries, 1,000 daily series and 2,086,550 addressable daily points. Daily point IDs are now resolvable by scripts.s6_number_registry.resolve_number; the resolver returns the exact rational value and source provenance.
- D2 tests: 22 passed, 9 skipped (the documented D1 artifact-integration tests are supplied only by their separate integration validation); D1-D2 Source Validation on source HEAD 8048e980951cb34e5c023c1b51e7a2ac5970171d: 31 passed; exact branch/Raw readback on registry commit c5e9...: PASS.
- Uploaded D2 evidence Artifact 13092805269 (d2-number-registry), 3,583,890 bytes, ZIP SHA-256 ec6319663287d84e653a84d2398c23fea6e711652831015ff846ade467e1a1d7.
- Canonical D2_NUMBER_REGISTRY_AUDIT.json now reports PASS_SCOPED_WITH_LIMITATIONS and retains its former 13,954-entry local-only report under historical_local_report; that historic report is not the current registry.
- Scope restrictions remain: Full Logging 105 keys only and 105 normalized statuses NOT_VERIFIED; C100 remains separate as CROSS_COHORT_DETERMINISTIC_REUSE with Golden NOT_RUN; Gate A production NOT_DECLARED; Gate B FAIL_SCOPED (10/10); Stability NOT_CONVERGED (0/60); N=4800 NOT_EXECUTED; five accounting fields MISSING_EVIDENCE.
- No new Trial, Simulation, Monte Carlo, N expansion, historical backfill or zero-fill was performed. D3 has not started.
