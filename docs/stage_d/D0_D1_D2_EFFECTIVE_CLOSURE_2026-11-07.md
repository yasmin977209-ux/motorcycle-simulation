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
