# Stage 9A — Deviations and Evidence Gaps

## Gap register after Phase V

| Gap | Status | Evidence | Blocking? | Action |
|---|---|---|---|---|
| G-01 Verify v2 after path 1 failed | REAL-NON-BLOCKING | Run `37650868144` failed with `FileNotFoundError: ... docs/stage9a/representative_trial_ids.json`; v2 Runs `37653597583` and `37653604522` succeeded | No | Preserve provenance in this document; no product change |
| G-02 `operating_net_profit` absent from anomaly report | REAL-NON-BLOCKING | Official `verification_report.json` anomaly summary omits the field; final workbook contains `Operating_Net_Profit` in 75 worksheet XML files and explicitly in `C100_G100_STATS` and `C100_G100_ACCTG` | No | Document only |
| G-03 manifest path on M-6 branch | REAL-NON-BLOCKING | `docs/stage9a/dataset_manifest.json` absent on `tmp/stage9a-06-manifest-20261007`; present on final build branch with blob SHA `e796fa2443493b607f1f9c60b58eb63607959c26` | No | No relocation required for product; final canonical file is recorded on main during Phase R |
| G-04 permanent R4 audit | REAL-BLOCKING | No `docs/stage9a/R4_audit.md` on main, stage3b-preserved, or final build branch before Phase R | Yes | Resolved by Commit 1 |
| G-05 independent AST gate | NOT-REAL as a blocking requirement | Reference §15.6 requires Excel error-free output; reference §19.2 defines separate `excel_builder.py` and `validation.py`; no explicit `ast.parse`/py_compile gate is mandated | No | No gate added |
| G-06 builder + openpyxl not canonical on main | REAL-BLOCKING | main lacked `scripts/excel_builder.py` and `openpyxl`; final build branch contained both | Yes | Resolved by Commit 1 |
| G-07 stale `enrichment_runs` in official Stage9A report | REAL-BLOCKING | Official artifact 11507380986 contains `37655041728, 37660610243, 37660658613`; final manifest maps scenarios to `37655041728` and `37662891608` | Yes | Corrected field only in Commit 1 |
| G-08 final output naming inconsistency | REAL-NON-BLOCKING | Existing artifact/report names differ from the unified naming convention requested for closure documentation | No | Document only; no product rename required |

## V-02.5 — 9C pre-flight data discovery

The official Stage 7 block artifact for `C100_G100` (`11312276587`) contains:

- one Parquet file: `block_1_1.parquet`
- one metadata file: `block_1_1_metadata.json`
- `trial_count = 1`
- final-trial fields including `trial_id`, `final_close_date`, `final_net_project_equity`, `final_cash`, `cumulative_project_profit`, `operating_net_profit`, `termination_count`, `owned_bikes`, `held_assets`, and partner entitlements.

The block Parquet is not a daily-row ledger for all trials. The enriched scenario artifact contains `trial_results.parquet`, `daily_distribution.parquet`, four representative JSON payloads, and fingerprints; it does not contain an individual daily accounting ledger for all trials.

The final workbook's `_ACCTG` sheets contain daily accounting rows for the representative P50 payload used by the builder, not a 9005-Trial × every-day accounting ledger.

Therefore a complete 9C requirement of 5 roll-forwards × 9005 trials = 45,025 trial-level daily tests cannot be truthfully reported from the currently available artifacts.

### 9C scope decision

**Stage 9C must be PARTIAL unless additional per-Trial daily accounting data becomes available.**

No missing daily values are inferred or reconstructed from aggregate fields.

## Product / procedure separation

### Product verdict
**PRODUCT-VERIFIED**

Evidence:
- 25 scenarios
- 9005 trials
- 100 representatives
- 163-test inventory: 162 PASS / 0 FAIL / 1 EXCLUDED
- 185 sheets
- 0 Excel error cells
- 0 formula cells
- XLSX SHA-256: `0fb325fc9e196a534ba8ab7484dcfd0541cefd3a2ca37c3b6f930e3215f62f6d`
- Global manifest SHA: `892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6`

### Process / provenance verdict before Phase R
**AUDIT-PARTIAL**

The process gaps are G-04, G-06, and G-07. They concern canonical provenance and reproducibility of the closure record, not a demonstrated corruption of the verified Stage 9A product.

## [0.1.a]

The current source search did not establish an authoritative repository occurrence of `[0.1.a]`, and the supplied reference does not define a corresponding authoritative value. Status remains:

**UNVERIFIABLE**

This is not converted into a fabricated YES/NO state.


## C100 Sampling Override (قرار مستخدم رسمي)

**التاريخ:** 2026-10-08T01:32:17+02:00

**القاعدة في المرجع:** C100 = 200 تكرار
(الباب 2.5 من المرجع).

**القيمة المنفذة فعلاً:** C100 = 1.

**القرار:** اعتماد C100 = 1 رسميًا.
السبب: C100 هو المستوى الحتمي الوحيد (collection_probability = 1.0)،
فالتباين صفري رياضيًا، ولا حاجة إحصائية لتكرارات متعددة.
تكرار واحد يكفي لإثبات الحتمية والتحقق التنفيذي.

**المرجعيات المتأثرة:** الباب 2.5.
**التصنيف:** OVERRIDE-ACCEPTED-BY-USER.
**الحالة:** RESOLVED.

### state.sha vs canonical_content_sha

- `state.sha` semantics: `parent_state_commit_pointer` — يشير إلى الـcommit السابق الذي يحمل أحدث حالة معتمدة، ولا يُستخدم كمرجع لـ`main HEAD`.
- `canonical_content_sha` يبقى منفصلاً عن `state.sha`، ولا يحل محل دلالة `state.sha` الجديدة.
- في الحالة الحالية: `state.sha = a7db0153299b3af8f89111bec52bb07d1356509c`، بينما `canonical_content_sha = a7db0153299b3af8f89111bec52bb07d1356509c`؛ تساوي القيمتين هنا نتيجة أن C-7 هو آخر commit غيّر الحالة الدلالية قبل تسجيل C-8، وليس لأن `state.sha` يشير إلى `main HEAD`.
