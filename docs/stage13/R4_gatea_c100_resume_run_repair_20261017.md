# R4 — CP Gate A C100 continuation repair, revised after failed attempts

- Date: 2026-10-17
- CP: CP-GATEA-C100-RESUME-RUN-REPAIR-20261017
- Branch: tmp/cp-gatea-c100-resume-20261017
- Base main: 647c19826b90d8224ce73ef9b90c306a45e03fb0
- Pre-change commit: 4cac8d024d0c0a0a72007f964258cf00388ce33a
- Run 1: 39002852709, tested SHA 693a74967cf69b5d428bb85afacaa4552fb510d6
- Run 2: 39003715853, tested SHA 4cac8d024d0c0a0a72007f964258cf00388ce33a
- Normative reference SHA-256: ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479
- Authorization: explicit user requests to repair Run 39002852709 and continue verifying/fixing this CP.

## R4 — Findings before these changes

| العنصر | الحالي | المرجع/القرار والفرع | النص الحاكم | الحكم |
|---|---|---|---|---|
| Extension key API (Run 39002852709) | The test imports expected_extension_keys(); the implementation only exposed expected_keys(). | Run 39002852709 log; tested SHA 693a749...; test blob 18ebac58ff9d0ec1ec325df4b7b91a501781f901. | D-2026-10-17-07 defines exactly the five C100 scenarios, trial IDs 2..600, totaling 2,995 extension rows. | K_CODE: missing compatibility API. Add an alias without changing the key range or set. |
| Prior prefix counts (Run 39003715853) | dict(Counter) omits scenarios with zero records, while the approved count inventory contains C100_G100: 0. The raw dictionaries therefore differ although the 2,048-row prefix is correct. | Run 39003715853 job 117311761478 log; original artifact 12087982889, archive SHA-256 d6b867529a8998f2230055c637209c67a4e0165b4f1ab68b62aa4cb8b223bfd6; prior script blob 52b98667efb6cda4c5d43732a48d834a8659fbf7. | Validate the exact key set and scenario count inventory; zero-count scenarios remain part of the approved inventory. | K_CODE: normalize observed counts across all five scenarios (missing count means zero) and separately compare the exact key set. |
| Failure evidence | Run 39003715853 failed before creating the result directory, so its artifact upload found no files. | Run 39003715853 artifact inventory was empty; stack trace ends at PRIOR_PROGRESS_COVERAGE_OR_SCENARIO_COUNTS_MISMATCH before opening the progress stream. | Failures must retain inspectable evidence, and no completed trial may be replayed. | WORKFLOW_DEFECT/K_CODE: write phase-aware execution status from PRECHECK and capture logs/exit code; always upload the diagnostic directory. |
| Retry safety guard | The original retry guard allowed only the first known pre-generation failure and rejected the second proven pre-generation failure. | Runs 39002852709 and 39003715853; prior workflow blob 3f098fcec7361754ec6605a973ae0208bc0dbb6b. | Never rerun completed trial IDs; fail closed if generation may have started. | WORKFLOW_DEFECT: reconcile the two known runs by exact SHA, step outcomes, log signature and empty artifact inventory. For newer attempts, require a diagnostic artifact that proves generation_started=false and no progress records before any further retry. |

## Bounded repair

1. Provide expected_extension_keys() as a compatibility alias to the existing exact key-set function.
2. Add validate_prior_coverage() that checks the exact prior key set and normalizes observed counts across the full five-scenario inventory. Add tests for the zero-count scenario and for missing-key rejection.
3. Write continuation_status.json from PRECHECK through prior-artifact verification, approved baseline verification, source-closure verification, generation start and final pending-audit state. On exception, preserve the last completed phase and write the exception type/message.
4. Always retain continuation.log, process_exit_code.txt, run_context.json and continuation_status.json in an artifact, including preflight failures. Keep the workflow pinned to this branch, contents/actions read-only, timeout 120 minutes, and no workflow_dispatch.
5. Permit retries only when the old failure is proven pre-generation. The two legacy failures must match their exact SHAs, failure signatures, step outcomes and have no artifacts. Subsequent failures must have a valid diagnostic artifact showing generation_started=false, a pre-generation phase, no final extension JSON and no nonempty progress stream. Otherwise stop without retry.
6. Before any new trial, continue to verify the immutable original artifact, all 14 pinned source files, SOURCE_SHA, source commit, MASTER_SEED=20270101, and the exact approved 25,205-row baseline map SHA 0fbe3aa87a253f9527953c77b0a122871c9344f75ece6c8a49da99b2a85c1ce1.
7. Generate only the 947 missing keys: C100_G070 IDs 253..600 and C100_G100 IDs 2..600. No statistical checkpoint or stability acceptance is authorized.

## Acceptance and prohibitions

- Focused deterministic tests must pass on the exact tested SHA.
- Inspect the resulting Artifact and payload: archive and member hashes/sizes, 2,995 extension rows, unique keys, per-record identities/hashes, separate provenance per Run, combined map count/hash and C100 coverage.
- If the retry guard cannot prove all prior executions stopped before generation, stop without running a trial.
- Do not change SOURCE_SHA, source commit, seed, RNG, sampling, historical Parquet, the normative reference, main, state.json, PR/merge state or Releases.
- A successful Run alone does not establish Gate A, statistical stability, delivery or production PASS. Keep the result labelled pending independent Artifact audit until the contents are inspected.
