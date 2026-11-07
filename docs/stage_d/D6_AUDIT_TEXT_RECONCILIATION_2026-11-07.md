# D6 Audit Text Reconciliation — 2026-11-07

D6 Run [42403657899](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42403657899), Job `128498571102`, tested SHA `42922d06637b7fad1d36c412e2253423f9367f34`, ran the pytest acceptance command and logged **8 passed in 523.32s**. `ACCEPTANCE_TEST_EXECUTION.json` records tests 175, 176, 179, 180, 181, 182, 183 and 186 as PASS on that exact SHA.

Selected `FINAL_AUDIT.md` / `FINAL_AUDIT.json` table details say the full historical acceptance contract was not executed. This conflicts with the execution fields and job log. Test 176 ran `tests.test_176_numeric_token_lineage::test_176_numeric_token_lineage`; its source asserts 241 total, 64 resolved, 177 explicitly classified, 0 unresolved, and `241 == 64 + 177 + 0`.

Correct interpretation: all eight named normative tests ran and passed. The separate full **177-unique-test suite** remains `NOT_RUN`; 177 in Test 176 counts numeric occurrences, not tests. D6 remains `PASS_SCOPED_WITH_LIMITATIONS`. Historical reports remain unchanged; this correction is append-only.


## D6 JSON writer root cause — verified from historical Job log (append-only)

Historical Run 42394060281 / Job 128467560335 / Tested SHA 40933aeaac12cef94882529655aa7626811d4bc4 failed with `JSONDecodeError: Extra data: line 72 column 2 (char 2860)`. The failing file was `docs/stage_d/D6_AUDIT_RUN_42394060281/ACCEPTANCE_TEST_EXECUTION.json` (2,862 bytes), not `D5_PACKAGE_PREFLIGHT_2026-11-07.json`. The historical writer in `.github/workflows/stage-d6-independent-audit.yml` line 109 appended literal backslash+n after the JSON object. The D5 preflight on that SHA is 2,388 bytes and parses as valid JSON.

The later D6 workflow revision writes a real newline. Run 42403657899 passed 49 unit tests and all eight normative tests (175, 176, 179, 180, 181, 182, 183, 186); Test 176 asserts 241 = 64 + 177 + 0. D6 remains PASS_SCOPED_WITH_LIMITATIONS and has not run on observed HEAD fa55d396b3f0d5af78a9086e3b481e2f925c112d. Historical reports remain unchanged.
