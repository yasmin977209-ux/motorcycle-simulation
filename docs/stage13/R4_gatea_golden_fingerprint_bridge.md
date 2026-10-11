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
- The audit parser may remove exactly the verified two-byte suffix `\\n` **in memory only**, and only if the original bytes end in `}\` followed by `n` and the remainder parses as one JSON object with no other trailing bytes. It must record the raw hash, this parse disposition, exact workflow source/blob and artifact provenance in the Gate A report. No general permissive JSON recovery is allowed.
- Validate all per-trial hash arrays and range/run/source identity after parsing. If a file deviates from this exact defect pattern or any block identity/fingerprint mismatch exists, that scenario fails and Gate A remains unestablished.
- This known formatting defect does not alter the stored hash strings; whether the full Gate A comparison can be accepted remains determined solely by all exact row-level golden comparisons and identity gates, and the defect remains disclosed in the report.

