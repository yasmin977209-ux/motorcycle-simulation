# D0–D2 Effective Closure — 2026-11-07

- Branch `tmp/d1-rebuild-20261101`; pre-update HEAD `72c8f18f2e522b34e136c231bef52f1c3625c205`; main `01a6f79eedc522bb734ed9c5ea31beee581f2468`.
- D1-D2 Run [42403657890](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42403657890), Job `128496620691`, tested SHA `42922d06637b7fad1d36c412e2253423f9367f34`: **36 passed, 0 failed**.
- Artifact 13586712091: 10,545 bytes; SHA-256 `a503f6646a5569143e0d5b1233b0534a69612f8e000aad54b3eeabc9f67be6dd`.

| Stage | Status | Limits |
|---|---|---|
| D0 | `PASS_SCOPED_WITH_LIMITATIONS` | Full Parquet matrix, 48K ledgers and source_run_metadata.sha256 remain missing. |
| D1 | `PASS_SCOPED_WITH_LIMITATIONS` | 105/105 representative keys; importer and full 48K remain unverified. |
| D2 | `PASS_SCOPED_WITH_LIMITATIONS` | 2,640 entries, 1,000 daily series, 2,086,550 points; C100 Golden NOT_RUN. |

Financial Gate A `PASS_SCOPED`; Production Gate A `NOT_DECLARED`; Gate B N=2400 `FAIL_SCOPED (10/10)`; Stability `NOT_CONVERGED (0/60)`; N=4800 `NOT_EXECUTED`. Five accounting fields remain `MISSING_EVIDENCE`: `Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Total_Assets`.

Exact Final HEAD is `NOT_ESTABLISHED`: run 42403657890 tested 42922, not observed HEAD 72c8.

## Current live source validation — 2026-11-07
D1-D2 Run 42407443585 / Job 128508085668 tested exact HEAD fa55d396b3f0d5af78a9086e3b481e2f925c112d: 36 passed, 0 failed. Artifact 13587689091: 10,545 bytes; SHA-256 174fc4e225186d9619db405cb7c952dfe659bb72aeb8b0b7fa3f9f8e168ea922. D1 and D2 remain PASS_SCOPED_WITH_LIMITATIONS. D0 was not rerun on this SHA and remains supported by Run 42283741942 on afbc65. C100 Golden revalidation remains NOT_RUN; independent Builder importer and two clean rebuilds remain NOT_RUN.


## Live reconciliation — 2026-11-08 (append-only)

Pre-C2 HEAD `3217ab43f587e468753d13952fdd16cb947259f8`; main `01a6f79eedc522bb734ed9c5ea31beee581f2468`.

D1-D2 Run 42419105795 / Job 128543480494: 37 passed on exact HEAD; Artifact 13593026097, 10,545 bytes, SHA-256 `b335be1aab68a85b0b085b018dd55272d1c3c9d18809efd61acc47b7ce1d5162`. D3 Run 42419105827 / Job 128543480974: 38 passed, 35 Raw readbacks, exact-head PASS. D6 Run 42419105855 / Job 128543481098: 49 auditor unit tests and 8 normative tests passed (175,176,179,180,181,182,183,186); Test 176 = `241 = 64 + 177 + 0`; Artifact 13592363586, 6,929 bytes, SHA-256 `cb57bb2edb5ad7f474ac5c6ab9f38add3a960325717698efe481ce23b0c95b60`. D6 disposition `PASS_SCOPED_WITH_LIMITATIONS`; Final Acceptance `NOT_ACCEPTED`.

Tri-hash Run 42416858162 is on older tested SHA `80c715d3ff489422ae2739627bb8819280ad48af`, not the pre-C2 HEAD. Artifact 13591479069: 20,502 bytes, SHA-256 `54ca0d9961b29af9fbdca5a60e491bac335485db0f34aade0fc7424e2313ba69`. Its 21 newly compared OneDrive references (D3S-010 + 20 multipart wrappers) MATCH; total 63/72 OneDrive metadata matches, 9 Dropbox reported-only, 0 mismatch, 0 not-comparable. This is metadata comparison only; raw-byte SHA-256 and restore remain NOT_RUN, E2 Replay 20 NOT_TRANSFERRED, Global Preservation BLOCKED.

D0 Run 42283741942 remains on `afbc65bae45a53ccc14fd9098014494d09ec70e3`; D4 Run 42387025927 on `1fb4898480629c0a327dbff13792d455cd205a59`; D5 Run 42393413807 on `c757126ac27e8f6606f38b14324119cc22604858`. Exact D0-D6 Final Head is NOT_ESTABLISHED. Project remains `T2_INTERIM / NOT_FINAL_BLOCKED`.
