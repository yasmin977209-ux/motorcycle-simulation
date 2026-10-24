# Stage 13 diagnostic workbook assembly — evidence reconciliation — 2026-10-24

## Status

This PR is a bounded **diagnostic-only** adapter run. The canonical Stage 9A manifest remains immutable at Git blob `c8591aac3d309fd94c4e67a547d33fb62ac5694d` and describes **9,005 trials** (450 per non-C100 scenario). It is retained only as the original identity pin for the official MaxCase audit/replay inputs. It is **not** used as the trial-result data source for this diagnostic cohort.

The diagnostic dataset is derived read-only from exact pinned source artifacts:
- Stage 7 run `37225915321`, HEAD `e0b2fab6710833774937d778097363d7a8ee8e59`.
- Stage 10 run `37709936740`, HEAD `ca73f2df37baacebbcad965fc5f433f129675820`.
- Stage 12 run `37964656154`, HEAD `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`.
- Stage 11 cohort manifest Git blob `b8947a60051a244784248875f5e0435b9996d95b`, dataset identity blob `72a481d509d39820fba78732724fde4fa9f25134`, aggregate SHA-256 `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`.

The builder validates exact source artifact IDs, run IDs/HEADs, artifact ZIP digests, per-trial TrialResult row hashes and all 22,546,465 Stage 12 daily rows against the corresponding TrialResult fingerprints before emitting the temporary 11,005-trial dataset. It does not run the simulation engine, run Monte Carlo/Trials/checkpoints, alter historical source artifacts, modify the Stage 9A manifest, or update the canonical Stage 11 dataset identity.

## MaxCase audit and recovery

- Source audit artifact: Run `40038112945`, artifact `12537818827`, current audit JSON/payloads are digest-pinned by the workflow.
- Exact selected-Trial replay artifact: Run `40050459020`, artifact `12542814312`, JSON digest `c477e390a5b0b9c8c35a3d5474e5b359056e59d1f2254395e589af4621982006`.
- Audit integrity: `PASS_SCOPED`; representative-inventory mismatch count 0.
- Existing exact-source MaxCase payloads: 15 reusable; 10 missing partner memo sources are covered by the separate exact replay bundle. CI validates replay TrialResult fingerprints and Stage 12 common fields before build.

## Diagnostic workbook behavior

The build input manifest is labeled `DERIVED_DIAGNOSTIC_ONLY_NOT_FINAL` and has 11,005 trials / 25 scenarios. The README reports the three source runs and source HEAD SHAs, not the historical Stage 9A run as if it produced the current cohort. The P50 time-series page is built from the verified Stage 12 ledger. Detailed assets, transaction/accounting roll-forward, partner-memo, guarantee, and contract pages require payload fields absent from the Stage 12 ledger; diagnostic mode explicitly marks these sections `SOURCE_NOT_AVAILABLE_IN_DIAGNOSTIC_COHORT` rather than inventing values or equating missing data with zero. These pages do not qualify as source-complete final workbook tabs.

The output name remains `Stage13_Diagnostic_Candidate_NOT_FINAL.xlsx`. Artifact upload includes the derived manifest and cohort provenance report alongside the MaxCase audit/replay bundle and build report. Any successful artifact build remains `NOT_FINAL_BLOCKED`; it is not the required seven-file Arabic/English final delivery, not P17/P18 release acceptance, and not a statistical gate pass.

## Acceptance boundary

The global statistical gate remains `BLOCKED_FOR_IMPLEMENTATION`; production execution permissions remain false. Open blockers include time-uniform financial-mean inference/K_SPEC, unintegrated quantile and Bernoulli components, incomplete Golden coverage, P90_Held_Assets acceptance, the historical C030_G030 N=300→600 P90_Final_Cash failure, Stage 10 metadata/fidelity drift, and G2 runtime evidence. No diagnostic artifact can waive these decisions.
