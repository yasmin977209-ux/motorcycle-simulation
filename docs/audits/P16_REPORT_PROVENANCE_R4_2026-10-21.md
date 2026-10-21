# R4 — P16 report provenance branch binding — 2026-10-21
1. **Item/current state:** P16 reports hard-code `tmp/p16-provisional-outputs-20261021`; actual full Run `39635040311` ran on `tmp/p16-diagnostic-benchmark-20261021`.
2. **Authority/evidence:** P16 Run 39635040311 and its read-back; tested source code SHA `30ba2d5d47d3a3d6c117f0ef667115401c337ad7`; workflow trigger SHA `2a06fba75bb66bd355b1a3b7e7e8546bf4e03190`.
3. **Current candidate:** `tmp/p16-diagnostic-benchmark-20261021` HEAD `7a5b0b732b7876edfae82afb29c02d97a248491e`; `scripts/p16_produce_deliverables_v4.py` blob `c3f630b883ec1c02c2fca6ab93363b2c099da51d`.
4. **Governing requirement:** run branch, tested SHA, and report provenance must be kept distinct and truthful; do not transfer a branch label across Runs or SHAs.
5. **Defect class:** `K_CODE` — report provenance string is hard-coded, while build evidence already captures the actual branch from `GITHUB_REF_NAME`.
6. **Minimum change:** pass `evidence["branch"]` into `write_reports` and interpolate it in both full-report templates; no other report logic changes.
7. **Authority/scope:** owner directed that integration be followed by implementation while avoiding unnecessary repetition; this is a code-only correction on a temporary candidate branch. No main, tests, Workflow, source, seed/RNG, cohort, trial, Parquet, CS, `is_stable`, or C100 policy changes.
8. **Reproduction/acceptance:** source read-back must show the caller passes the actual run branch and both Arabic/English full reports render that value, never the stale literal. Preserve all other report content.
9. **Verification boundary:** do not rerun the full P16 workflow or rebuild the cohort; its only full Run is already consumed. Existing workflow pins the old script blob, so full-workflow verification is out of scope without separate approval.
10. **Status/risk:** fix can be verified at source/read-back level on this CP; unit/integration result remains `NOT_TESTED` unless a safe existing test path is independently available. This does not repair or reclassify the already-built Artifact; its delivery remains `CONFLICTED / NOT_ACCEPTED`.
