# R4 — P16 full-report branch provenance regression — 2026-10-21

## Scope

- Base/main HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- Candidate parent: provenance correction branch head `b44873404af394629654a2731ae41e52a919daed`.
- Candidate branch: `tmp/cp-p16-report-provenance-verified-20261021`.
- Existing producer file blob: `781615b297095a8fc625116575f1064941b29cb4`.
- Classification: `K_TEST + K_WORKFLOW / DETERMINISTIC UNIT TEST ONLY`.

## Prior correction being validated

The prior code-only R4 changed the P16 full-report template to receive a `branch: str` argument and substituted that runtime argument into both English and Arabic report identity sections. The caller passes `evidence["branch"]`. That correction had `PASS_SCOPED_STATIC_READBACK / NOT_TESTED_RUNTIME` because the P16 production workflow asserts a fixed older producer blob and full P16 rebuild was not authorized.

## This CP's minimal validation

Add a deterministic test that:
- imports the report producer but never invokes the production entrypoint;
- monkeypatches Parquet reads to return empty synthetic row lists;
- supplies synthetic metric summaries/assignments and an explicit candidate branch string;
- calls only `write_reports` into pytest temporary storage;
- verifies both full report files contain the exact supplied branch name and do not contain the old hardcoded value `tmp/p16-provisional-outputs-20261021`.

Add a candidate-specific workflow that installs repository requirements, compiles the producer and test module, runs only this test, and uploads the JUnit/log plus exact source/test Git blob SHAs. It does not run `p16_produce_deliverables_v4.py` as a script or load production artifacts.

## Exclusions

No full P16 build; no output workbook generation, source artifact read, data write, input/manifest rewrite, Trial/Checkpoint, simulation, Monte Carlo, source SHA, seed/RNG, trial/cohort ID, historical artifact, main, merge, or release. The test must never invoke the main function or artifact-download paths.

## Acceptance

Only accept the provenance fix after exact-SHA candidate CI passes with the synthetic report test. This does not accept P16's outputs, resolve missing MaxCase daily payloads, resolve Gate A or C050 provenance, or promote delivery.

## Status

`PENDING_TEST_AND_EXACT_SHA_CI`.
