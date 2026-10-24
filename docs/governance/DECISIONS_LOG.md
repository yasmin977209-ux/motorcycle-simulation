# سجل القرارات الإدارية — 2026-10-09

**الحالة:** قرارات صادرة عن المستخدم ومسجلة للتنفيذ المتتابع.  
**نطاق هذا CP:** تسجيل القرارات ومراجعها وتحديث `state.json` لتسجيل اكتمال CP-A والخطوة التالية والعوائق المفتوحة. لا يُعلن هذا السجل وحده اجتياز بوابة، ولا يُدمج أي فرع.

## القرار 1 — G7 في Stage 11

**تاريخ القرار:** 2026-10-09  
**التصنيف المعتمد بقرار المستخدم:** `K_SPEC`  
**القرار:** عُرّف G7 سابقًا بشرط `next_trial_id - 1 == trial_id_max`. الشرط لا يصلح للتحقق من عدم إعادة التشغيل عند مقارنة مؤشر حالة Stage 7 المنتهي عند 450 بمجموعة بيانات مدمجة تشمل إضافة Stage 10 حتى 550. يعتمد تعريف G7 المعتمد الآن على هدف البوابة: **التحقق من عدم إعادة replay** في دمج Stage 7 وStage 10، مع فحص هوية التكرارات، وعدم التداخل، وعدم وجود فجوات، وبصمات التكرارات.

**الأدلة الموجودة وقت تسجيل القرار:**
- الفرع المؤقت `tmp/stage11-manifest-11005-20261008`، commit `f17e1a59a91df8d4a967ebc3cbbd035ca1230439` (CP-11-B-Rev1).
- الملف `docs/stage11/global_manifest_11005.json`، blob SHA `27e94a0ddb573b4d09701faac9978168f62ded89`.
- يسجل الحقل `g7_revised_verification.result = PASS` والادعاءات: مطابقة مؤشر Stage 7 في 25/25، ومطابقة إضافات Stage 10 في 20/20، وعدم تداخل 25/25، وعدم وجود فجوات 25/25، والتحقق من دليل SHA لكل تكرار.
- بصمة المجموعة المجمعة المسجلة: `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`.

**قيد التوثيق:** الملف المشار إليه أعلاه ما زال يسجل `manifest_status = FAIL` وملاحظة الفشل القديمة إلى جانب نتيجة تحقق G7 المنقحة. لا يمحو هذا السجل الأثر التاريخي؛ يلزم في CP لاحق مصالحة الحالة العامة للـmanifest مع تعريف G7 المعتمد والأدلة أعلاه، ثم حفظ نتيجة التحقق في الملف الرسمي على فرع عمل. لا يُعاد تشغيل أي تجربة لهذا الغرض.

## القرار 2 — التفويض بأثر لاحق لإعادة materialization في Stage 12

**تاريخ القرار:** 2026-10-09  
**القرار:** يصدر المستخدم تفويضًا رسميًا بأثر لاحق لإعادة حساب نطاقات التكرارات المطلوبة من أجل إنشاء daily accounting ledger الذي لم يكن موجودًا في مخرجات Stage 7/Stage 10 السابقة. هذا توثيق لتفويض بأثر لاحق، **ولا يعني أن التفويض كان سابقًا للتشغيل**.

**النطاق الدقيق للتشغيل:** توليفات C100 استخدمت trial ID واحدًا لكل توليفة؛ والتوليفات غير C100 استخدمت `trial_id=1..550`، بإجمالي 11,005 تكرارات عبر 25 توليفة.

**دليل التشغيل:** [GitHub Actions Run 37964656154](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/37964656154)، branch `tmp/stage12-b3-25jobs-20261009`، head SHA `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`.
- `overall_result = PASS`
- `original_global_sha256 = reproduced_global_sha256 = 7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`
- `match = YES`
- 25 ملف Parquet، 22,546,465 صفًا يوميًا، `retries = 0`
- `source_sha = f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`، `master_seed = 20270101`.

تطابق البصمة دليل على تطابق الهوية/النتيجة وفق خوارزمية التجميع المسجلة؛ ولا يُستشهد بالبصمة وحدها كبرهان عام على عدم حدوث تنفيذ متكرر. نطاق هذه الموافقة هو إعادة materialization اليومية المحددة أعلاه.

## القرار 3 — اعتماد طوبولوجيا Stage 12 الجديدة

**تاريخ القرار:** 2026-10-09  
**القرار:** يعتمد المستخدم طوبولوجيا 25 وظيفة materialization، وظيفة واحدة لكل سيناريو، بوصفها الطوبولوجيا الرسمية لعقد Stage 12؛ مع وظيفتي validate وaggregate منفصلتين، أي 27 وظيفة workflow إجمالًا.

**الدليل:** workflow `.github/workflows/stage12-b3-25jobs.yml` على `tmp/stage12-b3-25jobs-20261009`، blob SHA `bbe4bfd5e3bd95edb7d41f90cdf30cb325363d95`، Run `37964656154`. سجل التشغيل يمتد من `2026-10-09T17:12:48Z` إلى `2026-10-09T17:40:40Z` (27 دقيقة و52 ثانية وفق طوابع تشغيل GitHub).
- 25 وظيفة materialization، `max-parallel = 25`.
- مهلة validate هي 45 دقيقة؛ مهلة وظائف materialization المسجلة في workflow هي 360 دقيقة؛ مهلة aggregate هي 30 دقيقة.
- اكتملت البوابة بنجاح مع تطابق global SHA، ومن دون retries.

**تنفيذ القرار:** هذا السجل يثبت اعتماد المستخدم. عقد Stage 12 الرسمي على `main` لم يكن موجودًا عند تسجيل القرار؛ ويلزم في CP توثيقي لاحق إنشاء `docs/stage12/accounting_data_contract.json` بإصدار جديد، مع الإشارة إلى عقد CP-12-A التاريخي على `tmp/stage12-contract-20261008` commit `6df051f680a43ff86a41d3cfab3c04bce40c2724`، وتوثيق اختلاف 45-job design عن الطوبولوجيا المعتمدة الحالية. لا تُعاد التجارب من أجل تحديث العقد.

## حدود الأثر

1. لا يغيّر هذا السجل ملف `state.json` أو يعلن إغلاقًا جديدًا لأي CP.
2. لا يُعدّل هذا السجل كود المحرك أو الاختبارات أو workflows.
3. لا يدمج أي فرع تلقائيًا؛ تبقى التغييرات المقترحة خاضعة لمراجعة PR.
4. لا يرفع Stage 9C من `PARTIAL` إلى `PASS`؛ بوابة Parquet مقابل `_STATS` المستقلة تظل بحاجة إلى تنفيذ ودليل وفق تعريفها المعتمد.

---

## D-2026-10-10-01 — السياسة الإحصائية

**Status:** APPROVED — NORMATIVE
**Scope:** نقاط البداية والتصعيد الإحصائي وبوابتا Gate A/Gate B.
**Supersedes:** نقاط البداية والتنفيذ الإحصائي التاريخي في §§2.5 و14.2 للتنفيذ الجديد؛ يظل الأصل دون تعديل. يُلغى الحد الأدنى 5000 وأي تفسير خطي +50.
**Details:** C100=1 للتحقق من الحتمية بلا CI وبـtrial_id/بذور مختلفة؛ C085/C070/C050/C030 تبدأ عند 300 مع تصعيد مضاعف 300→600→1200→2400→4800→9600→... بلا سقف. Gate A يطابق المرجع/الذهبي. Gate B يطلب نصف CI 95% بتوزيع t أقل من 1% من |mean| للمقاييس Final_Net_Project_Equity وPartner1_Final_Entitlement وPartner2_Final_Entitlement، مع CI_ABSOLUTE_EPSILON=1 قرب الصفر. يُشترط نجاح البوابتين في ثلاث نقاط متتالية؛ وإذا نجح Gate B عند 300/600/1200 مع تغير P50 بأكثر من 5% بين النقاط فالحالة PRELIMINARY_STABLE وتستمر عند 2400. تُسجل كل النقاط في stability_history.json. لم يُعثر على عبارة حرفية +50 داخل §16؛ لا تُنسب للمرجع.
**Reference:** D-2026-10-10-01؛ REFERENCE_AMENDMENTS.md / Amendment-01.

## D-2026-10-10-02 — العدد الفعّال للاختبارات

**Status:** APPROVED — NORMATIVE
**Scope:** جرد القبول وتقاريره.
**Supersedes:** أي احتساب يساوي بين مخزون 163 والاختبارات الفعّالة.
**Details:** المخزون 163؛ العدد الفعّال 162؛ Test 158 مصنف K_TEST ولا يُصلح أو يُستبدل أو يُحذف. تقرير Stage12-D السابق (162 PASS, 0 FAIL, 1 K_TEST) دليل تشغيل سابق، لا قرار مستقل.
**Reference:** D-2026-10-10-02؛ REFERENCE_AMENDMENTS.md / Amendment-02.

## D-2026-10-10-03 — خمسة أدوار تمثيلية

**Status:** APPROVED — NORMATIVE
**Scope:** REPRESENTATIVE_CASES والسجلات اليومية.
**Supersedes:** الإشارات إلى أربعة أدوار أو ثلاثة أدوار إضافية ضمن المجموعة نفسها.
**Details:** P50/P10/P90/LossCase/MaxCase. LossCase هو أقل abs(Final_Net_Project_Equity) (الأقرب إلى الصفر) أياً كانت إشارة القيمة؛ MaxCase أعلى قيمة موجبة. كسر التعادل لجميع الأدوار بأصغر trial_id. إن لم توجد قيمة موجبة، تسجل UNDEFINED_BUSINESS_RULE وتتوقف الموافقة على التوليفة حتى توجيه.
**Reference:** D-2026-10-10-03؛ REFERENCE_AMENDMENTS.md / Amendment-03.

## D-2026-10-10-04 — معمارية Excel

**Status:** APPROVED — ARCHITECTURE TARGET
**Scope:** التصميم المستقبلي لمسار إنشاء Excel.
**Supersedes:** أي تفسير يجعل بناء Excel مسؤولية غير مفصولة الطبقات.
**Details:** scripts/excel_builder.py هو Orchestrator للـCLI/config/mode، وتحميل Parquet/SQLite، والتسجيل والأخطاء دون إنشاء أوراق. scripts/stage13_assemble.py هو Assembler بـassemble_workbook لبناء 185 ورقة والتجزئة والتحقق بلا CLI مستقل. الواجهة build_excel(dataset_path, output_path, mode="canonical") تستدعي load_dataset ثم stage13_assemble.assemble_workbook(data, output_path, mode). canonical=11005 افتراضياً، sample=625، demo تشغيل صغير. هذا هدف معماري لا يثبت تنفيذ الكود الحالي.
**Reference:** D-2026-10-10-04؛ REFERENCE_AMENDMENTS.md / Amendment-04.

---

## D-2026-10-11-01 — Authorize Analytical Reuse of Historical Trials

**Status:** APPROVED BY PROJECT OWNER  
**Date:** 2026-10-11  
**Scope:** Analytical inputs for Gate B only.

### Decision

1. Historical results with `trial_id=1..300` for each of the 20 non-C100 scenarios may be used as **analytical inputs only** for Gate B calculations under the normative policy in D-2026-10-10-01.
2. These historical results may be included in cumulative Gate B checkpoints where those trials are part of the sample, including N=300, N=600, N=1200 and subsequent required checkpoints. At each checkpoint, complete only the additional required trials that have not previously completed; do not rerun any completed trial.
3. This analytical use does not resume, extend, consolidate, merge, relabel, or modify metadata for the historical dataset, and does not change its source identity or fingerprints.
4. Preserve provenance for every historical analytical input, including historical Run 37964656154, `source_sha=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, the historical `+50/550` sampling policy, scenario, trial_id, schema identity, and available source/output fingerprints.
5. Before Gate B calculation, verify required-trial completeness and key uniqueness, metric correctness and extraction path, and compatibility of engine identity and input parameters. Reference §§14.3–14.4 establish deterministic RNG and stable `trial_id` only when the relevant source and inputs match; they do not replace those compatibility checks. If compatibility cannot be established, hold the affected use and do not claim Gate B PASS; do not rerun trials 1–300.
6. This decision does not change the normative future statistical policy, permit historical metadata edits, or authorize rerunning any completed trial.
7. This decision neither satisfies Gate A nor establishes Gate B in advance. Both gates retain their own criteria and evidence requirements.
8. This decision supersedes the earlier restriction **only** as to using historical trials 1–300 as analytical inputs for Gate B. All other restrictions concerning identity changes, reruns, and gate acceptance remain in force.

### Implementation boundary

This decision authorizes analytical read-only reuse only. It is not authorization to resume or consolidate the historical dataset and does not authorize a change to any historical Parquet metadata, row, fingerprint, or global aggregate identity.

**Reference:** `docs/governance/REFERENCE_AMENDMENTS.md / Amendment-05`.


## D-2026-10-11-02 — CP-B2 acceptance semantics and extended analytical reuse

**Status:** APPROVED BY PROJECT OWNER  
**Date:** 2026-10-11  
**Scope:** CP-B2 contract-gate interpretation and analytical inputs for cumulative Gate B checkpoints only.

### Decision

1. `ACCOUNTING_DATA_CONTRACT_DEFINED=PASS` is an informational status of the contract artifact, not an independent declaration that CP-B2 is complete. The field remains unchanged unless a separate evidence-backed correction is required.
2. CP-B2 can be accepted only after the documented contract deliverable, source/schema/policy checks, historical identity checks, required static checks, and required review/merge steps are proven with evidence. A clean whitespace check or a status field alone is insufficient.
3. Historical trial IDs `301..550`, for each of the 20 non-C100 scenarios, may be used as analytical inputs for cumulative Gate B checkpoints only, extending D-2026-10-11-01. This includes their contribution to `N=600` and subsequent cumulative checkpoints where they are part of the sample.
4. Analytical reuse is not resume, dataset extension, consolidation, cross-run metadata merge, relabeling, or a change of historical data identity or fingerprint. Do not modify historical Parquet, row values, metadata, source identity, or global/per-trial fingerprints. Do not rerun completed trials.
5. Preserve provenance for every historical record from IDs `301..550`: historical Run `37964656154`, `source_sha=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, historical sampling policy `+50/550`, scenario, `trial_id`, schema identity, and available source/output fingerprints.
6. Before using any records, verify source/engine/input-parameter compatibility, exact per-trial fingerprints, completeness and uniqueness of scenario/trial keys, and correctness of metric extraction. If any required evidence is absent or mismatched, hold the affected use and do not claim Gate B PASS.
7. For `N=600`, use the compatible historical sample `1..550` as read-only analytical inputs and execute only the not-yet-completed required trials `551..600` for each non-C100 scenario. For later cumulative checkpoints, execute only the additional not-yet-completed trial IDs required by the live policy. Preserve separate provenance for historical and newly executed inputs.
8. This decision neither establishes Gate A nor establishes Gate B in advance. All statistical criteria, including the Student-t CI rule, absolute epsilon, and consecutive-checkpoint rule, remain unchanged under D-2026-10-10-01.
9. The decision supersedes the prior hold/restriction only for the explicit CP-B2 gate interpretation in items 1–2 and analytical reuse of completed historical IDs `301..550) for Gate B under items 3–7. It does not supersede any other acceptance criteria or authorize other forms of data reuse.

**References:** D-2026-10-10-01; D-2026-10-11-01; Amendment-01; Amendment-05; Amendment-06.


## D-2026-10-12-01 — Normative definition of Gate B P50 change >5%

**Status:** APPROVED — DELEGATED PROJECT-OWNER DECISION  
**Date:** 2026-10-12  
**Scope:** Resolving the formula/denominator omission in the P50 >5% branch of D-2026-10-10-01 only.

### Normative decision

1. Apply this rule independently to each of the 20 non-C100 scenarios. C100 remains on its separate deterministic verification path and is excluded from this P50 comparison.
2. At each cumulative checkpoint N=300, 600 and 1200, calculate P50 as the linear 50th percentile of `Final_Net_Project_Equity` over the complete valid trial IDs `1..N` for that scenario. This matches the existing N=1200 audit extraction (`numpy.quantile(..., 0.50, method="linear")`) and does not change trial identity or simulation output.
3. Compare **adjacent checkpoints only**: N=300→600 and N=600→1200. The denominator is the absolute P50 at the previous checkpoint:
   `change_percent = 100 * abs(P50_new - P50_previous) / abs(P50_previous)`.
4. The continuation trigger is strict: a relative change **greater than 5.0%** at either adjacent comparison requires `PRELIMINARY_STABLE` and a next N=2400 checkpoint for that scenario. Exactly 5.0% does not exceed the threshold.
5. Near-zero denominator handling follows the already-approved mathematical pattern in reference §2.5, without introducing a new epsilon: if `abs(P50_previous) < REFERENCE_EPSILON (1e-6)`, do not compute a percentage; stability for this comparison requires `abs(P50_new - P50_previous) < ABSOLUTE_EPSILON (1 currency unit)`. A difference greater than or equal to one unit requires continued sampling. This P50 fallback is separate from the Gate B CI near-zero rule.
6. Escalation is per scenario. If escalation is required, only the new trial IDs `1201..2400` may be materialized; completed IDs must not be rerun. If the P50 trigger is not met, this condition alone does not require N=2400. All existing CI, identity, Gate A and final-stability criteria remain unchanged.
7. This decision fills the missing formula only. It does not amend the reference file, alter the 5% threshold, relax any CI criterion, establish Gate A, or declare overall project acceptance.

### Evidence-backed application to N=300/600/1200

The three preserved checkpoint reports each contain 60/60 CI points passed, with zero failed points. The N=1200 report's P50 series was re-evaluated read-only under this formula: 20 scenarios × 2 adjacent transitions = 40 comparisons; none exceeded 5.0%. The maximum N=300→600 change was 0.348341% (`C050_G000`); the maximum N=600→1200 change was 0.191901% (`C050_G000`). No P50-triggered N=2400 is required by these observations. See `docs/stage12/R4_gateb_n1200_parallel20_resume_20261012.md` and its 2026-10-12 addendum for source identities, artifact digests and per-scenario values.

**References:** D-2026-10-10-01; `REFERENCE_AMENDMENTS.md / Amendment-01`; reference §2.5; R4 decision record dated 2026-10-12.

## D-2026-10-12-02 — CP-D canonical XLSX precision gate scope

**Status:** APPROVED — DELEGATED PROJECT-OWNER DECISION  
**Date:** 2026-10-12  
**Scope:** CP-D / Stage 9C exact Parquet-to-XLSX numeric serialization gate only.

### Normative decision

1. The CP-D precision gate uses the canonical full-scope Stage 9A Parquet dataset identified by source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, Stage 7 Run `37225915321`, master seed `20270101`, and dataset-manifest SHA-256 `892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6`. Its scope is 25 scenarios and 9,005 unique trial rows (one trial per C100 scenario and 450 per non-C100 scenario).
2. The gate compares four metrics — `Final_Net_Project_Equity`, `Partner1_Final_Entitlement`, `Partner2_Final_Entitlement`, and `Final_Cash` — against `MIN`, `P10`, `P50`, `P90`, and `MAX` on each scenario's `_STATS` sheet. This is 20 comparisons per scenario and 500 comparisons total.
3. Parquet remains the computational source of truth and Excel is the exported presentation/audit layer. Quantiles use `numpy.quantile(values, q, method="linear")`; all 500 values must be numeric, finite, and **exactly equal**. No tolerance, rounding, epsilon, or relaxation is allowed.
4. The serializer correction is restricted to the numeric lexical representation of affected target cells where the openpyxl serialization would lose float round-trip precision. It does not alter the quantile formula, underlying metric, source Parquet, dataset identity, fingerprints, historical workbook, or any completed trial.
5. The historical Stage 13 sample gate defined for a 625-trial cohort is a separate gate/cohort. It is not the CP-D canonical source and cannot replace, be merged with, or be represented as the full 9,005-trial CP-D audit.
6. CP-D PASS certifies only this exact export-consistency gate plus its approved regression/acceptance/path inventory. It does **not** upgrade the historical overall Stage 9C status from `PARTIAL` to full PASS: the Stage 9C report's full daily accounting-ledger coverage for all 9,005 trials remains unavailable, and its previously accepted partial-closure decision is not reopened by this precision correction.
7. The prior raw `python -m pytest -q tests` diagnostic remains a reported non-PASS and must not be renamed or described as all-tests PASS. The four Stage 5 fixture failures are resolved in the approved fixture-first inventory run. The seven out-of-inventory failures remain documented and classified in the R4 report; no tests were modified to satisfy the candidate.

### Evidence-backed application

Run `38165878333` on candidate head `2680335d365a8f923aec076f1fb72cb410f821fb` completed both jobs successfully. The canonical precision gate passed 25/25 scenario packages, 9,005/9,005 unique trial rows, 185 worksheets, zero Excel-error cells, zero formulas, and 500/500 exact numeric comparisons. One target cell required patching; all 500 target cells were verified post-write. The original published workbook SHA-256 remains `0fb325fc9e196a534ba8ab7484dcfd0541cefd3a2ca37c3b6f930e3215f62f6d`; the separate candidate workbook SHA-256 is `4bc35a3047b5790e3921475d78a5dd84e05a5c52a729e3ce1f5caa01355185b1`. No simulation or new trial execution occurred.

**References:** `docs/stage9c/STAGE9C_REPORT.md` §C-6; `docs/stage9a/dataset_manifest.json`; `docs/stage9c/R4_export_numeric_precision.md`; Stage 9C canonical precision gate Run `38165878333`. The 625-trial Stage 13 definition is maintained as a distinct cohort and is not amended here.

## D-2026-10-24-01 — Explicit Gate A Golden provider authorization and bounded use

**Status:** APPROVED — current explicit project-owner delegation dated 2026-10-24  
**Scope:** authorization to wire and validate the already-produced, read-only Gate A Golden fingerprint map in the Stage 7 acceptance path. This is a new decision for this exact scope; it does not reconstruct, replace, or claim recovery of the missing/corrupted text of D-2026-10-14-01 or D-2026-10-15-10.

### Decision

1. Authorize the pinned existing Golden evidence only as an immutable reference for exact per-trial TrialResult identity checks. The canonical model source remains `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, and the master seed remains `20270101`. For each comparison, validate scenario ID, integer trial ID, source SHA, seed, and exact TrialResult SHA-256. Missing evidence or unsupported trial coverage is BLOCKED; identity/hash mismatch is FAIL. Never generate, infer, or relabel a Golden hash from the trial currently being tested.
2. The immutable map scope is **25 scenarios and 25,205 trial fingerprints**: the base Gate A map has 24,005 fingerprints (20 non-C100 scenarios at IDs 1..1200 and the five C100 scenarios at canonical trial ID 1 each), plus the separate 1,200-ID extension for `C030_G030` covering IDs 1201..2400. Keep these distinct identities separate: the **24,005-fingerprint base Gate A map SHA-256** is `166cae242d972c597f1a4466d184062f3d959649eb5e2440ad8de8b75663ff2c`; the **25,205-fingerprint combined extended Gate A map SHA-256** is `0fbe3aa87a253f9527953c77b0a122871c9344f75ece6c8a49da99b2a85c1ce1`; the **11,005-fingerprint Stage 12 canonical map SHA-256** is `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`; the non-C100 N=600 map SHA-256 is `dd537fe96c5a8736201441e9a620db148a0d16cadae518d2a777fbc723db395f`; and the non-C100 N=1200 map SHA-256 is `eaf1f8f3060aac6967b064d3199c082d2a9b47027c865628986f56cbb23c1fc3`.
3. The only approved coverage through N=2400 is `C030_G030`, IDs `1201..2400`, source Run `38662076725`, head `aafe5946a8a51c991471057d71f5643c46087086`, artifact `11940485523`, artifact ZIP SHA-256 `049af21733b59d753967f27f251cb88fec122b5e1ff4f99d77b9215114c9d3e3`, ordered extension-map SHA-256 `0c7679edfbee54797d64fc66e17116f0db617d1e0fa5f7ee21395fe98a628c65`. Coverage for any other scenario beyond ID 1200 is unsupported and must be blocked before running its trial/checkpoint. C100 remains canonical trial ID 1 only under this decision; no C100 trial extension is authorized here.
4. The provider must revalidate immutable run identities, artifact digests, row-level provenance, coverage, and the expected canonical map hashes at runtime; the short-lived cache must round-trip to the same verified map. This decision authorizes wiring/read-only integrity verification, not rewriting old artifacts or declaring Gate A passed without matching actual results.
5. The current user delegation expressly covers the implementation, tests, and candidate-only workflow verification for this scope. **It does not waive** the separate `STATISTICAL_INFERENCE_BLOCKED` gate. No production Monte Carlo, Trial, checkpoint, stability declaration, or final delivery acceptance is authorized until the statistical execution contract has been implemented, validated on the exact source, and separately accepted. The provider must continue to fail closed on that blocker.
6. Do not modify the pinned source, RNG/seed, historical Parquet/JSON evidence, trial IDs, scenario manifest, or historical run artifacts. Preserve the previous C030_G030 N=300→600 failure record; an N=2400 Golden extension is reference preparation, not a completed N=2400 statistical checkpoint.

### Verification identity

This authorization is tied to the provider implementation constants and runtime provenance checks in `scripts/golden_reference_provider.py`. Its exact map and scope validation is separately exercised by the candidate-only verifier and tests. Any change to the pinned artifact IDs, digests, map hashes, source SHA, seed, or supported coverage requires a new review.

**Boundary:** this decision establishes only authority to consume this precisely scoped, immutable Golden map as a test reference. It does not retroactively repair D-2026-10-14-01 / D-2026-10-15-10 text and does not establish statistical stability or project release acceptance.

## D-2026-10-24-02 — Stage 11 execution scope and topology

- **Status:** APPROVED_BY_DELEGATED_PROJECT_OWNER; scoped to Stage 11 scope only.
- **Decision:** Stage 11 is the documentation/identity reconciliation stage for the already-existing canonical 11,005-trial cohort. Its deliverables are `docs/stage11/dataset_identity.json`, `docs/stage11/global_manifest_11005_reconciled.json`, and their reconciliation evidence. Stage 11 does not create a new production simulation workflow, worker matrix, Monte Carlo run, Trial, or checkpoint.
- **Existing execution topology remains separate:** Stage 7 is the 25-scenario matrix with maximum parallelism 10 and per-scenario checkpoint/state handling; Stage 12 materializes the 25 scenario ledgers and then validates/aggregates; Stage 13 performs the delivery assembly. This decision documents scope; it does not change any workflow.
- **Evidence boundary:** `docs/stage10/STAGE10_METRICS.json` records the historical benchmark of 45 matrix jobs, observed max concurrency 10, matrix wall 1,051 seconds, and slowest job 470 seconds. It also records `source_identity=PARTIAL`, `fidelity=PARTIAL`, and `topology_status=NOT_DEFINED_IN_CURRENT_REPOSITORY`. Those metrics describe the Stage 10 benchmark, not a measured full adaptive Stage 7 or Stage 11 production runtime.
- **Open blockers preserved:** Stage 10 metadata/source-identity/fidelity drift remains open; the 40-minute internal timeout / 45-minute job timeout risk remains unmeasured under a full production workload; statistical execution remains blocked until the time-uniform inference contract is implemented and accepted. This decision is not Gate A PASS, Gate B PASS, scenario stability, or delivery acceptance.
- **No data mutation:** this decision does not alter the canonical 11,005-trial identities, source SHA, master seed, RNG, Trial IDs, trial/daily ledgers, manifest hashes, historical stability claims, or the approved 300→600→1200→2400 execution policy. It does not authorize any new Trial/checkpoint/Golden expansion.
- **Disposition:** `STAGE11_SCOPE_CLOSED_DOCUMENTATION_ONLY`; keep Stage 10 metadata drift and runtime-risk blockers explicitly open.

References: `docs/stage11/dataset_identity.json`; `docs/stage11/global_manifest_11005_reconciled.json`; `docs/stage11/R4_manifest_reconciliation.md`; `docs/stage10/STAGE10_METRICS.json`; `docs/PROJECT_CONTINUITY.md` and the five supplied references.
