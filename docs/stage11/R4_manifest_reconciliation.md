## R4 Reconciliation — 2026-10-11 (CP-B1)

**main HEAD at R4 time:** 163270a66f863b34c504044cbcdf85a486f11893
**PR #16 head:** c7c885feab0e53d8267d3f54ca83b5dd069f602b
**Reviewer scope:** 13 items
**Result:** 12 MATCH, 1 EXPECTED_BASELINE_GAP, 0 DEVIATION, 0 VIOLATION
**Note:** The historical R4 below was performed against main@5185f51faef836a2884c904b8bb8feb775f5f6c2. This section records the current R4 against main@163270a66f863b34c504044cbcdf85a486f11893.

### R4 reconciliation table

| # | Item | main at R4 time | PR #16 candidate | Reference / approved decision | Judgment |
|---:|---|---|---|---|---|
| 1 | Manifest v1.1 structure | Canonical 11005 manifest absent; this is the planned CP-B1 baseline gap | Manifest v1.1 declares 11005 evidenced trials, 25 scenarios, SHA-256 aggregate, G1-G8, and reconciliation evidence | Reference §§14.3-14.4 and the approved G7 decision | EXPECTED_BASELINE_GAP; candidate structure accepted |
| 2 | dataset_identity.json vs 11005 expansion | Existing identity file records 25 scenarios and 11005 trials, with Stage 7 and Stage 10 provenance | Manifest points to dataset_identity.json and its verified blob SHA; no dataset identity file rewrite | Preserve identity provenance and do not replay trials | MATCH |
| 3 | Exact G7 decision | DECISIONS_LOG.md records the approved no-replay interpretation | Manifest uses Stage 7 checkpoint plus Stage 10 extension, identity checks, overlap/gap checks, and per-trial SHA evidence | “يعتمد تعريف G7 المعتمد الآن على هدف البوابة: **التحقق من عدم إعادة replay** في دمج Stage 7 وStage 10، مع فحص هوية التكرارات، وعدم التداخل، وعدم وجود فجوات، وبصمات التكرارات.” | MATCH |
| 4 | Possible CP-B2 path conflict | CP-B2 accounting data contract remains a separate open blocker | The PR changes only the two authorized docs/stage11 files; it does not change Stage 12 or workflow files | CP-B2 remains separate and must not be started by CP-B1 | MATCH |
| 5 | source_sha compatibility | state.json source_sha is f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b | Manifest source_sha matches | State and dataset identity source SHA | MATCH |
| 6 | 9005 data hash vs historical 11005 file blob | dataset_identity.json labels 892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6 as the Stage 9A 9005 data identity only | Manifest identifies the historical 11005 Git blob separately as 27e94a0ddb573b4d09701faac9978168f62ded89 | A data hash is not a Git blob SHA; preserve both independently | MATCH |
| 7 | Per-scenario trial IDs and gaps/overlaps | Five C100 scenarios use trial_id 1 only; twenty non-C100 scenarios use 1..550 | Scenario counts are 1 for each C100 case and 550 for each non-C100 case; Stage 7 contributes 1..450 and Stage 10 adds 451..550 | Validate ranges per scenario, not as a single global range | MATCH |
| 8 | Manifest source_sha equals state.source_sha | Both use f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b | Manifest evidence records source SHA compatibility as true | Existing canonical source identity | MATCH |
| 9 | MASTER_SEED | 20270101 | 20270101 | Reference §14.3 | MATCH |
| 10 | Stage 12 topology | Current state records CP-B2 topology as 25 materialization jobs plus validate and aggregate | The candidate makes no topology or workflow changes | Preserve topology work for CP-B2; no conflict introduced here | MATCH |
| 11 | REFERENCE_AMENDMENTS compatibility | Approved D-2026-10-10-01 through D-2026-10-10-04 exist | Manifest statistics scope is per-scenario; pooled cross-scenario statistics are descriptive only | Approved amendments, especially Amendment-01 statistics scope | MATCH |
| 12 | Historical R4 retained and current R4 added | Canonical Stage 11 manifest/R4 are absent from current main | Original R4 text is retained below this added section; historical comparison remains against main@5185f51 | Add current review without rewriting historical evidence | MATCH |
| 13 | Exact PR #16 files and blobs | The two files are not yet canonical on main | R4: 3623 bytes, blob 03e632257ee35b6307937707e478da9961cdb691. Manifest: 4636 bytes, blob b8947a60051a244784248875f5e0435b9996d95b | The authorized transfer is limited to these two files | MATCH |

### Evidence references checked

- Current main state blob: 646ccc51766c09e4b1b25442119fff65211887b4.
- dataset_identity.json blob: 72a481d509d39820fba78732724fde4fa9f25134.
- REFERENCE_AMENDMENTS.md blob: bf4a1a99af7f9065830163c86bb8c7d086143a11.
- DECISIONS_LOG.md blob: 24ab9630c262100dcef0abed6e7dfeda676b89f6.
- STATE_SHA_SEMANTICS.md blob: 134363f0f2834f8087760b3148910a1a3d3af38b.
- The historical 11005 source was fetched from tmp/stage11-manifest-11005-20261008 at commit f17e1a59a91df8d4a967ebc3cbbd035ca1230439; its actual blob SHA matches 27e94a0ddb573b4d09701faac9978168f62ded89.
- No trial replay or engine, test, RNG, workflow, decision-log, amendment, or original-reference change is included in this CP-B1 transfer.

---

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
