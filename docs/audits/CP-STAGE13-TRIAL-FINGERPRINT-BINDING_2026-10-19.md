# CP-STAGE13-TRIAL-FINGERPRINT-BINDING — 2026-10-19

## Disposition

**Candidate integrity fix recorded; runtime test gate remains PENDING/BLOCKED; project delivery remains PARTIAL.** This CP found and corrected a candidate-only identity gap in adaptive Stage 13. No production dataset, reference, source, seed/RNG, trial, workflow, main or Release was changed.

## R4 / authority

The pre-change R4 was written on the candidate first: `docs/stage13/R4_trial_fingerprint_binding_20261019.md`, current candidate report blob `02e813d1bd4fdf20fa99a7b5f98a7139b4a27e7f`.

The R4 compares the candidate validator with source-backed digest definitions:
- `scripts/stage7_run_trial_block.py` on main, blob `33527f198bafadcb7ac8d06b2a72e142deb268ac`, hashes canonical JSON of `asdict(TrialResult)`.
- `scripts/stage12_gateb_n600_audit.py` on main, blob `dd9b4c738e065f4f62139efe131df75c37f41dac`, defines the same sorted-key compact UTF-8 JSON hash form.

## Finding and change

Before the change, `scripts/stage13_assemble.py` only verified that each supplied `result_sha256` looked like a valid SHA-256 and then calculated the ordered aggregate map from those strings. It did not recompute each digest from the row's TrialResult values. The candidate's synthetic fixture itself used a digest of scenario and trial ID, independent of result values. That could leave changed financial outputs detached from their row fingerprints if a matching aggregate map were supplied. This was a **K_CODE finding on the candidate**, not evidence of production data tampering.

Implemented candidate changes:
- New assembler blob: `1548d4393cd79922abfd570f1c9a90454d7e40fe`.
- It requires exactly the 18 source-defined `TrialResult` fields plus a separate `result_sha256`, recomputes the digest using the established canonical JSON encoding, and fails closed on schema drift or digest mismatch before the aggregate map is built.
- New tests blob: `68c64ea6a63c12b0cbc8602db44cdfa15d23c094`.
- Synthetic adaptive fixtures now hash an instantiated `monte_carlo.TrialResult` with the same serialization contract. Added regression tests reject (a) a changed outcome value with an unchanged digest and (b) missing TrialResult fields.

## Exact identity and verification boundary

- Candidate branch: `tmp/cp-stage13-adaptive-assembler-20261017`.
- Candidate HEAD: `8f690adbbd7ec533a50028dab8c5d78ba0c370bb`; main base remains `647c19826b90d8224ce73ef9b90c306a45e03fb0`; compare is 67 commits ahead / 0 behind, with 21 changed paths in this broad candidate branch. Do not merge the branch as a unit; it contains prior unrelated candidate work.
- Current candidate file blobs were independently re-read from GitHub and contain the new schema guard, digest recomputation, and both test definitions.
- **No runtime test was run on the amended HEAD.** The earlier synthetic run `38995349182` was for tested SHA `3fdcdf8d006eff8f4a8fabb9ea2feb5c70c81633` and cannot cover these changes. Its temporary test workflow has been removed. This CP made no workflow edits; the exact-head test gate remains `PENDING/BLOCKED` until a permitted branch-pinned runtime path is explicitly authorized and run.

## Unchanged protected state

- main HEAD: `647c19826b90d8224ce73ef9b90c306a45e03fb0`.
- main `state.json` blob: `2178260bb18efeb81437486f13b6d10cf5e85936`; stage `12-CLOSED`; `repository_status=FINAL_DELIVERY_BLOCKERS_OPEN`; `source_sha=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`.
- `scripts/stage13_assemble.py` is still absent from main (404). No model/source/seed/RNG/sampling/trial identity, historical dataset, reference, main state, workflow, PR state or Release was altered. PR #46 remains open / Draft / unmerged.

## Next permitted action

Continue read-only audit of the Stage 13 clean-main compatibility candidate and final-delivery blockers. Keep the amended adaptive candidate unaccepted until focused tests and any resulting XLSX validation are executed on exact tested SHAs through an explicitly authorized path. No final-delivery or merge claim is made.
