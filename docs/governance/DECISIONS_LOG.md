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


## D-2026-10-17-04 — first-passing-checkpoint stopping policy (partial ruling)

**Status:** PARTIALLY APPROVED BY PROJECT OWNER; initial N=300 §2.5 evaluation remains PENDING  
**Date:** 2026-10-17  
**Authority:** Direct project-owner instruction in the conversation dated 2026-10-17.  
**Scope:** Per-scenario minimum statistical cohort, doubling schedule, stopping rule, and interpretation of historical stability failures. The reference file itself is not modified.

### Approved normative clauses

1. Every one of the 25 scenarios, including C100 scenarios, must cover trial IDs 1..300 before the first stability decision. This narrowly supersedes D-2026-10-10-01's C100 one-trial startup rule and any later one-trial C100 shortcut for this execution policy. C100's deterministic business-result equivalence remains a separate identity check; no unsupported claim is made that the statistical CI policy for C100 is otherwise resolved by this clause.
2. The per-scenario checkpoint sequence is N=300, 600, 1200, 2400, 4800, 9600, ... with no fixed global cap. After the initial checkpoint and after each doubling, evaluate that scenario and stop adding trials at its first passing checkpoint. Do not require all scenarios to reach the same N.
3. Record the accepted stopping count per scenario (stable_at_n / equivalent output field), along with source SHA, master seed, RNG/sampling/schema identity, trial-ID coverage, fingerprints, and every checkpoint result. The final cohort size is the sum of the accepted per-scenario counts, not a hard-coded total.
4. Do not rerun a completed trial ID. Use identity-verified existing results where authorized and materialize only missing IDs. This decision does not authorize changing SOURCE_SHA, RNG, master seed, historical Parquet, or accepting candidate output as its own golden reference.
5. Preserve every historical failed transition verbatim in the history. A prior failed transition is not a permanent blocker to overall stability: a later checkpoint may pass the applicable current transition and permit stopping under this policy. The earlier failure remains visible and must never be relabeled PASS or deleted.
6. The numerical thresholds and near-zero treatment in Reference §2.5 are not changed by this decision. This entry does not amend the reference document.

### Pending first-checkpoint rule — do not infer

The current §2.5 seven-metric evaluator compares values between adjacent checkpoints. N=300 is the first checkpoint under this policy, so there is no preceding approved doubling checkpoint against which to evaluate those seven changes. The owner instruction requires a stability decision at N=300 but does not specify that missing comparison baseline. Record this as PENDING/UNDEFINED_BUSINESS_RULE; do not substitute Gate B alone for overall stability, invent an N=150 checkpoint/baseline, relax the threshold, or initiate a new statistical run until this clause is resolved.

### Explicit non-claims / boundaries

- Gate A exact-golden/source-identity validation, Gate B CI semantics where applicable, and the seven §2.5 metrics remain distinct gates; one PASS does not imply all-gate stability.
- No production checkpoint, extra Golden coverage, source identity change, test/workflow edit, merge, delivery approval, or Release is authorized by this documentation entry alone.
- Implementation changes to tests or GitHub Actions require an R4 proposal and the separate explicit approval required by project controls.

**References:** D-2026-10-10-01; Reference §§2.5 and 14.2; D-2026-10-12-01; D-2026-10-14-12 as recorded on the candidate; explicit owner instruction dated 2026-10-17.

## D-2026-10-17-05 — compare every actual adjacent stability transition per scenario

**Status:** PARTIALLY APPROVED; the first decision at N=300 remains PENDING  
**Date:** 2026-10-17  
**Authority:** Direct project-owner instruction in the conversation dated 2026-10-17.  
**Scope:** Comparison of §2.5 stability metrics across per-scenario checkpoint transitions. This decision does not amend the normative reference file.

### Approved clauses

1. For each of all 25 scenarios (including C100), trial IDs 1..300 are mandatory baseline coverage before any stability decision or adaptive escalation.
2. Apply §2.5 to every actual adjacent transition that exists in that scenario's checkpoint history: compare the immediately previous authorized checkpoint against the current checkpoint for the same scenario. Do not compare different scenarios, skip an existing adjacent transition, create a fictitious transition, or require two transitions as a universal count.
3. A transition passes the §2.5 stability criterion only when all seven required metrics pass together using the reference's unchanged relative threshold (<1%) and unchanged near-zero absolute fallback (REFERENCE_EPSILON=1e-6; absolute difference <1 currency unit).
4. The adaptive schedule remains per scenario: N=300, 600, 1200, 2400, 4800, 9600, ... . Once an eligible adjacent transition passes, stop that scenario at the first passing checkpoint and record stable_at_n as its current N, with checkpoint and data-identity evidence.
5. Do not invent N=150 or another unapproved baseline. Keep every historical failure verbatim. A later passing eligible transition may support a later stability conclusion without erasing or relabelling a historical failure.

### Still pending — no §2.5 comparison exists at the first N=300 point

The rule above defines comparisons whenever an actual adjacent checkpoint transition exists; it does not create a predecessor for the first N=300 point. Consequently, N=300 alone cannot yield a §2.5 transition pass under the reference's pairwise formula. The owner's preference to stop at N=300 if already stable is not operationally reconciled with this missing predecessor.

Until the owner resolves this narrow point, do not claim §2.5 stability at N=300, manufacture a comparison baseline, substitute Gate B for the seven-metric test, or run a new production checkpoint. The remaining choice is whether N=300 is coverage-only and the first possible §2.5 stability decision is on the 300→600 transition, or whether the owner defines a separate first-point criterion explicitly consistent with the governing reference.

### Boundaries

- Existing §2.5 numerical thresholds and metric definitions are unchanged.
- Gate A, Gate B, and §2.5 remain separate gates; passing one does not establish overall stability.
- The production Gate A provider and SOURCE_SHA drift blockers remain open.
- No test/workflow edits, simulation, completed-trial rerun, merge, release, or final-delivery approval is made by this governance record.

**References:** Reference §2.5; D-2026-10-17-04; D-2026-10-10-01; direct owner instruction dated 2026-10-17.

## D-2026-10-17-06 — resolve the first §2.5 stability checkpoint

**Status:** APPROVED BY PROJECT OWNER  
**Date:** 2026-10-17  
**Authority:** Direct owner reply “اعتمد” to the explicit choice between (a) N=300 as mandatory coverage only, with the first §2.5 stability decision on transition 300→600, and (b) a separately defined N=300 initial-point criterion.  
**Scope:** Resolves only the first-checkpoint question left pending by D-2026-10-17-04 and D-2026-10-17-05. Does not amend the normative reference.

### Approved decision

1. Trial IDs 1..300 remain mandatory for each of the 25 scenarios, including C100. N=300 is **coverage only**; it is not itself a passing §2.5 stability checkpoint and cannot set stable_at_n=300.
2. The first eligible §2.5 stability comparison is the actual per-scenario transition **N=300 → N=600**. Therefore, no scenario can be declared stable by §2.5 before its N=600 results are available and the seven-metric comparison passes.
3. Evaluate all seven §2.5 metrics together on every actual adjacent transition in each scenario's own checkpoint history, using the reference's unchanged rule: relative change strictly below 1% when |old_value| >= 1e-6; otherwise absolute difference strictly below 1 currency unit.
4. After N=600, follow the per-scenario doubling sequence 1200, 2400, 4800, 9600, ... only when the latest applicable transition fails. Stop that scenario at the first passing eligible transition and record stable_at_n as the new/current checkpoint N. A transition is not allowed to skip an existing adjacent checkpoint.
5. The policy change does not authorize any production execution by itself. Gate A must have a validated approved-golden provider, and source identity/data provenance blockers must be resolved before new production checkpoint execution. Existing completed trial IDs must not be rerun or relabelled; do not silently change SOURCE_SHA, master_seed, RNG, sampling, historical data, or schema.
6. Preserve the historical failure record unchanged. A historical failure is not by itself a permanent blocker when a later applicable transition passes, but it remains visible and must not be rewritten as PASS.

### Disposition of prior pending clause

This decision resolves the first-point ambiguity only by choosing N=300 coverage-only and N=300→600 as the first eligible §2.5 comparison. It supersedes the pending alternatives recorded under D-2026-10-17-04 and D-2026-10-17-05 only for this narrow question. All other boundaries and project blockers remain.

**References:** Reference §2.5; D-2026-10-17-04; D-2026-10-17-05; direct owner approval dated 2026-10-17.

