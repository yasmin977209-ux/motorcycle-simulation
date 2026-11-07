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


## Live reconciliation — 2026-11-08 (append-only)

Pre-C2 HEAD `3217ab43f587e468753d13952fdd16cb947259f8`; main `01a6f79eedc522bb734ed9c5ea31beee581f2468`.

D1-D2 Run 42419105795 / Job 128543480494: 37 passed on exact HEAD; Artifact 13593026097, 10,545 bytes, SHA-256 `b335be1aab68a85b0b085b018dd55272d1c3c9d18809efd61acc47b7ce1d5162`. D3 Run 42419105827 / Job 128543480974: 38 passed, 35 Raw readbacks, exact-head PASS. D6 Run 42419105855 / Job 128543481098: 49 auditor unit tests and 8 normative tests passed (175,176,179,180,181,182,183,186); Test 176 = `241 = 64 + 177 + 0`; Artifact 13592363586, 6,929 bytes, SHA-256 `cb57bb2edb5ad7f474ac5c6ab9f38add3a960325717698efe481ce23b0c95b60`. D6 disposition `PASS_SCOPED_WITH_LIMITATIONS`; Final Acceptance `NOT_ACCEPTED`.

Tri-hash Run 42416858162 is on older tested SHA `80c715d3ff489422ae2739627bb8819280ad48af`, not the pre-C2 HEAD. Artifact 13591479069: 20,502 bytes, SHA-256 `54ca0d9961b29af9fbdca5a60e491bac335485db0f34aade0fc7424e2313ba69`. Its 21 newly compared OneDrive references (D3S-010 + 20 multipart wrappers) MATCH; total 63/72 OneDrive metadata matches, 9 Dropbox reported-only, 0 mismatch, 0 not-comparable. This is metadata comparison only; raw-byte SHA-256 and restore remain NOT_RUN, E2 Replay 20 NOT_TRANSFERRED, Global Preservation BLOCKED.

D0 Run 42283741942 remains on `afbc65bae45a53ccc14fd9098014494d09ec70e3`; D4 Run 42387025927 on `1fb4898480629c0a327dbff13792d455cd205a59`; D5 Run 42393413807 on `c757126ac27e8f6606f38b14324119cc22604858`. Exact D0-D6 Final Head is NOT_ESTABLISHED. Project remains `T2_INTERIM / NOT_FINAL_BLOCKED`.
