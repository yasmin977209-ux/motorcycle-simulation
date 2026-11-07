# Stage D Continuity Handoff — 2026-11-07

Append-only handoff. Preserve historical run outcomes and use only exact Tested SHA and Exact Final HEAD evidence.


## D5 publication record correction — 2026-11-05 (append-only)

- D5 Run 41928234377 tested source SHA: baf696af1e951cbf4a79e8a9e009c60c6b053b2d. The workflow committed publication evidence as 4c6a84b10ac78b6067175d0eafa149f3f12dbc2a; the earlier `publication_commit_sha` field and prose entry naming baf696... identify the triggering/tested SHA, not the documentation commit.
- D5 matrix path is dated 2026-11-05, but its internal title says 2026-11-03; this is a stale title only and does not change package bytes or test results.
- D5 exact-final-head Raw readback was performed at 4c6a84b10ac78b6067175d0eafa149f3f12dbc2a.

## D6 independent post-write audit — 2026-11-05 (append-only)

- Run 42403657899; tested source SHA 42922d06637b7fad1d36c412e2253423f9367f34; D5 Artifact 13582441423 from Run 42393413807.
- Disposition PASS_SCOPED_WITH_LIMITATIONS; classification T2_INTERIM / NOT_FINAL_BLOCKED.
- See docs/stage_d/D6_AUDIT_RUN_42403657899/FINAL_AUDIT.md and FINAL_AUDIT.json for check-level results and limitations.
- D6 is not P17 acceptance, FINAL_ACCEPTED, CONVERGED or release authorization.

## 2026-11-07 — Live evidence recovery continuation (append-only)

- Pre-update HEAD: `72c8f18f2e522b34e136c231bef52f1c3625c205`; protected main: `01a6f79eedc522bb734ed9c5ea31beee581f2468`.
- D0/D1/D2: `PASS_SCOPED_WITH_LIMITATIONS`; Run 42403657890, Job 128496620691, SHA 42922, 36 passed, Artifact 13586712091.
- D3: `PASS_GAP_FREE_NORMATIVE_V240_SCOPE`; Run 42403657857 on SHA 42922. Global Preservation is separate and remains BLOCKED.
- D4: `PASS_GAP_FREE` on SHA 1fb489 (Run 42387025927). D5: `PASS_GAP_FREE` on SHA c757126 (Run 42393413807; Artifact 13582441423). D6: `PASS_SCOPED_WITH_LIMITATIONS` on SHA 42922 (Run 42403657899); tests 175/176/179/180/181/182/183/186 all PASS; Test 176 = 241 = 64 + 177 + 0.
- D6 wording conflict corrected append-only; full 177-unique-test suite remains NOT_RUN.
- Tri-hash: 51/72 MATCH, 21/72 NOT_COMPARABLE; raw-byte SHA-256 and restore NOT_RUN; E2 Replay 20 not transferred; two independent durable failure domains not proven.
- Exact Final Head across D0-D6: NOT_ESTABLISHED. Overall `T2_INTERIM / NOT_FINAL_BLOCKED`.

New records: REV7, D0-D2 effective closure, D5-D6 aggregate closure, D0-D6 master closure, 72-object metadata ledger, blocker register, D6 wording reconciliation and current pointer. Post-write raw readback is required before assigning SHA-256/commit triples.

## Resume point after live reconciliation — 2026-11-07

Current branch before commit: fa55d396b3f0d5af78a9086e3b481e2f925c112d; main: 01a6f79eedc522bb734ed9c5ea31beee581f2468. After this documentation/workflow commit, inspect the new Raw Readback run on the new exact HEAD. D0, D5 and D6 remain on older Tested SHAs and must not be represented as tested on the new HEAD. The raw-readback workflow is corrected to write parseable JSON, enforce expected SHA-256 values, deduplicate paths and run eight negative checks. Next blockers: verify 72 raw-byte hashes and restore; transfer E2 Replay 20; resolve 21 NOT_COMPARABLE items; confirm independent failure domains; obtain a transfer route for the 519 MB D5 artifact; run missing stage validations only through authorized read-only workflows. Keep main read-only and project status T2_INTERIM / NOT_FINAL_BLOCKED.


## Live reconciliation — 2026-11-08 (append-only)

Pre-C2 branch HEAD: `3217ab43f587e468753d13952fdd16cb947259f8`; protected main: `01a6f79eedc522bb734ed9c5ea31beee581f2468`.

### Exact-head C1 validation
- D1-D2 Run [42419105795](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42419105795), Job `128543480494`, tested `3217ab43f587e468753d13952fdd16cb947259f8`: **37 passed, 0 failed**. Artifact 13593026097: 10,545 bytes; SHA-256 `b335be1aab68a85b0b085b018dd55272d1c3c9d18809efd61acc47b7ce1d5162`.
- D3 Run [42419105827](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42419105827), Job `128543480974`, tested `3217ab43f587e468753d13952fdd16cb947259f8`: **38 passed**, 35 committed files read back from exact GitHub Raw SHA; exact-head PASS.
- D6 Run [42419105855](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42419105855), Job `128543481098`, tested `3217ab43f587e468753d13952fdd16cb947259f8`: 49 auditor unit tests passed (2 warnings) and 8 normative tests passed in 473.04s. IDs 175,176,179,180,181,182,183,186; Test 176 = `241 = 64 + 177 + 0`. Artifact 13592363586: 6,929 bytes; SHA-256 `cb57bb2edb5ad7f474ac5c6ab9f38add3a960325717698efe481ce23b0c95b60`. D6 `PASS_SCOPED_WITH_LIMITATIONS`; final acceptance `NOT_ACCEPTED`.

### Tri-hash — different tested SHA
Run 42416858162 tested `80c715d3ff489422ae2739627bb8819280ad48af`, not current branch HEAD. Artifact 13591479069: 20,502 bytes; SHA-256 `54ca0d9961b29af9fbdca5a60e491bac335485db0f34aade0fc7424e2313ba69`. The 21 newly compared OneDrive objects (D3S-010 + 20 multipart wrappers) MATCH; 63/72 OneDrive metadata matches, 9 Dropbox `REPORTED_ONLY`, 0 mismatch, 0 not-comparable. Provider raw-byte SHA-256 and restore remain `NOT_RUN`; E2 Replay 20 `NOT_TRANSFERRED`; Global Preservation `BLOCKED`.

### Historical stage SHAs and fixed limits
D0 Run 42283741942 tested `afbc65bae45a53ccc14fd9098014494d09ec70e3`; D4 Run 42387025927 tested `1fb4898480629c0a327dbff13792d455cd205a59`; D5 Run 42393413807 tested `c757126ac27e8f6606f38b14324119cc22604858`. These historical results do not migrate to `3217ab43f587e468753d13952fdd16cb947259f8`. Exact D0-D6 Final Head remains `NOT_ESTABLISHED` pending post-C2 final-head workflows.

Financial Gate A `PASS_SCOPED`; Production Gate A `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`; Gate B N=2400 `FAIL_SCOPED (10/10)`; Stability `NOT_CONVERGED (0/60)`; N=4800 `NOT_EXECUTED`; Full Logging 105 representative keys only. Five accounting fields remain missing and must not be guessed or zero-filled. Project status `T2_INTERIM / NOT_FINAL_BLOCKED`.
