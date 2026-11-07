# D5–D6 Aggregate Closure — 2026-11-07

## D5 — `PASS_GAP_FREE`
Run [42393413807](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42393413807), Job `128465567045`, tested SHA `c757126ac27e8f6606f38b14324119cc22604858`. Artifact 13582441423: 519,117,017 bytes; SHA-256 `ae84c0e9c27d5a0be7c5c37ec1f923676745013b86e3fd528178d830df61d0cc`. Inner package: 8 members; 519,104,624 bytes; SHA-256 `f7004da675f2af8d3201ed1b51d5106b890fe521ab66e198c635be414e5421c7`. D6 independently downloaded and checked the D5 Artifact.

## D6 — `PASS_SCOPED_WITH_LIMITATIONS`
Run [42403657899](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42403657899), Job `128498571102`, tested SHA `42922d06637b7fad1d36c412e2253423f9367f34`. Tests 175, 176, 179, 180, 181, 182, 183 and 186: **8 passed in 523.32 seconds**. Test 176: 241 = 64 + 177 + 0. Artifact 13586354284: 8,217 bytes; SHA-256 `2bbd2edb3a948891c1da376079b93b6b3bbdb6d0a7149ec3859a62e81f2a20f1`.

An append-only correction resolves conflicting wording in the run-specific report. The eight named normative tests passed; the separate full 177-unique-test suite remains `NOT_RUN`. Exact Final HEAD on D4/D5/D6 remains unestablished.

## Live D5/D6 reconciliation — 2026-11-07
- D5 Run 42393413807 / Job 128465567045 tested c757126ac27e8f6606f38b14324119cc22604858; Artifact 13582441423: 519,117,017 bytes; SHA-256 ae84c0e9c27d5a0be7c5c37ec1f923676745013b86e3fd528178d830df61d0cc; 8 package members. D6 downloaded and cryptographically checked this exact artifact.
- D6 Run 42403657899 / Job 128498571102 tested 42922d06637b7fad1d36c412e2253423f9367f34; 49 unit tests and 8 normative tests passed; Test 176 = 241 = 64 + 177 + 0. D6 remains PASS_SCOPED_WITH_LIMITATIONS.
- Root cause: historical D6 writer created invalid ACCEPTANCE_TEST_EXECUTION.json by appending literal backslash+n; the exact run log ties it to JSONDecodeError at line 72 column 2 char 2860. The later D6 workflow corrected the writer. D5_PACKAGE_PREFLIGHT on 40933 is valid JSON.
- D6 has not run on observed HEAD fa55d396b3f0d5af78a9086e3b481e2f925c112d; the full 177-unique-test suite remains NOT_RUN. D5/D6 exact final head remains NOT_ESTABLISHED.
- D5 full artifact external OneDrive upload was blocked by the 100 MiB source-file limit. Global Preservation remains BLOCKED independently of D5/D6 Stage disposition.


## Live reconciliation — 2026-11-08 (append-only)

Pre-C2 HEAD `3217ab43f587e468753d13952fdd16cb947259f8`; main `01a6f79eedc522bb734ed9c5ea31beee581f2468`.

D1-D2 Run 42419105795 / Job 128543480494: 37 passed on exact HEAD; Artifact 13593026097, 10,545 bytes, SHA-256 `b335be1aab68a85b0b085b018dd55272d1c3c9d18809efd61acc47b7ce1d5162`. D3 Run 42419105827 / Job 128543480974: 38 passed, 35 Raw readbacks, exact-head PASS. D6 Run 42419105855 / Job 128543481098: 49 auditor unit tests and 8 normative tests passed (175,176,179,180,181,182,183,186); Test 176 = `241 = 64 + 177 + 0`; Artifact 13592363586, 6,929 bytes, SHA-256 `cb57bb2edb5ad7f474ac5c6ab9f38add3a960325717698efe481ce23b0c95b60`. D6 disposition `PASS_SCOPED_WITH_LIMITATIONS`; Final Acceptance `NOT_ACCEPTED`.

Tri-hash Run 42416858162 is on older tested SHA `80c715d3ff489422ae2739627bb8819280ad48af`, not the pre-C2 HEAD. Artifact 13591479069: 20,502 bytes, SHA-256 `54ca0d9961b29af9fbdca5a60e491bac335485db0f34aade0fc7424e2313ba69`. Its 21 newly compared OneDrive references (D3S-010 + 20 multipart wrappers) MATCH; total 63/72 OneDrive metadata matches, 9 Dropbox reported-only, 0 mismatch, 0 not-comparable. This is metadata comparison only; raw-byte SHA-256 and restore remain NOT_RUN, E2 Replay 20 NOT_TRANSFERRED, Global Preservation BLOCKED.

D0 Run 42283741942 remains on `afbc65bae45a53ccc14fd9098014494d09ec70e3`; D4 Run 42387025927 on `1fb4898480629c0a327dbff13792d455cd205a59`; D5 Run 42393413807 on `c757126ac27e8f6606f38b14324119cc22604858`. Exact D0-D6 Final Head is NOT_ESTABLISHED. Project remains `T2_INTERIM / NOT_FINAL_BLOCKED`.
