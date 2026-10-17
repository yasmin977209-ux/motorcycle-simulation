# R4 — CP Gate A C100 continuation run failure repair

- Date: 2026-10-17
- CP: \`CP-GATEA-C100-RESUME-RUN-REPAIR-20261017\`
- Branch: \`tmp/cp-gatea-c100-resume-20261017\`
- Base \`main\`: \`647c19826b90d8224ce73ef9b90c306a45e03fb0\`
- Pre-change branch head: \`693a74967cf69b5d428bb85afacaa4552fb510d6\`
- Failed Run: \`39002852709\`
- Failed Run tested SHA: \`693a74967cf69b5d428bb85afacaa4552fb510d6\`
- Normative reference SHA-256: \`ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479\`
- Requester authorization: explicit user instruction, “قم بإصلاح run 39002852709”.

## Pre-change R4

| العنصر | الحالي | المرجع/القرار والفرع | النص الحاكم | الحكم |
|---|---|---|---|---|
| Expected extension key API | \`scripts/resume_c100_golden_extension.py\` defines \`expected_keys()\`, but not \`expected_extension_keys()\`; the focused test imports the latter. | Failed Run 39002852709, tested SHA \`693a749...\`; current resume script blob \`5b053b2dce95944374dd64f9630f584cdaef042e\`; current test blob \`18ebac58ff9d0ec1ec325df4b7b91a501781f901\`. | D-2026-10-17-07 requires exactly the five C100 scenarios and trial IDs 2..600, yielding 2,995 unique records. Existing \`expected_keys()\` already constructs that exact set. | \`K_CODE\`: intended key-set implementation exists under another API name; import contract is missing. Repair with a backwards-compatible alias; do not alter the test's normative assertion. |
| Failed run execution boundary | Focused pytest collection failed with \`ImportError: cannot import name 'expected_extension_keys'\`; source closure and generation steps were skipped. The run produced no Artifact. | Run 39002852709 job 117309224660 logs and artifact inventory. | Generate only the exact 947 missing IDs after prior artifact, source closure and approved baseline verification. | No trial generation was started by this failed Run; preserve it as immutable failure evidence. |
| One-time workflow guard | Existing guard rejects every previous run of the workflow, including a run that failed during test collection before the generation step and uploaded no Artifact. | Current workflow blob \`f55cfc0bf7e3c71963e30694238a65276bfbb66d\`; Run 39002852709. | Never rerun completed trial IDs; nevertheless, repair a pre-generation code failure only after proving no generation step ran and no output Artifact exists. | \`WORKFLOW_DEFECT\`: too broad to permit one safe recovery. Allow exactly this known pre-generation failed Run only, verified by job-step conclusions and an empty Artifact list; reject every other prior-run shape. |

## Approved bounded fix

1. Add \`expected_extension_keys()\` as a compatibility API that returns \`expected_keys()\`; keep key coverage, ranges, trial identities, hashes, seed, RNG, schema and source SHA unchanged.
2. Narrow the workflow's one-time guard to allow one repair execution only when the sole prior run is Run \`39002852709\`, with the exact prior tested SHA, completed/failure conclusion, focused-test failure, source-closure and generation steps skipped, and no artifacts. The workflow must fail closed if any of those conditions differ or if any other prior attempt exists.
3. Leave \`tests/test_c100_golden_extension_resume.py\` and the original partial Artifact unchanged; the existing regression test itself will verify the API contract.
4. The new execution still validates the immutable original Run/Artifact, the pinned 14-file model source closure, source identity and seed, and exact 25,205-row baseline map SHA \`0fbe3aa87a253f9527953c77b0a122871c9344f75ece6c8a49da99b2a85c1ce1\` before generating any IDs.
5. Generation is permitted only for \`C100_G070\` IDs \`253..600\` and \`C100_G100\` IDs \`2..600\`, exactly 947 keys. It does not authorize a checkpoint or statistical stability claim.

## Acceptance / prohibitions

- Test the focused deterministic suite on the new exact branch SHA.
- Inspect the resulting Artifact and payload; reconcile record keys, record hashes, per-run provenance, combined map count/hash, artifact bytes and archive SHA independently.
- If the guard does not prove the previous run stopped before generation, or if a different run is present, stop without generation and report the blocker.
- Do not re-run completed IDs; do not change \`SOURCE_SHA\`, master seed, RNG, sampling, historical Parquet, reference, \`main\`, \`state.json\`, merges, PR state or Releases.
- Remove the temporary workflow file on this branch only after its output Artifact has been inspected; retain the branch and evidence.
- No \`PASS\` for Gate A, stability, delivery or production is implied by this recovery.
