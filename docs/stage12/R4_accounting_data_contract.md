# CP-B2 R4 — Stage 12 accounting data contract canonicalization

Date: 2026-10-10
Scope: contract and audit documentation only. No engine, tests, RNG, reference, workflow, or state.json changes.

## Required three-way comparison before change

| Item | main (HEAD 5185f51faef836a2884c904b8bb8feb775f5f6c2) | stage3b-preserved (HEAD 2e3aa381d833fe430d2aec42e98dd0d29918c3bf) | Binding reference | Judgment |
|---|---|---|---|---|
| Stage 12 contract | `docs/stage12/accounting_data_contract.json` absent from main. Actual roll-forward report `6084e8f68fa649fcf0726daa04f41ae9b0636706` and closure report `81bc3cd9c7666487b69b644dcc3291d0547c8e8b` both record PASS for 11,005 trials and 22,546,465 daily rows. | Contract absent; historical `state.json` is a Stage 9-era diagnostic record with a different source package SHA and cannot define Stage 12. | Reference §§14.3–14.4 define MASTER_SEED=20270101, SHA-256 RNG and stable trial identity; §§15.1–15.6 and 18.1–18.2 define Excel/source-of-truth and output requirements. | **DEVIATION:** current canonical Stage 12 contract missing from main. Add new v1.1 contract; preserve historical v1.0 unchanged. |
| Dataset schema and keys | Existing CP12-A contract on `tmp/stage12-contract-20261008` commit `6df051f680a43ff86a41d3cfab3c04bce40c2724` identifies daily accounting columns and primary key `(scenario_id, trial_id, date)`; materializer/aggregator code on the accepted Stage 12 branch implements the same schema plus `result_sha256`. | No Stage 12 schema/contract. Do not copy diagnostic code. | Reference §14 requires trial identities to remain fixed irrespective of scheduling; §18 requires trial outputs to remain identifiable and reproducible. | **MATCH** after carrying forward the established key/fields and recording the actual emitted `result_sha256` field. |
| Runtime topology | Historical v1.0 contract describes 45 chunks, max parallel 10, 30-minute job timeout and an estimated 22,850,782 rows; those values are superseded for the adopted Stage12 materialization topology. | No corresponding canonical topology. | Reference §19 requires execution from validated Python outputs; no business rule defines a 45-job workflow. User decision in `DECISIONS_LOG.md` (2026-10-09) adopts 25 scenario materialization jobs plus validate and aggregate. | **DEVIATION resolved in proposed v1.1:** 25 scenario-level materialization jobs plus validate and aggregate (27 jobs total), max parallel 25; timeouts 45 / 360 / 30 minutes. |
| Actual row/output evidence | CP12-B run `37964656154`, head `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`, original and reproduced global hash both `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`, 11,005 trials, 22,546,465 daily rows, zero retries. CP12-C / CP12-D both record zero violations over their full reported scopes. | No Stage 12 actual output evidence. | Reference §§14.3–14.4 require deterministic identity; §§15 and 18 require the final Excel/output package to derive from verified Python outputs. | **MATCH:** use actual, run-backed counts and preserve the old estimate only as historical metadata, not as actual. |

## R4 classification

- **DEVIATION:** canonical Stage 12 accounting data contract missing from main; historic v1.0 workflow description conflicts with the subsequently adopted topology.
- **MATCH:** source SHA, seed, aggregate identity, trial count and row count match the CP12-B/C/D records.
- **VIOLATION:** none found in the documentation-only CP-B2 scope.
- The old v1.0 contract at blob SHA `1915f6b568661b010781f193146546b070006e34` is referenced as immutable historical evidence and is not modified.
- No trials were re-run. No state update is part of this batch.

## CP-B2 proposed files

- `docs/stage12/accounting_data_contract.json` — canonical v1.1, with observed counts and the adopted topology.
- `docs/stage12/R4_accounting_data_contract.md` — this review.

## Current R4 refresh — 2026-10-11 (post-CP-B1 main)

This section is an additive current-state review. The 2026-10-10 R4 record above is preserved verbatim as historical evidence; its comparison baseline was `main@5185f51faef836a2884c904b8bb8feb775f5f6c2` and must not be mistaken for the current main snapshot.

**Live comparison identity**
- Current `refs/heads/main`: `601d8cf92ee64a64d1ac0a53d31d32c84ee830e3` (verified immediately before this update).
- Proposed contract source: PR #18 head `9eb3a89f77048e2d727d5c7ae1117c0d03ba61c6`, contract v1.1.
- `stage3b-preserved`: `2e3aa381d833fe430d2aec42e98dd0d29918c3bf`; diagnostic evidence only. The `docs/stage12` path is absent there, so it cannot supply the current accounting contract.
- Binding reference used for this review: `المرجع_النهائي_الموحد_المعتمد.md`; local-file SHA-256 `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`.
- Live `main/state.json` records CP-B1 complete, CP-B2 next, and CP-D still pending. The state file is not changed by this documentation proposal.

### Current three-way R4 comparison

| Item | current main | `stage3b-preserved` | binding reference / accepted evidence | judgment |
|---|---|---|---|---|
| Canonical Stage 12 contract | `docs/stage12/accounting_data_contract.json` and this R4 file are absent from current `main`; existing roll-forward and closure reports remain present. | No Stage 12 contract; the branch is diagnostic and its Stage 9-era state cannot define current Stage 12. | The reference defines accounting roll-forward requirements in §10.6, deterministic identity in §§14.3–14.4, the separate daily statistical output in §14.7, and output/quality requirements in §§15.1–15.6 and 18.1–18.2; it does not prescribe these GitHub file paths. | **DEVIATION** — a canonical contract is still missing from main. |
| Daily ledger schema | No canonical contract in main; current validation reports identify schema `stage12-daily-accounting-v1`. | No Stage 12 schema. | Accepted producer/aggregator evidence emits the 38 fields in v1.1 order, including `result_sha256`; types match the producer; only `Final_Close_Date` is nullable. Primary key: `(scenario_id, trial_id, date)`; `result_sha256` remains constant within each `(scenario_id, trial_id)`. | **MATCH** — proposed v1.1 schema matches the observed producer schema. |
| Dataset identity and observed counts | Current reports record `source_sha=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, seed `20270101`, global SHA `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`, 25 scenarios, 11,005 trials and 22,546,465 daily rows. | No comparable accepted Stage 12 output evidence. | §§14.3–14.4 govern deterministic identity. Run 37964656154 reports original/reproduced global SHA equality and zero retries; observed counts in v1.1 agree with validation reports. | **MATCH** — observed provenance/counts agree; no trial rerun is requested. |
| Accounting validation | `roll_forward_validation.json` (blob `6084e8f68fa649fcf0726daa04f41ae9b0636706`) and `closure_settlement_validation.json` (blob `81bc3cd9c7666487b69b644dcc3291d0547c8e8b`) each record `overall_result=PASS` and zero reported violations. | No Stage 12 validation outputs. | §10.6 requires roll-forward consistency; §§18.1–18.2 cover output requirements and quality. | **MATCH** for the reported validation scopes only; this does not assert the separate Stage 9C 20-point gate. |
| Accepted workflow topology | Current governance decision log records D3: 25 scenario materialization jobs plus validate and aggregate, 27 total. | No corresponding canonical topology. | User decision in `docs/governance/DECISIONS_LOG.md` dated 2026-10-09 accepts that topology; the reference does not define the historical 45-job design as a business rule. | **MATCH** — proposed v1.1 records 25 + 1 + 1 jobs, max parallel 25, and job timeouts 45/360/30 minutes. |
| Statistical-policy metadata | Current `docs/governance/DECISIONS_LOG.md`, D-2026-10-10-01, records the approved new policy as doubling from 300 (300→600→1200→2400→4800→9600→…), with no ceiling; it supersedes the previous +50 model for new execution. | The diagnostic branch does not override current governance decisions. | The approved current decision is authoritative for future execution. The dataset was produced by Run 37964656154 on 2026-10-09, before the decision dated 2026-10-10. | **DEVIATION requiring explicit disposition** — contract v1.1 `dataset_identity.stability_policy` says +50 and accepted N=550, conflicting with the later normative policy if read as current policy. This proposal preserves the field as historical dataset provenance and does not silently rewrite the decision log or observed dataset. It must not be used to claim future sampling-policy compliance. |
| Reference traceability | The 2026-10-10 R4 section cited its then-current base SHA and is preserved as historical. | Diagnostic branch provides no current reference substitute. | Direct check of the binding reference found no §12.17 heading/reference; relevant sections are §10.6, §§14.3–14.4, §14.7, §§15.1–15.6, the Chapter 16 acceptance inventory, and §§18.1–18.2. | **MATCH** — use these actual sections; do not cite a nonexistent §12.17. |

### Current R4 classification and disposition

- **MATCH:** v1.1's 38-field order, types, nullability, key, fingerprint metadata, Parquet representation, accepted 27-job topology, and recorded run/count/hash evidence match the current producer/validation evidence in the scoped review.
- **DEVIATION:** the canonical contract is absent from current main until merged.
- **DEVIATION requiring review:** `dataset_identity.stability_policy` records +50/550 while D-2026-10-10-01 is the newer normative policy for new execution. This CP preserves the observed dataset identity and exposes the conflict; it does not decide to alter the governance decision, replay data, or amend the accepted output identity.
- **VIOLATION:** no additional runtime violation is asserted by this documentation-only change. This is **not a CP-B2 PASS** and does not close the policy discrepancy or the independent CP-D gate.
- No engine, test, RNG, source reference, workflow, or `state.json` changes are included. No trial was rerun. The CP-B2 proposal remains for explicit review, with the policy discrepancy visible.



---

## R4 Addendum — 2026-10-11 — literal identity reconciliation and bounded documentation correction

**Status:** Additive review record. The 2026-10-10 R4 and the earlier 2026-10-11 review above remain preserved verbatim. This addendum corrects the scope of the prior review: the previous comparison checked the schema shape, nullability, counts and run evidence, but did not compare the four `dataset_identity` policy strings byte-for-byte against the producer and aggregator constants. Its earlier statement that the identity metadata matched was therefore incomplete for these four strings.

### Live identity and evidence pins checked before this addendum

- Repository: `yasmin977209-ux/motorcycle-simulation`.
- Current `main` HEAD: `601d8cf92ee64a64d1ac0a53d31d32c84ee830e3`.
- PR #25 branch: `tmp/cp-b2-accounting-contract-r4-refresh-20261011`; pre-change HEAD: `e6c277fe4b183defdb8bdc52cc1a0ea5749c7d6f`; PR remains open and Draft, based on the current `main`.
- `main/state.json` blob SHA: `a0cb76e175f6196cc304e26138a13398af9f33d1`; it still records CP-B2 as next and source identity `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`.
- Binding reference: `المرجع_النهائي_الموحد_المعتمد.md`, SHA-256 `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`.
- Run 37964656154 source commit: `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`.
- Producer `scripts/stage12_materialize.py` blob SHA: `76ffd5b6bd08358dde364f0677c3d82374ce0590`.
- Aggregator `scripts/stage12_aggregate.py` blob SHA: `fd16864e92d2f4de97e1a9972e3992c38ab4e102`.
- Pre-change contract blob SHA: `424997e7b16ec12addb2d3bd66fc5ad01110a85a`.
- Pre-change R4 report blob SHA: `15d0851a1c54381f7c99ba8c304e56cb828e5556`.

### 1. Primary-key write-time assertion

The pre-change contract asserted `schema.duplicate_missing_policy.primary_key_enforced_at_write_time = true`. The producer at `0156c5f4272eb0ca7e32442657d0df9eaf4973d3` calls `pq.write_table(...)` for per-trial scratch Parquet and `ParquetWriter.write_table(...)` for the scenario artifact without a uniqueness constraint for `(scenario_id, trial_id, date)` at write time.

The aggregator at the same source commit validates the ordered materialized data after writing: it rejects a repeated `(scenario_id, trial_id)` group, rejects a date that is not exactly the following day within a trial (including a duplicate date), checks trial coverage, and rejects drift in `result_sha256`. CP-12-C and CP-12-D add post-materialization checks for schema, date continuity, coverage and closure. The accepted reports record no violations in their declared scopes; this is not evidence that the data contained duplicates, and no such claim is made here.

The binding reference §§14.4, 18.1 and 18.2 requires stable trial identity, Parquet/SQLite outputs and output/accounting quality. The review found no normative text requiring uniqueness to be enforced by the Parquet writer specifically. Accordingly, the documentation flag is corrected to `false`; `duplicate_action = FAIL` and `missing_action = FAIL` remain unchanged. No product, aggregator, test or workflow is altered by this documentation change.

### 2. Exact comparison of dataset identity policy strings

The following literal constant values were obtained from both `stage12_materialize.py` and `stage12_aggregate.py` at source commit `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`. The producer and aggregator values were compared independently and are identical for all four constants.

#### `rng_policy`

**Pre-change v1.1 value:**
```text
SHA-256 key master_seed|scenario_id|trial_id|bike_id|date|event_type; draw from first 8 digest bytes big-endian divided by 2^64
```

**Producer and aggregator literal; copied unchanged into the contract:**
```text
rng.py:SHA-256(seed key master_seed|scenario_id|trial_id|bike_id|date|event_type); draw=first_8_digest_bytes_big_endian/2^64; probability boundaries are deterministic
```

**Finding:** The former value omitted the `rng.py:` prefix, used different wording around the seed key and draw operation, and omitted the explicit deterministic probability-boundary statement.

#### `sampling_policy`

**Pre-change v1.1 value:**
```text
C100 has trial_id 1..1; every non-C100 scenario has trial_id 1..550; no trial was re-run in CP-B2
```

**Producer and aggregator literal; copied unchanged into the contract:**
```text
one-based contiguous trial IDs; C100 scenarios use 1..1; non-C100 scenarios use 1..550; one materialization per scenario/trial; no cross-run inputs or resume
```

**Finding:** The former value summarized scenario trial bounds and added the CP-B2 no-rerun statement, but omitted one-based contiguous IDs, one materialization per scenario/trial, and the no-cross-run-input/no-resume constraints. The contract now records the source constant; run-history claims remain outside the identity string.

#### `trial_id_policy`

**Pre-change v1.1 value:**
```text
one-based contiguous trial IDs; trial_id is logical identity independent of worker execution order
```

**Producer and aggregator literal; copied unchanged into the contract:**
```text
one-based contiguous trial IDs from 1 to scenario target; no duplicate IDs
```

**Finding:** The former value described logical identity and worker-order independence, but did not match the source constant that specifies IDs begin at 1 and forbids duplicates.

#### `stability_policy`

**Pre-change v1.1 value:**
```text
C100 has no CI gate; non-C100 checkpoints start at 300 and increase by 50, three consecutive successful checkpoints; accepted datasets contain 550 trials
```

**Producer and aggregator literal; copied unchanged into the contract:**
```text
C100 uses one deterministic trial and no CI gate; non-C100 checkpoint N=300 then +50; 95% Student-t CI half-width <1% of absolute mean for Final_Net_Project_Equity, Partner1_Final_Entitlement, Partner2_Final_Entitlement; CI_ABSOLUTE_EPSILON=1; three consecutive successful checkpoints; accepted N=550 (checkpoints 450, 500, 550)
```

**Finding:** The former value summarized +50/550 but omitted the three exact metric names, Student-t confidence-interval condition, `CI_ABSOLUTE_EPSILON=1`, and the precise checkpoint wording. The literal source value remains historical dataset identity and must not be read as the current policy for future execution.

### 3. Historical identity versus future statistical policy

The dataset identity emitted by Run 37964656154 on 2026-10-09 used `C100=1` and, for non-C100 scenarios, checkpoints beginning at 300 with historical +50 increases; the accepted dataset contains 550 trials. Its identity remains `source_sha=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, `master_seed=20270101`, schema version `stage12-daily-accounting-v1`, 25 scenarios, 11,005 trials, 22,546,465 daily rows, and global aggregate SHA-256 `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`.

Future execution is governed separately by **D-2026-10-10-01** in `docs/governance/DECISIONS_LOG.md` and **Amendment-01** in `docs/governance/REFERENCE_AMENDMENTS.md`: `C100=1` without a CI gate; non-C100 scenarios start at 300 and double `300 → 600 → 1200 → 2400 → 4800 → 9600 → …`, without a ceiling.

The existing `outputs_and_constraints.note` is extended to state explicitly that `dataset_identity` documents the historical run and that +50/550 is not the future policy. No new JSON field, enum or schema version is introduced. The four identity fields now match the literal producer/aggregator values; this does not rewrite Parquet metadata, replay data, or claim the existing dataset used the future policy.

### 4. Contract gate label

The JSON label `gate = ACCOUNTING_DATA_CONTRACT_DEFINED=PASS` is retained unchanged. No explicit definition of that exact label, or mapping from it to CP-B2 completion, was found in the live decision log, approved amendments or binding reference checked for this R4. It is recorded as a contract-level label only; it must not be read as `CP-B2 = PASS`. Live `main/state.json` still says CP-B2 is pending and the contract is not canonical in `main`.

### 5. Static checks and evidence limits

The documentation changes were checked against source constants and schema declarations. No Parquet artifact was reopened or revalidated in this revision, no published validation report was rewritten, and no simulation or completed trial was rerun. The previous Run 37964656154, CP-12-C and CP-12-D evidence retains its original scope and status.

- Run 37964656154: `completed / success`; source commit `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`.
- CP-12-C Run 37971902520: `completed / success`; its published roll-forward report records `PASS` and zero reported violations.
- CP-12-D Run 37972735159: `completed / success`; its published closure/settlement report records `PASS` and zero reported violations.
- Stage 9C's independent 20-point Parquet-versus-`_STATS` gate remains `NOT_EXECUTED` according to live `main/state.json`; it is separate and is not claimed to pass here.
- Post-change blob SHA of the contract JSON: `dd3f7f102389def92df16af3b0732b77dd66df6d`.
- Post-change blob SHA of this R4 report is given in the execution summary rather than embedded in itself, avoiding a self-referential blob hash.

### 6. Result of this bounded documentation review

- Schema: field count/order/types and nullability align with the producer's `DAILY_FIELDS` and `_daily_schema` definitions.
- Identity text: all four strings match producer and aggregator constants exactly.
- Primary-key description: accurately records that the writer has no write-time uniqueness guard while retaining downstream `FAIL` behavior.
- Historical provenance: source identity, sampling identity, and historical +50/550 policy remain attached to the existing dataset; only the descriptive note separates that history from future execution policy.
- Gate label: retained unchanged and not used to infer CP-B2 completion.
- CP-B2 remains pending explicit review/acceptance and merge authorization. This addendum does not declare CP-B2 complete or `PASS`.

---

## Current R4 refresh — after D-2026-10-11-01 registration — 2026-10-11

This is an additive current-state review. Earlier R4 findings and provenance are preserved; no historical data or JSON identity is rewritten.

### Live repository identity

- Current `main` HEAD: `94b6ea49715c9f845be83b6f106b26c253bf0506`; this includes merged governance PR #26 (merge commit).
- Current `main/state.json` blob SHA: `77af8022cf2e8d70e8dcc7fb0827479f68c912ad`. It records D-2026-10-11-01 in the existing `governance_decisions` map and still lists CP-B2 as next and Stage 9C as not executed.
- Current PR #25 branch head before this R4-only correction: `eb631c38af06600d01c899cbd6bc76c9fc464f98`.
- GitHub comparison `main@94b6ea49715c9f845be83b6f106b26c253bf0506...eb631c38af06600d01c899cbd6bc76c9fc464f98` reports `diverged`, `ahead_by=2`, `behind_by=1`, with merge base `601d8cf92ee64a64d1ac0a53d31d32c84ee830e3`. The actual compare lists only the two intended additions, `docs/stage12/accounting_data_contract.json` and this R4 document. No branch reset or rebase has been performed.
- Current decision log blob SHA: `5896e166be27170454d4103bd83638bad05b5b62`; amendments blob SHA: `55d410cda50b77ee708374343af6205c6fdfb9e6`; SHA-semantics note blob SHA: `134363f0f2834f8087760b3148910a1a3d3af38b`.
- Binding reference file SHA-256: `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`.

### Current three-way R4 comparison

| Item | main at `94b6ea49715c9f845be83b6f106b26c253bf0506` | stage3b-preserved at `2e3aa381d833fe430d2aec42e98dd0d29918c3bf` | Binding reference / approved decisions / source | Judgment |
|---|---|---|---|---|
| Canonical Stage 12 contract | Both proposed contract files remain absent; roll-forward and closure reports remain historical evidence. | Stage 12 contract and governance files are absent; its Stage 9 state is diagnostic only. | Reference §§14.3–14.4 establish deterministic trial identity; §§15 and 18 govern verified outputs. The accepted topology is the explicit decision in DECISIONS_LOG.md, not a rule copied from stage3b. | **DEVIATION:** canonical contract is still not on main until this PR is accepted. |
| Schema, key and source constants | No Stage 12 materializer/aggregator source is on main. | No Stage 12 schema/source to compare. | Producer at source commit `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`, blobs `76ffd5b6bd08358dde364f0677c3d82374ce0590` and `fd16864e92d2f4de97e1a9972e3992c38ab4e102`, matches the 38-field contract and four historical identity strings. | **MATCH** for the explicitly compared schema and constants; it does not prove Gate A/B. |
| Historical sampling versus future policy | D-2026-10-10-01 and Amendment-01 remain normative for future execution; D-2026-10-11-01 and Amendment-05 authorize analytical reuse of historical trials 1–300 for Gate B only, subject to compatibility checks. | No normative policy status; diagnostic only. | Historical Run 37964656154 uses `+50/550`; the accepted future policy doubles from 300. D-2026-10-11-01 prohibits modifying the historical identity or rerunning completed trials. | **MATCH** only when the historical and future policies remain explicitly distinguished. |
| Contract-level gate label | The decision log, amendment, and state do not define `ACCOUNTING_DATA_CONTRACT_DEFINED=PASS` as CP-B2 completion. | No definition available. | No such binding definition was found in the reviewed reference or approved decision/amendment records. | **UNDEFINED_BUSINESS_RULE:** preserve the label; do not use it to infer CP-B2 PASS. |
| Implementation state | The live state still lists CP-B2 as next and Stage 9C as pending. | Its Stage 9 state is not authoritative for current execution. | No historical run or roll-forward/closure report substitutes for the new Gate A/Gate B criteria. | **PENDING:** both CP-B2 completion and Stage 9C's independent gate require their own evidence. |

### Scope of this R4 refresh

The only pre-existing content edit in this refresh is removal of the one confirmed trailing-whitespace occurrence at the end of line 3. This addendum records the changed live main identity and the effect of the newly merged governance decision; it does not change the JSON contract, engine, RNG, trial outputs, historical data metadata, or source identity.
