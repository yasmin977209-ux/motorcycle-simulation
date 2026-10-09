# CP-B1 R4 — Stage 11 manifest reconciliation

Date: 2026-10-10. Scope: documentation/manifest only; no engine, test, RNG, reference, or workflow changes.

## Three-way comparison completed before the proposed change

| Item | main (HEAD 5185f51faef836a2884c904b8bb8feb775f5f6c2) | stage3b-preserved (HEAD 2e3aa381d833fe430d2aec42e98dd0d29918c3bf) | Binding reference | Judgment |
|---|---|---|---|---|
| 11005-trial global manifest | The reconciled manifest is absent; state.json and DECISIONS_LOG.md record this as pending. | Manifest absent; branch state is Stage 9-era diagnostic history with a different source-package SHA. | §§14.3–14.4 require stable MASTER_SEED, SHA-256 RNG and logical trial_id; they do not prescribe this manifest path. | DEVIATION: canonical reconciled manifest missing from main. Add a new file; never rewrite historic evidence. |
| Dataset identity | dataset_identity.json records Stage 7 IDs 1..450, Stage 10 additions 451..550, 25 scenarios and 11005 trials; main state source_sha is f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b. | Diagnostic state records Stage 9 and different source-package SHA c7429d1a31037e98201a05ed98b62c9c68118b2fda89064804d2d2cea2dfed79. | §§14.3–14.4 require reproducible identity, fixed master seed, stable trial ID and order-independent results. | MATCH for main identity constraints; stage3b remains historical and is not used as data source. |
| G7 semantics | DECISIONS_LOG.md records the user-approved no-replay interpretation and the historical K_SPEC classification on 2026-10-09. | No Stage 11 / revised G7 authority. | Reference requires stable trial identity but does not define the project-specific G7 checkpoint equation. | MATCH: follow the explicit recorded decision; do not require next_trial_id - 1 == merged trial_id_max. Historical K_SPEC is excluded from CB-9 by the user's latest clarification. |
| Historic evidence | Source manifest is not on main; provenance is recorded in DECISIONS_LOG.md. | No same-path Stage 11 manifest. | §0.1 prohibits inventing rules; project governance says historical evidence must remain unchanged. | MATCH if a new reconciled file is added and the original branch/file remain untouched. |

## R4 classification

- DEVIATION: reconciled 11005-trial manifest is missing from main.
- MATCH: main's Stage 11 identity and revised G7 decision align with the reference identity constraints.
- VIOLATION: none found in CP-B1 scope.
- Historic source: tmp/stage11-manifest-11005-20261008, commit f17e1a59a91df8d4a967ebc3cbbd035ca1230439, file docs/stage11/global_manifest_11005.json, blob SHA 27e94a0ddb573b4d09701faac9978168f62ded89. Its legacy FAIL and 20-item obsolete failure list are preserved as historic evidence; no source file is rewritten.
- No trials were rerun. Global aggregate SHA remains 7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44.

## Reconciliation gates

| Gate | Result | Evidence |
|---|---|---|
| G1–G6 | PASS | Existing identity evidence covers 11005/11005 trials, 25 scenarios, per-trial evidence, source SHA and master seed. |
| G7 (revised) | PASS | Stored CP-11-B-Rev1 verification: Stage 7 checkpoint matches 25/25; Stage 10 additions 20/20; no overlap 25/25; no gaps 25/25; per-trial SHA evidence VERIFIED. |
| G8 | PASS after commit | Only new documentation/manifest files; branch diff inspected; historic source and stage3b-preserved untouched. |
| Cross-check | PASS | 25/25 fingerprints match dataset_identity.json; source SHA f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b; MASTER_SEED 20270101; total N 11005. |

No state.json update is included in this batch.
