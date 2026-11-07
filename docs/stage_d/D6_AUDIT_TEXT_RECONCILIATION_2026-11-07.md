# D6 Audit Text Reconciliation — 2026-11-07

D6 Run [42403657899](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42403657899), Job `128498571102`, tested SHA `42922d06637b7fad1d36c412e2253423f9367f34`, ran the pytest acceptance command and logged **8 passed in 523.32s**. `ACCEPTANCE_TEST_EXECUTION.json` records tests 175, 176, 179, 180, 181, 182, 183 and 186 as PASS on that exact SHA.

Selected `FINAL_AUDIT.md` / `FINAL_AUDIT.json` table details say the full historical acceptance contract was not executed. This conflicts with the execution fields and job log. Test 176 ran `tests.test_176_numeric_token_lineage::test_176_numeric_token_lineage`; its source asserts 241 total, 64 resolved, 177 explicitly classified, 0 unresolved, and `241 == 64 + 177 + 0`.

Correct interpretation: all eight named normative tests ran and passed. The separate full **177-unique-test suite** remains `NOT_RUN`; 177 in Test 176 counts numeric occurrences, not tests. D6 remains `PASS_SCOPED_WITH_LIMITATIONS`. Historical reports remain unchanged; this correction is append-only.


## D6 JSON writer root cause — verified from historical Job log (append-only)

Historical Run 42394060281 / Job 128467560335 / Tested SHA 40933aeaac12cef94882529655aa7626811d4bc4 failed with `JSONDecodeError: Extra data: line 72 column 2 (char 2860)`. The failing file was `docs/stage_d/D6_AUDIT_RUN_42394060281/ACCEPTANCE_TEST_EXECUTION.json` (2,862 bytes), not `D5_PACKAGE_PREFLIGHT_2026-11-07.json`. The historical writer in `.github/workflows/stage-d6-independent-audit.yml` line 109 appended literal backslash+n after the JSON object. The D5 preflight on that SHA is 2,388 bytes and parses as valid JSON.

The later D6 workflow revision writes a real newline. Run 42403657899 passed 49 unit tests and all eight normative tests (175, 176, 179, 180, 181, 182, 183, 186); Test 176 asserts 241 = 64 + 177 + 0. D6 remains PASS_SCOPED_WITH_LIMITATIONS and has not run on observed HEAD fa55d396b3f0d5af78a9086e3b481e2f925c112d. Historical reports remain unchanged.


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
