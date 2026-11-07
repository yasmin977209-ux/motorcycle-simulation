# D0–D6 Master Closure — 2026-11-07

| Stage | Status |
|---|---|
| D0 | `PASS_SCOPED_WITH_LIMITATIONS` |
| D1 | `PASS_SCOPED_WITH_LIMITATIONS` |
| D2 | `PASS_SCOPED_WITH_LIMITATIONS` |
| D3 | `PASS_GAP_FREE_NORMATIVE_V240_SCOPE` |
| D4 | `PASS_GAP_FREE` |
| D5 | `PASS_GAP_FREE` |
| D6 | `PASS_SCOPED_WITH_LIMITATIONS` |

Pre-update branch HEAD: `72c8f18f2e522b34e136c231bef52f1c3625c205`; protected main: `01a6f79eedc522bb734ed9c5ea31beee581f2468`; divergence 1,149 ahead / 2 behind; merge base `c6e54349a5e94f65d5aa9f83141f225d777bb474`. No main write, merge or Release.

D1-D2 Run 42403657890 and D3 Run 42403657857 tested `42922d0…`; D4 Run 42387025927 tested `1fb489…`; D5 Run 42393413807 tested `c757126…`; D6 Run 42403657899 tested `42922d0…`. Exact Final Head across D0-D6 is `NOT_ESTABLISHED`.

Detailed tri-hash reconciliation: 51/72 metadata MATCH, 21/72 NOT_COMPARABLE, zero mismatch. Provider raw-byte SHA-256, restore tests, E2 Replay 20 transfer and two independent durable failure domains remain unproven. Global Preservation Gate is `BLOCKED` independently before E3. Earlier D3 72/72 summary conflicts with the later detailed reconciliation; preserve both.

Project status: `T2_INTERIM / NOT_FINAL_BLOCKED`. Financial Gate A `PASS_SCOPED`; Production Gate A `NOT_DECLARED`; Gate B N=2400 `FAIL_SCOPED (10/10)`; Stability `NOT_CONVERGED (0/60)`; N=4800 `NOT_EXECUTED`. Five historical accounting fields remain MISSING_EVIDENCE. D6 is not final acceptance.

## Live reconciliation at fa55d396b3f0d5af78a9086e3b481e2f925c112d (2026-11-07)
- D0 Run 42283741942 tested afbc65bae45a53ccc14fd9098014494d09ec70e3: 27 Artifact-specific jobs and 27 Artifacts succeeded; D0 remains PASS_SCOPED_WITH_LIMITATIONS.
- D1-D2 Run 42407443585 / Job 128508085668 tested fa55d396b3f0d5af78a9086e3b481e2f925c112d: 36 passed; Artifact 13587689091, 10,545 bytes, SHA-256 174fc4e225186d9619db405cb7c952dfe659bb72aeb8b0b7fa3f9f8e168ea922.
- D3 Run 42407443559 / Job 128508085687 tested fa55d396b3f0d5af78a9086e3b481e2f925c112d: 38 passed; 35 committed files read back; no workbook rebuild.
- D4 exact-head gate Run 42407443567 / Job 128508085683 tested fa55d396b3f0d5af78a9086e3b481e2f925c112d: 5 passed; Artifact 13587862179, 6,325 bytes, SHA-256 aa974d58122ac02e35f30c24cdbd738be65f63be8919d00e8153719ed30cad45.
- D5 remains on c757126ac27e8f6606f38b14324119cc22604858; D6 remains on 42922d06637b7fad1d36c412e2253423f9367f34. Neither has run on fa55d396b3f0d5af78a9086e3b481e2f925c112d.
- Raw Readback Run 42407443575 tested fa55d396b3f0d5af78a9086e3b481e2f925c112d, compared 39 files, but its report JSON was malformed by a literal backslash+n suffix. The workflow correction and negative tests are included in this commit; post-push run is pending.
- Exact Final Head across D0-D6 remains NOT_ESTABLISHED. Global Preservation remains BLOCKED. Final Acceptance remains NOT_ACCEPTED.
