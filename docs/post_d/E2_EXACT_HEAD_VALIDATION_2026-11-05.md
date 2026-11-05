# Exact-HEAD Validation Record — E0–E2 Gap Disposition — 2026-11-05

## Candidate HEAD tested

- Repository: `yasmin977209-ux/motorcycle-simulation`
- Branch: `tmp/d1-rebuild-20261101`
- Tested candidate HEAD: `225974b05527dbf2fb27d0542ae2fd7b77413774`
- main: `01a6f79eedc522bb734ed9c5ea31beee581f2468`
- All three workflow runs below completed after the consolidated gap report and continuity updates were committed and read back.

| Scope | Run / Job | Tested SHA | Result |
|---|---|---|---|
| D1–D2 | [41954633832](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41954633832) / 127006466583 | `225974b05527dbf2fb27d0542ae2fd7b77413774` | SUCCESS; 34 passed, 0 failed, 0 skipped |
| D3 | [41954633860](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41954633860) / 127006467211 | `225974b05527dbf2fb27d0542ae2fd7b77413774` | SUCCESS; 35 committed Raw files read back |
| D0–D4 | [41954633829](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41954633829) / 127006467170 | `225974b05527dbf2fb27d0542ae2fd7b77413774` | SUCCESS; five DOCX reopened, pagination/fingerprints, focused tests and Raw readback |

D0–D4 evidence Artifact 13382253631: 5,698 bytes; SHA-256 `d7811702f0e8365ca888bc49ec2652877d4d451beb4a54d87e43c0a7abcae718`; expiry 2026-12-05T02:21:52Z.

## What this does and does not close

This closes the exact-head validation race for candidate `225974b05527dbf2fb27d0542ae2fd7b77413774` across D1–D2, D3 and D0–D4. It does not upgrade any scoped stage disposition, close Production Gate A, pass Gate B, establish Stability, execute N=4800, run the full 177-test suite, or invoke Tests 176/179/180/181/183 or historical invocations 175/182/186.

The E2 historical accounting gap remains open: all five fields remain `MISSING_EVIDENCE`; Production Gate A remains `NOT_DECLARED`. No deterministic replay is authorized or performed. Owner must choose Option A or B in `E2_OWNER_DECISION_REQUIRED.md`.

The prior Run 41952532356 exact-head mismatch is retained as historical evidence. It is superseded for candidate `225974b05527dbf2fb27d0542ae2fd7b77413774` by Run 41954633829, not deleted or rewritten.

This record is being committed after the candidate validation. The commit containing this record is a new HEAD and must be checked by its own triggered exact-head workflows; do not attribute the runs above to that later commit.
