# D2 Requirements Matrix — Number Registry
Date: 2026-11-01
Repository: yasmin977209-ux/motorcycle-simulation
Branch: tmp/d1-rebuild-20261101
Governing decision: D-2026-10-30-REFERENCE-V2.4.0 (APPROVED_BY_OWNER)

| ID | Requirement | Implementation / evidence | Disposition |
|---|---|---|---|
| D2-01 | Build deterministic registry from pinned Aggregate, Full Logging and C100 artifacts | scripts/s6_number_registry.py; pinned artifact verification in stage-d2-number-registry.yml | PASS_SCOPED |
| D2-02 | Verify artifact ZIP size, SHA-256, CRC and member integrity before parsing | verify_zip / verify_member; workflow pin checks | PASS_SCOPED |
| D2-03 | Preserve S6 and C100 identities and do not pool cohorts | Registry scope metadata; C100 marked CROSS_COHORT_DETERMINISTIC_REUSE | PASS_SCOPED |
| D2-04 | Stable unique number_id for explicit numeric entries | stable_id; duplicate-ID validation | PASS_SCOPED |
| D2-05 | Address every Daily Distribution point deterministically | D2D-{series_sha20}-{zero_based_date_offset_6_digits}; full 2,086,550-point resolution validation | PASS_SCOPED (completion workflow must conclude SUCCESS) |
| D2-06 | Preserve exact numerator/denominator, reduced fractions and deterministic display rounding | Fraction / Decimal / ROUND_HALF_EVEN; per-entry and per-point validation | PASS_SCOPED |
| D2-07 | Prohibit float in serialized registry | no_floats recursive validation | PASS_SCOPED |
| D2-08 | Preserve source provenance and locators | source artifact/run/member, hashes, path, source commit, cohort and gate/evidence fields | PASS_SCOPED_WITH_LIMITATIONS |
| D2-09 | Preserve unavailable evidence without inference or zero-fill | Five accounting fields and source_run_metadata.sha256 remain MISSING_EVIDENCE | PASS_SCOPED |
| D2-10 | Unit tests cover exact arithmetic, IDs, resolver modes, invalid IDs and provenance | tests/test_s6_number_registry.py plus builder tests | PASS_SCOPED (completion workflow must conclude SUCCESS) |
| D2-11 | Produce audit Markdown and canonical JSON while retaining the old local report | docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.md and .json; old report nested under historical_local_report | PASS_SCOPED |
| D2-12 | Exact final HEAD and GitHub Raw byte readback for every D2 deliverable | Stage D2 workflow final validation step; run log emits URL/path, bytes, SHA-256, blob SHA-1 and commit | PASS_SCOPED (completion workflow must conclude SUCCESS) |
| D2-13 | Append session, handoff and project continuity without rewriting history | docs/PROJECT_CONTINUITY.md and Stage D status/handoff | PASS_SCOPED (completion workflow must conclude SUCCESS) |
| D2-14 | Preserve all governance limits; no Trials, Simulation, Monte Carlo, N expansion, backfill or zero-fill | Workflow contains pinned-source build only; explicit audit limitations | PASS_SCOPED |

## Scope boundary
D2 is a Number Registry phase, not project final acceptance. Full Logging covers 105 representative keys only. C100 Golden revalidation remains NOT_RUN. Financial Gate A remains PASS_SCOPED; production Gate A remains NOT_DECLARED; Gate B at N=2400 remains FAIL_SCOPED (10/10); Stability remains NOT_CONVERGED (0/60); N=4800 remains NOT_EXECUTED. The five historical accounting fields remain MISSING_EVIDENCE. No new Trial, Simulation, Monte Carlo, N expansion, historical backfill or zero-fill is authorized by this phase.


## Completion workflow record

- Workflow Run: 41332273796
- Triggering source SHA: 2407a8e832aa8fa01ed8951ce8f89cc8548a8dea
- Registry-containing commit: 024c71a909328cec379f3628df25981310c64fe7
- First exact-head gate passed before this documentation finalization. The final post-finalization exact HEAD and all Raw byte triples are established by the last validation step and the SUCCESS conclusion of this same workflow Run.
