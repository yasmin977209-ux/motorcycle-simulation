undefined

## Execution/read-back result

- Code commit 1: `da9e11a8d8da6b987846563439d41a2962fdc8a0`; `scripts/stage7_stability.py` blob after edit: `13872f6aa9405bc72532d32756979dc2c7e8695d`.
- Code commit 2 / branch head at read-back: `f1f824f56c6160f3283737b9cb25a4618d49e005`; `run_batch.py` blob after edit: `3acc9bdc27694b2fef3925e05f4eaba5a110ddef`.
- Candidate comparison against base `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`: 3 commits ahead, 0 behind; exactly the R4 document and the two code files changed. No test/workflow/state/source/data file changed.
- An uncommitted standalone logic probe passed valid doubling points, intermediate integer classification, malformed/missing N rejection, strict Gate B Boolean rejection, and prior order/duplicate fail-closed checks. Output: `PASS_SCOPED_LOCAL_LOGIC_PROBE`.
- The probe is not an import/integration test of the full repository, not pytest, not GitHub CI, and not runtime/production evidence. No Workflow or Monte Carlo ran.
- Live `main` was re-read at `6a218ebe0fccf210ec18f3552b141afbdd1a49ef` and remains unchanged.
- Disposition: `PASS_SCOPED_LOCAL / NOT_CI_VALIDATED`; this CP improves invalid-input handling only. Gate A, near-zero CI interpretation, complete statistical policy, production acceptance, and release remain open.
