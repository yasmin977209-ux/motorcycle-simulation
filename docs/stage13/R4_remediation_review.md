# Stage 13.3 Remediation R4 — triple-source review and implementation boundaries

Scope: repair the Stage 13 workflow/evidence harness after Run 37997114441 was cancelled.
Protected: daily_engine.py, rng.py, main, state.json, the canonical reference, and canonical 11,005-trial data.
Source basis: current main, stage3b-preserved as diagnostic evidence only, and المرجع_النهائي_الموحد_المعتمد.md. No preserved-branch code is copied into the product.

| Item | main | stage3b-preserved | Canonical reference | Judgment |
|---|---|---|---|---|
| Chapter 4.4 path helper | Current engine provides daily_engine._new_contract; integration test called absent daily_engine._create_contract. | Historical engine has _create_contract. Diagnostic comparison only. | Section 4.4 requires specified lifecycle paths, not a private helper name. | WORKFLOW_DEFECT under R5. Adapt test call to the interface present on main; leave assertions and engine untouched. |
| M1–M17 trace assertion | Trace collection is opt-in via project._execution_trace_enabled; a dedicated test already enables it and separately proves default trace is empty. | Historical engine unconditionally appends execution trace. | M1–M17 order is mandatory; default trace collection is not mandated. | K_TEST. Enable trace inside the order test; preserve no-trace-by-default contract. |
| Asset roll-forward key | accounting.py emits Gross_Writeoffs_On_Ownership. | Older module has no current-format exported roll-forward key to use as authority for this schema. | Chapter 10 specifies Gross_Writeoffs_On_Ownership. | K_TEST. Correct the misspelled assertion key only. No accounting code change. |
| Acceptance input files | Tests 127 and 159–161 read results_stage5/* files that are not committed data products. | Legacy state and artifacts describe an older workflow contract and do not supply valid current fixtures. | Acceptance needs actual worker-equivalence and sample-data evidence; it does not mandate committed fixture files or require results_stage5 as an authoritative data product. | WORKFLOW_DEFECT. Generate deterministic run-local fixtures before pytest; validate the C100 golden and actual sequential/parallel equality. Keep fixtures out of the final sample dataset. |
| Excel input shape | scripts/excel_builder.py expects sequences in write_table, but its daily sheet passes dictionaries. | Preserved branch is not the authority for the current workbook builder. | Excel is presentation/audit output; Python and Parquet are accounting truth. | WORKFLOW_DEFECT. Apply a narrow in-process adapter at the build boundary, converting dict records to header order without altering the canonical builder on main. Independently re-read the exported workbook. |
| Long-running sampling | Original one-job run had no artifact and was cancelled with exit 143. | No historic artifact proves which IDs completed in that isolated run. | Resume identity must include source SHA, seed, RNG, sampling/stability policy, trial ID, schema and scenario; do not mix datasets or repeat known completed trials. | WORKFLOW_DEFECT. Use a separate diagnostic cohort with trial IDs 26–50 per scenario and per-trial atomic gzip checkpoints bound to exact implementation SHA and workflow run ID. Reject mismatched checkpoints; split by scenario. |
| Twenty-point gate | Stage 13 defines four metrics × five statistics × 25 scenarios. | No authoritative alternative definition found. | User subsequently authorized an explicit 20-point consistency definition; canonical statistical Gate A/B remains distinct. | Definition is 500 exact numeric Parquet-to-_STATS comparisons. This does not establish statistical Gate A/B acceptance. |

| Recovery post-processing checksums | No matching Stage 13 recovery workflow on `main`; canonical engine and state remain protected. | Preserved branch is diagnostic only and supplies no authority for this package schema. | The reference requires full dataset identity and output fingerprint integrity; package identity and manifests must not disagree. | **WORKFLOW_DEFECT** in recovery post-processing: after `sampling`/`stability` were added to each scenario's `dataset_identity.json`, nested `artifact_manifest.json` values also needed rebuilding. Recovery now regenerates and verifies all 25 nested manifests before rebuilding and verifying the outer manifest. |

## Guarded execution design

1. Run pinned-source integrity checks before simulation.
2. Generate test-only inputs in a separate acceptance step and gate pytest plus the 163-test inventory (162 PASS, zero FAIL, test 158 EXCLUDED).
3. Launch one job per scenario with no workflow-dispatch trigger, no wildcard branch pattern, and a job-level timeout.
4. Checkpoint after every completed trial using atomic replacement and SHA-256 checks over the summary and daily rows. Accept only full identity matches; reject corrupt, conflicting or foreign-cohort files.
5. Keep IDs 26–50 in a distinct cohort. Do not overwrite or combine the canonical 11,005-trial Parquet set and do not claim Monte Carlo Gate A/B PASS.
6. Verify 25 scenario packages, 625 summaries, 125 role assignments, representative replay equality, all daily balance checks, cohort fingerprint, 185 worksheets, zero Excel error cells and zero formula cells.
7. Independently recompute MIN/P10/P50/P90/MAX for Final_Net_Project_Equity, Partner1_Final_Entitlement, Partner2_Final_Entitlement and Final_Cash, then compare all 500 numeric values from the exported workbook exactly.
8. Keep the complete build on the temporary branch. Do not merge, mutate main, or update state.json in this CP.

## Verified execution evidence — 2026-10-10

The exact workflow head `d1531b1ffd1e841ae2ad19d6154ac9d81c617ea1` completed in GitHub Actions Run [38060796014](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/38060796014), conclusion `success`.

This was an assembly-only recovery, not a rerun of the diagnostic trials:
- The original producer run was `38005557997`, head `648b5315da1ef46146226d7982020a88c4905dcb`. Its acceptance job and all 25 scenario jobs succeeded; only its first assembly attempt failed because the shallow checkout lacked the pinned source commit.
- In Run `38060796014`, the `acceptance` and `sample` jobs were intentionally skipped. The assembly job fetched the scenario packages and acceptance evidence from Run `38005557997`, verified the producer implementation identity, built the workbook and executed the 500 comparisons.
- Recorded assembly output: cohort `STAGE13_SAMPLE_TRIAL_IDS_26_50_V2`; 25 scenarios; trial IDs 26–50; 625 trial results; 125 representative role assignments; 105 unique representative detail trials; 185 workbook sheets; zero Excel error cells; zero formula cells; `GATE_STATUS=PASS`; `POINTS_MATCHED=500` of 500.
- Trial-results fingerprint: `ba6f1e0dcf6daad1a4e5dcf07c01ff26b8dbac79320b4dcc2a3d3514e276c772`.
- Workbook SHA-256: `dae115c9bb41be9a9d4558429d874df649e80439f2299aff8a8e4f3a9038b201`.
- Post-processing logs: `SCENARIO_ARTIFACT_MANIFESTS_REBUILT_AND_VERIFIED=25` and `FINAL_ARTIFACT_MANIFEST_INTEGRITY=PASS; FILES=316`.
- Uploaded evidence artifact: `stage13-sample-final-evidence`, artifact ID `11673197601`, archive digest `sha256:4ead98bec5f29e608447360bd3f1755c49aa9f2727a4834ac358e4376d63c774`.

The result proves only the explicit 500-point Parquet-to-XLSX consistency gate for this separate 625-trial diagnostic cohort. It does **not** establish statistical Gate A/B or replace/change the canonical 11,005-trial dataset (fingerprint `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`). Main and `state.json` remain unchanged; PR #20 remains draft and unmerged. The current `main/state.json` still names Stage `12-CLOSED` and next `CP-B1`; this diagnostic recovery does not authorize crossing that CP boundary.

## CP outcome

| Gate | Result | Evidence |
|---|---|---|
| Acceptance evidence used for this cohort | PASS (reused from the original producer run) | Run `38005557997`; acceptance artifact; 163-test inventory report |
| Source/producers match pinned sample revision | PASS | Run `38060796014`, step `Verify source code matches the pinned completed sample cohort` |
| Scenario coverage and trial identities | PASS | 25 packages; 625 results; IDs 26–50 per scenario; assembler runtime checks |
| Workbook structure/integrity | PASS | 185 sheets; 0 Excel error cells; 0 formula cells |
| 500 exact Parquet-to-XLSX comparisons | PASS | Runtime output `POINTS_MATCHED=500`, `POINTS_EXPECTED=500` |
| 25 nested artifact manifests | PASS | `SCENARIO_ARTIFACT_MANIFESTS_REBUILT_AND_VERIFIED=25` |
| Outer artifact manifest | PASS | `FINAL_ARTIFACT_MANIFEST_INTEGRITY=PASS; FILES=316` |
| Statistical Gate A/B | NOT EXECUTED by this cohort | Explicitly out of scope; no PASS inferred |
| Merge/state update/next CP | NOT AUTHORIZED here | Main unchanged; PR #20 remains draft |

