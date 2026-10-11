# R4 — Gate A full-scope historical golden fingerprint bridge

Date: 2026-10-11
Scope: read-only comparison of the canonical Stage 12 daily ledger's per-trial `result_sha256` against the recorded Stage 7/Stage 10 golden fingerprints for all 11,005 canonical trials.

## Three-source review before adding an audit script or workflow

| Item | Current main | `stage3b-preserved` | Binding reference / decisions / source evidence | Judgment |
|---|---|---|---|---|
| Gate A acceptance rule | `docs/governance/DECISIONS_LOG.md` blob `5896e166be27170454d4103bd83638bad05b5b62` contains normative D-2026-10-10-01: Gate A matches the approved reference/golden. | Diagnostic only; no Gate A evidence or code will be copied from it. | D-2026-10-10-01 / Amendment-01; historical output golden sources are Stage 7 Run `37225915321` (head `e0b2fab6710833774937d778097363d7a8ee8e59`) and Stage 10 Run `37709936740`. Both identify engine source `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`. | **MATCH** with direct equality of recorded per-trial output hashes. No tolerance, derived metric threshold, or altered acceptance rule is introduced. |
| Canonical source identity | `docs/stage11/dataset_identity.json` blob `72a481d509d39820fba78732724fde4fa9f25134` identifies 25 scenarios and 11,005 canonical trials; Stage 7 and Stage 10 identities are recorded there. | No implementation/artifact copied. | `docs/stage12/roll_forward_validation.json` blob `6084e8f68fa649fcf0726daa04f41ae9b0636706` ties the Stage 12 data to Run `37964656154`, source SHA, seed/schema identity and expected global aggregate `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`. CP12-D closure report blob `81bc3cd9c7666487b69b644dcc3291d0547c8e8b` says all trials finalized. | **MATCH** provided each artifact and each row is checked against its recorded identity before comparison. |
| Historical per-trial golden fingerprints | Main holds Stage 11 identity, the Stage 9A 9,005-trial manifest (blob `e796fa2443493b607f1f9c60b58eb63607959c26`) and Stage 12 validation/closure reports, but not a dedicated full 11,005-trial Gate A bridge report. | No reference/golden files or code copied from diagnostic branch. | Official Stage 7 block artifacts provide per-trial SHA-256 for IDs 1..450; the Stage 10 consolidated artifacts repeat those exact ranges and add IDs 451..550. Stage 7 C100 block artifacts provide the one canonical trial (ID 1) for each C100 scenario. Stage 12 daily Parquet stores `result_sha256` repeated per daily row. | **DEVIATION: evidence gap**, not yet a proven data mismatch. Proposed audit compares all fingerprints and verifies within-trial consistency, completeness and uniqueness. |
| Relationship to D-2026-10-11-01 | `state.json` records D-2026-10-11-01 in governance decisions; it does not turn state into a source of rules. | Not applicable. | The decision allows historical IDs 1..300 only as **Gate B** analytical inputs. This Gate A task compares recorded hashes to goldens as a read-only reference identity check; it performs no Gate B CI computation, no dataset resume/consolidation and no trial execution. IDs 301..550 are not admitted as Gate B inputs by this audit. | **MATCH**: separate gate scope and provenance. |
| Execution design | Existing main workflow files were inspected; no existing workflow currently produces this all-trial Gate A comparison. | No workflow copied from the preserved branch. | Use a new push-only workflow pinned to `tmp/gatea-golden-fingerprint-bridge-20261011`; use only `contents: read` and `actions: read`; exact artifact/run IDs and source SHA are asserted; `timeout-minutes` belongs inside each job; no `workflow_dispatch`, no self-dispatch. Matrix concurrency is limited to five scenarios at once. | **DEVIATION** resolved by a separately audited read-only workflow. |

## Exact comparison contract for this audit

1. For each non-C100 scenario, construct the expected fingerprint map for IDs 1..550 from the official Stage 7 block metadata for IDs 1..450 and Stage 10's block metadata for IDs 451..550. Validate range endpoints, per-trial SHA count, scenario, source SHA, and originating run for every block before using any hash.
2. For each C100 scenario, use only the official Stage 7 block's canonical `trial_id=1` fingerprint. Other C100 verification trials from Stage 10 are not canonical dataset trials and are not mixed into the map.
3. Stream the Stage 12 daily Parquet file for the same scenario. Validate the schema and embedded dataset identity, source SHA, master seed, unique/contiguous trial IDs, daily date continuity, and constant `result_sha256` within each trial. The Stage 12 hash for each trial must equal the source golden hash exactly.
4. The intended coverage is 25/25 scenarios and 11,005/11,005 canonical trial fingerprints. The report keeps Stage 7, Stage 10 and Stage 12 artifact IDs and ZIP SHA-256 values per scenario. The aggregate result is PASS only if every identity, coverage, uniqueness, and exact-hash gate passes.
5. This audit does not execute the engine, compute Gate B statistics, alter any historic artifact/metadata, or claim that Gate B/Stage 9C/CP-B2 is complete.

## Scope decision

The normative Gate A text says “matches the approved reference/golden.” Comparing every canonical per-trial output fingerprint is a direct exact-identity comparison to the source golden, adding no numerical threshold or business acceptance criterion. The audit will report its computed evidence without presuming success.

## R4 addendum — Stage 10 metadata encoding defect found in exact source

The sample Stage 10 non-C100 artifact `stage10-bench-C070_G100-1` (artifact ID `11520898788`, run `37709936740`, ZIP SHA-256 `e8278c5d0df4d208859ec14265a6cd665fea2e17e5a8a15ba908e65dbf36272d`) contains a `block_451_550_metadata.json` whose closing bytes are the literal characters `\\n` after the JSON object. Its raw SHA-256 is `cc53708648b99aa67d26365d790f0a6ddf9040bb505baaa02a633d35bcf83cc8`. This was reproduced from the archived artifact without modifying it.

The exact source at Run 37709936740 head `ca73f2df37baacebbcad965fc5f433f129675820`, `scripts/stage10_benchmark.py` blob `d54602982b6422939955ca841a251ecd250b4139`, line 72, contains `write_json(... + "\\\\n", ...)`; this emits a literal backslash+n suffix instead of a JSON file terminator newline. Classification: **K_CODE — Stage 10 metadata serialization defect**. The previous Stage 7 blocks inside the Stage 10 ZIP are valid JSON and match Stage 7 metadata exactly.

Audit disposition:
- Preserve and record the original Stage 10 metadata bytes and SHA; do not rewrite the historic artifact or its metadata.
- The audit parser may remove exactly the verified two-byte suffix `\\n` **in memory only**, and only if the original bytes end in `}` followed by `n` and the remainder parses as one JSON object with no other trailing bytes. It must record the raw hash, this parse disposition, exact workflow source/blob and artifact provenance in the Gate A report. No general permissive JSON recovery is allowed.
- Validate all per-trial hash arrays and range/run/source identity after parsing. If a file deviates from this exact defect pattern or any block identity/fingerprint mismatch exists, that scenario fails and Gate A remains unestablished.
- This known formatting defect does not alter the stored hash strings; whether the full Gate A comparison can be accepted remains determined solely by all exact row-level golden comparisons and identity gates, and the defect remains disclosed in the report.

## R4 addendum — independently re-hash source parquet rows before Gate A comparison

The Gate A runner will not treat `per_trial_sha256` metadata as the only source of golden values. Before comparing Stage 12:
- Recompute the canonical result SHA-256 for every row in each source Stage 7/Stage 10 block Parquet using the confirmed Stage10 source function at `scripts/stage10_benchmark.py` blob `d54602982b6422939955ca841a251ecd250b4139`, `canonical_json(dataclasses.asdict(x))` with `ensure_ascii=False`, `sort_keys=True`, separators `(",", ":")`, and `default=str`.
- Require the recomputed values and trial IDs to exactly equal the relevant block metadata `per_trial_sha256` map.
- Require Stage 7's recorded block `fingerprint_sha256` to match the official Stage 9A `docs/stage9a/dataset_manifest.json` blob `e796fa2443493b607f1f9c60b58eb63607959c26` at global fingerprint `892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6`, for the four blocks covering 1..450 (or the one canonical row for C100).
- For non-C100, compare the Stage 7 and Stage 10 archive bytes for all copied block Parquets and copied metadata files for IDs 1..450; both parsed metadata values and raw file SHA-256 must be identical. Independently verify the new 451..550 Parquet block against the Stage10 metadata after the exact one-suffix in-memory parser disposition recorded above.
- Finally compare every recomputed source result SHA to the Stage 12 `result_sha256`, after Stage12 row coverage, date continuity, schema, seed, source SHA and dataset-identity checks pass.

This bounds acceptance to exact hashes from the actual source row data; metadata parsing cannot manufacture an expected trial hash. The source artifacts remain byte-identical, and Gate A is PASS only at 11,005/11,005 source-row, metadata and Stage12 hash matches.
## R4 addendum — execution evidence discrepancies found in the first Gate A run (2026-10-11)

Base rechecked before correction: main `94b6ea49715c9f845be83b6f106b26c253bf0506`; `stage3b-preserved` `2e3aa381d833fe430d2aec42e98dd0d29918c3bf`. The approved Gate A criterion is exact comparison to the accepted source golden; the Stage 12 file SHAs must separately match CP12-B/CP12-C. No historical artifact or identity document may be rewritten by this audit.

| Finding | Evidence | Classification / disposition |
|---|---|---|
| C100 Stage 7 filename | Official C100 artifact `stage7-blocks-C100_G100-1` contains `block_1_1.parquet` and `block_1_1_metadata.json` (artifact `11312276587`, run `37225915321`). The previous audit implementation requested `block_1_300.*`, which does not exist in the artifact. | `K_CODE` — audit harness path defect. Correct the reader to the exact archived filenames; do not change the artifact or manifest. |
| Stage 10 head in Stage 11 identity summary | Main blob `docs/stage11/dataset_identity.json` `72a481d509d39820fba78732724fde4fa9f25134` stores `sources.stage10.branch_head_sha=ca73f2df37baacebbcad965f5c433f129675820` (39 chars). Live GitHub Actions Run `37709936740` reports actual head `ca73f2df37baacebbcad965fc5f433f129675820` (40 chars). Its aggregate workflow conclusion is `failure`, but individual canonical scenario jobs are checked separately and must each be `success`; the Stage 10 source code `verify_source()` enforces engine-file identity to `source_sha=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`. | `K_CODE` — malformed provenance summary field. Preserve the historical identity document untouched. The audit must record both values, use the live Run API head as execution provenance, and independently validate the exact per-scenario job, source SHA, metadata, row hashes and combined fingerprint. Do not hide the mismatch. |
| Gate A aggregate hash encoding | The binding CP12 aggregator blob `fd16864e92d2f4de97e1a9972e3992c38ab4e102`, lines 155–163, hashes the ordered bytes `scenario_id|trial_id|trial_hash` plus LF. Gate A `hash_entries()` uses the same ordering and byte encoding for unique `(scenario, trial_id)` pairs. | The earlier assessment that these were different byte domains was incorrect; the completed run’s source-map SHA equals the expected CP12 global value. | **MATCH:** require actual and source-golden trial-map hashes to equal one another and the expected global SHA; independently check each Parquet file against CP12-B/CP12-C per-scenario reports. |

These three corrections are audit implementation repairs, not a change to Gate A policy. The report must explicitly disclose the Stage 11 head-summary defect, separately retain the Stage 10 metadata literal-backslash-n defect and raw hashes, and claim Gate A PASS only if all 25 scenarios, all 11,005 exact trial hashes, Stage 12 file-identity checks, unique keys, source provenance, and parser/Actions gates pass. Stage 9C and Gate B remain independent gates.

## R4 addendum — Stage 12 evidence dictionary key mismatch (2026-10-11)

Run `38168648208` on candidate SHA `400880fbb26c31cb9000040ff0d2e93d93409696` passed the four strict parser tests and read the canonical source and Stage 12 artifacts, but each scenario stopped at the harness's field lookup with exact error `'unique_trial_keys'`. In `scripts/stage13_gatea_fingerprint_bridge.py`, `validate_stage12()` returns `exact_comparison_count`; the caller incorrectly referenced `unique_trial_keys`. This is an audit-harness **K_CODE** error, not a data mismatch. The gate now compares `exact_comparison_count == expected trial count`; key uniqueness is separately protected by ordered contiguous one-per-trial coverage and duplicate/gap rejection during the stream. No source, historical identity metadata, Parquet, trial or engine code changed.

| Item | Current main | stage3b-preserved | Binding source / current candidate | Judgment |
|---|---|---|---|---|
| Stage 12 comparison evidence field | Main owns the existing CP12 reports; no Gate A bridge script is on main. | Diagnostic only, no code reused. | Candidate helper returns `exact_comparison_count` from the number of closed unique trial IDs; previous consumer asked for nonexistent `unique_trial_keys`. | **K_CODE** in the helper, fixed to consume the returned contract field; preserve strict contiguity and duplicate rejection. |

The corrected branch reruns the same pinned, read-only Gate A audit against unchanged artifacts. The earlier failing run remains a recorded failed run and is not overwritten.

## R4 corrective addendum — global fingerprint encoding verified from binding source (2026-10-11)

Direct inspection of the actual CP12 aggregation code proves that its global-hash byte stream is identical to Gate A's ordered map stream. The earlier sentence alleging different hash domains was a mistaken assessment and is superseded by the corrected table row above. No production data or metadata changed; the successful Gate A report independently computed the source-golden ordered-map SHA-256 as `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`, equal to the expected CP12 global value.

The aggregate report now adds separate gates requiring (1) the actual Stage 12 map SHA equals the official CP12 global SHA, and (2) the source-golden map SHA equals the same official value, in addition to equality between the two maps and per-Parquet SHA checks. Run `38168776800` completed before these explicit gates were added; a fresh run is required before claiming PASS under the strengthened inventory.


---

## R4 final acceptance addendum — Gate A exact golden bridge, refreshed 2026-10-12

**Purpose:** close the previously identified R4 evidence gap for Gate A against the actual `main` HEAD after CP-C was merged. This addendum supersedes the earlier pre-final-run note that a fresh run was still required after strengthening the global fingerprint gates. The final audit run below was executed after those gates were added; the workflow, runner, aggregator and test file listed here are unchanged in this state/document-only acceptance update.

### Final three-source comparison (before acceptance into main)

| Item | `main` immediately before this change | `stage3b-preserved` | Binding rule / source evidence | Judgment |
|---|---|---|---|---|
| Normative Gate A criterion | `docs/governance/DECISIONS_LOG.md` includes D-2026-10-10-01; the separate Gate A acceptance record remained open in `state.json`. | Diagnostic reference only; the preserved tree has no Gate A bridge files and no implementation was copied from it. | Approved `docs/governance/REFERENCE_AMENDMENTS.md`, Amendment-01, defines Gate A as matching the approved reference/golden. The source reference is `المرجع_النهائي_الموحد_المعتمد.md`. | **MATCH** — no tolerance or business acceptance threshold was added. |
| Data identity and comparison domain | `docs/stage11/dataset_identity.json`, Stage 12 roll-forward validation and closure evidence are present and unchanged. | Used only as diagnostic evidence; not used as a code or dataset source. | Source engine SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`; master seed `20270101`; 25 scenarios; 11,005 canonical trials; 22,546,465 daily rows; expected global ordered-map SHA `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`. | **MATCH** — exact per-trial SHA-256 equality and dataset/report identity gates. |
| Added audit implementation | The five files in this PR were absent from `main` at base SHA `5f4933eed90cdd22fc8037a9785447b3fa510df0`. They are an isolated read-only auditor, strict parser regression test, workflow, aggregator and this R4 report. | The Gate A implementation is not present in its 92-entry tree; no files were copied from it. | Candidate head used for the successful run: `95288a2bccb40d6772f5a5d042fdabc152c9d89a`. Blob identities are recorded below, so the evidence remains bound to the executed implementation even though only R4/state are updated in the current PR revision. | **MATCH** — production engine, RNG, historical Parquet, Stage 7/10 metadata and Stage 12 dataset are not changed. |
| Workflow safety | No Gate A workflow existed in the base main tree. | No workflow was copied. | Workflow blob `7070f168e2c66ccffff5409d517aca25c86f9d0d`; exactly pins push trigger to `tmp/gatea-golden-fingerprint-bridge-20261011`; `contents: read`, `actions: read`; no `workflow_dispatch`, wildcard branch or self-dispatch; every job declares `timeout-minutes` inside the job. Matrix parallelism is capped at five. | **MATCH**. |
| Historical source irregularities | Original source artifacts and identity records remain immutable. | Not applicable. | Stage 10 aggregate Run `37709936740` had a non-success aggregate conclusion; each of its 20 canonical scenario jobs was checked individually and required to be successful. The Stage 11 summary has a recorded 39-character Stage 10 head, while the live Actions run head is 40 characters. The source writer also emits a literal two-byte `\\n` suffix in 60 Stage 10 JSON files. | **DEVIATION disclosed as K_CODE** — exact run API provenance and per-row hashes are checked; only the proven suffix is stripped from an in-memory buffer. Source artifacts and metadata are not rewritten. |
| Final result and acceptance boundary | This addendum and the Gate A record are included in PR #30; current main remains untouched until the authorized merge. | Diagnostic branch remains untouched. | Final artifact and run evidence below. | **PASS for Gate A evidence only**; not a claim that CP-D, final overall stability or delivery is complete. |

### Final authoritative Gate A run

- Run: [38169163565](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/38169163565); conclusion: **success**.
- Tested implementation head: `95288a2bccb40d6772f5a5d042fdabc152c9d89a`.
- Unit test job: success; 25/25 scenario jobs: success; aggregate job: success; total: 27/27 jobs successful.
- Full report artifact ID: `11713395913`; ZIP SHA-256: `e00afa6a5d5ddbc8f84b5e225755535818460ec016d211fad0d1d2a210cfd996`.
- Exact comparisons: 11,005/11,005; Stage 12 daily rows: 22,546,465/22,546,465; per-trial hash mismatches: 0.
- Actual Stage 12 ordered map SHA-256 and independently re-hashed source-golden ordered map SHA-256 both equal the official CP12 global hash: `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`.
- All 20 aggregate gates passed, including completeness/uniqueness, exact per-trial comparison, per-scenario report status, global identity from both CP12-B and CP12-C reports, source SHA provenance, read-only protection, explicit disclosure of the Stage 10 metadata suffix defect and 39/40-character identity-summary deviation, unit tests and matrix status.
- The artifact reports 60 exact Stage 10 suffix recoveries across the 20 non-C100 scenarios (metadata, metrics, and resume descriptors); original raw bytes and SHA values were retained as evidence.
- Code blob identities bound to the run: workflow `7070f168e2c66ccffff5409d517aca25c86f9d0d`; aggregator `0698e1fe1a8907c3469e67348e43d71dcc0e478e`; runner `177eba71e3517ccb123c179fac6cb361127f92c1`; unit test `1ec17cd660fea64d017985dfb9044adda958bab4`. The current change does not alter these files.

### CP closure boundary

Gate A is accepted only within its exact scope: read-only evidence that the canonical Stage 12 per-trial fingerprints match their approved source goldens. This does **not** establish Stage 9C/CP-D, does not change CP-C's N=300/N=600/N=1200 Gate B evidence, and does not declare overall final stability or deliverables complete. The original Stage 10 metadata/head-summary defects remain disclosed as source `K_CODE` findings; neither historical artifacts nor their identity records were edited.
