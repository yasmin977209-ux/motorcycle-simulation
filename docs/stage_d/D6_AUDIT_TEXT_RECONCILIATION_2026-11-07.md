# D6 Audit Text Reconciliation — 2026-11-07

D6 Run [42403657899](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42403657899), Job `128498571102`, tested SHA `42922d06637b7fad1d36c412e2253423f9367f34`, ran the pytest acceptance command and logged **8 passed in 523.32s**. `ACCEPTANCE_TEST_EXECUTION.json` records tests 175, 176, 179, 180, 181, 182, 183 and 186 as PASS on that exact SHA.

Selected `FINAL_AUDIT.md` / `FINAL_AUDIT.json` table details say the full historical acceptance contract was not executed. This conflicts with the execution fields and job log. Test 176 ran `tests.test_176_numeric_token_lineage::test_176_numeric_token_lineage`; its source asserts 241 total, 64 resolved, 177 explicitly classified, 0 unresolved, and `241 == 64 + 177 + 0`.

Correct interpretation: all eight named normative tests ran and passed. The separate full **177-unique-test suite** remains `NOT_RUN`; 177 in Test 176 counts numeric occurrences, not tests. D6 remains `PASS_SCOPED_WITH_LIMITATIONS`. Historical reports remain unchanged; this correction is append-only.
