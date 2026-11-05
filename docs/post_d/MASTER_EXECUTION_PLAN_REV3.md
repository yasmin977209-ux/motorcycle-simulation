# MASTER EXECUTION PLAN REV3 — Motorcycle Simulation
**تاريخ الإعداد:** 2026-11-05  
**المستودع:** `yasmin977209-ux/motorcycle-simulation`  
**فرع العمل:** `tmp/d1-rebuild-20261101`  
**Baseline branch HEAD قبل إنشاء هذه الخطة:** `e508daf3520e2fec267e10745fb46c020dd24dec`  
**Baseline main HEAD:** `01a6f79eedc522bb734ed9c5ea31beee581f2468`  
**تصنيف الخطة:** وثيقة تخطيط/حوكمة تنفيذية؛ لا تمثل تشغيلًا أو قبولًا أو تفويضًا جديدًا.

---

## 1. الغرض والسلطة

تجمع هذه الخطة المسار المتبقي من E3 إلى E6، مع إجراءات التحضير والتدقيق اللازمة، في خطة واحدة قابلة للتتبع. لا تستبدل المرجع الحاكم ولا تنشئ قواعد أعمال أو عتبات أو هويات أو صلاحيات.

ترتيب السلطة:
1. قرارات المالك الصريحة وحدودها.
2. المرجع الحاكم v2.4.0 وفق القرار `D-2026-10-30-REFERENCE-V2.4.0` بحالة `APPROVED_BY_OWNER`.
3. أدلة GitHub الحية (الملفات والـcommits والـActions والـArtifacts).
4. هذه الخطة كأداة تنظيم وربط فقط.
5. السجلات التاريخية والذاكرة للسياق لا لإثبات الحالة الحالية.

### 1.1 مراجع الهوية المرجعية — لا تخلط بينها

- `current_governing_reference_sha256`: v2.4.0 = `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b` (القيمة المصرح بها في قرار المالك).
- `historical_execution_reference_sha256`: v2.3 = `e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f`.
- v2.3.1 = `CLOSED_UNAPPROVED_CANDIDATE`.
- مرجع v2.4.0 المنشور في GitHub يحمل Git blob SHA-1 `9fe43bfbb2cbfd2bb7f7010866e7469506d22c33` وحجمًا مسجلًا قدره 401,397 bytes. لا تدّعي هذه الخطة إعادة حساب Raw SHA-256 من البايتات؛ قرار المالك هو الحاكم رغم أن رأس الوثيقة ما زال يعرض `PROPOSED_FOR_OWNER_ADOPTION — NOT_EFFECTIVE_YET`. يُحفظ هذا التعارض ويُعالج Append-only، ولا تُعدّل بايتات المرجع ضمن هذه الخطة.

### 1.2 نقطة الأساس الحية عند إعداد REV3

| العنصر | الحالة المتحققة |
|---|---|
| فرع العمل | `tmp/d1-rebuild-20261101` موجود |
| HEAD الفرع قبل الخطة | `e508daf3520e2fec267e10745fb46c020dd24dec` |
| HEAD main | `01a6f79eedc522bb734ed9c5ea31beee581f2468` |
| مقارنة الفرع بـ main | Diverged؛ الفرع متقدم 938 commit ومتأخر 2 commits |
| D0–D6 | `PASS_SCOPED_WITH_LIMITATIONS` لكل مرحلة، ضمن نطاق الأدلة فقط |
| E0 | `PASS_SCOPED` — جرد فجوات فقط |
| E1 | `PASS_SCOPED` — تسوية وثائقية/حوكمية فقط |
| E2 | `PASS_SCOPED` — تدقيق أدلة تاريخية؛ لا يعلن Production Gate A |
| E3–E6 | `NOT_STARTED` |
| التصنيف العام | `T2_INTERIM / NOT_FINAL_BLOCKED` |

هذه اللقطة مرتبطة بالـBaseline أعلاه. قبل كل مرحلة/جلسة لاحقة يجب إعادة استخراج HEAD للفرع وmain من GitHub API وقراءة الملفات ذات الصلة من الفرع الحي. لا تُستخدم هذه اللقطة كبديل عن ذلك.

---

## 2. مبادئ التنفيذ الإلزامية

1. العمل على `tmp/d1-rebuild-20261101` فقط. `main` للقراءة والمقارنة فقط.
2. لا Merge أو Rebase أو Force-push أو حذف تاريخ أو تغيير `main`.
3. لا تغيير للمرجع أو قواعد الأعمال أو الحسابات أو RNG أو sampling أو العتبات أو طرق الاستدلال دون قرار مالك مستقل ومحدد.
4. لا تغيير لـ`SOURCE_SHA` أو `cohort_id` أو `MASTER_SEED` أو Trial IDs أو أي هوية تشغيلية دون قرار مالك صريح.
5. لا تشغيل Trial أو Simulation أو Monte Carlo أو Golden revalidation أو N expansion بموجب هذه الخطة وحدها.
6. لا تشغيل `N=4800`؛ يظل `NOT_EXECUTED` ويتطلب قرارًا منفصلًا.
7. لا backfill أو تخمين أو zero-fill للحقول المحاسبية التاريخية المفقودة.
8. لا تعديل أو استبدال أو حذف Artifact أو manifest تاريخي.
9. لا خلط بين S6 وC100 وStage 12/13، ولا بين Workflow HEAD وmodel `SOURCE_SHA` وexecution commit وworkflow-file blob.
10. التوثيق Append-only. لا تمحُ إخفاقًا أو لقطة قديمة؛ أضف تصحيحًا مؤرخًا مع روابط وأدلة.
11. لا يُستخدم `VERIFIED_LIVE` أو `PASS` لملف إلا مع URL دقيق وRaw SHA-256 محسوبة من البايتات وGit blob SHA-1 والحجم وcommit الحاوي.
12. نجاح Workflow لا يثبت وحده سلامة Artifact أو محتواه أو نطاقه. اربط كل نتيجة بـRun ID وJob ID وtested SHA وArtifact ID/digest/size.
13. عند أي mismatch أو نقص في identity/provenance/coverage، يكون السلوك fail-closed: إيقاف المسار المتأثر وتسجيله دون إصلاح تخميني.
14. لا انتقال إلى بوابة/مرحلة لاحقة حتى تُثبت بوابة المرحلة السابقة على exact final HEAD.

---

## 3. الحالة المثبتة والقيود الثابتة

### 3.1 D0–D6

كل مراحل D0 إلى D6 لها إغلاق `PASS_SCOPED_WITH_LIMITATIONS` ضمن نطاقاتها فقط. لا يعني ذلك قبول المشروع أو إغلاق كل متطلبات المرجع. تبقى القيود التالية:

- D3-18: سجل القبول الأعلى يذكر `PASS_SCOPED` بينما خريطة المتطلبات تسجل `NOT_RUN`; يجب إبقاء الفرق بين قبول Artifact ضمن نطاقه وبين تنفيذ Test 18. لا ترفع Test 18.
- 105 normalized manifest statuses = `NOT_VERIFIED` عند غياب expected byte sizes مستقلة.
- D4 Test 176 وfull numeric-token-to-Registry lineage لكل قيم DOCX = `NOT_RUN`.
- D5 حزمة منشورة/متحقق من سلامتها ضمن النطاق، لكن Full 177-test suite = `NOT_RUN`.
- D6 تدقيق مستقل محدود؛ Tests 176/179/180/181/183 = `NOT_RUN`، وعمليات الاستدعاء التاريخية 175/182/186 ليست مثبتة كاستدعاءات فعلية لمجرد وجود فحوص scoped.
- تغطية المخرجات الـ28 لم تثبت بالكامل: وجود سبعة deliverables لا يثبت 24 مخرجًا لكل مجموعة من 25 مجموعة سيناريوهات إضافة إلى 4 مخرجات مشروع.

### 3.2 E0 وE1 وE2

- E0 `PASS_SCOPED`: سجل فجوات، لا يغلق الفجوات.
- E1 `PASS_SCOPED`: reconciles documentary/evidence-role conflicts فقط، لا يغير قواعد أو هويات.
- E2 `PASS_SCOPED`: تدقيق تاريخي وتشخيص producer path؛ Production Gate A يبقى `NOT_DECLARED`.

### 3.3 بوابات لا يجوز ترقيتها

| البوابة/المؤشر | الحالة الثابتة |
|---|---|
| Financial Gate A | `PASS_SCOPED` فقط |
| Production Gate A | `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS` |
| Gate B عند N=2400 | `FAIL_SCOPED (10/10)` |
| Stability | `NOT_CONVERGED (0/60)` |
| N=4800 | `NOT_EXECUTED` |
| Full Logging | 105 مفاتيح تمثيلية فقط؛ ليست 48K Trial logging |
| Normalized manifest | `NOT_VERIFIED_105_OF_105` |
| C100 Golden revalidation | `NOT_RUN` على السلالة المطلوبة الجديدة |
| Full 177 unique-test suite | `NOT_RUN` |
| Final acceptance / P17 / P18 / Convergence | `NOT_DECLARED` |

الحقول الخمسة التاريخية التالية تبقى `MISSING_EVIDENCE` ولا تُخمن أو تُصفّر:
`Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Total_Assets`.

---

## 4. تسوية هويات E2 — شرط سابق لأي تنفيذ لاحق

يجب أن تظهر الهويات الثلاث في كل سجل/جدول/تقرير منفصلة:

### 4.1 Original S6 التاريخي
- Source Run: `40731224990`.
- execution commit: `a23ba71f48487f3ebead99bc30039b14ef9b7609`.
- `SOURCE_SHA=da1a9ea9b5cd789c944de3f07b08395bb67c49e7`.
- cohort: `s6-v23-da1a9ea9`.
- `MASTER_SEED=20270101`.
- 20 scenarios × 2,400 = 48,000 Trial identities.
- producer `monte_carlo.py::_daily_snapshot` حفظ إسقاطًا يوميًا مختصرًا وأسقط الحقول الخمسة. لا يمكن استعادتها من ذلك الإسقاط.

### 4.2 Old-identity Replay Reconstruction — نتيجة ناجحة لكن محدودة
- Run: `41958935113`.
- النتيجة: `PASS_SCOPED_REPLAY_RECONSTRUCTION`؛ 20/20 scenario jobs وaggregate نجحت.
- 48,000 Trial identities و98,323,918 daily rows.
- Aggregate Artifact: `13393273763`; SHA-256 المسجلة `fcd8f86c8c60b9577931839b2755041e0072063cf963c396ddcb318a3d14b7c1`.
- هذا Replay أعاد بناء الإسقاط المحاسبي على الهوية القديمة؛ workflow استخدم execution source القديم وأضاف instrumentation overlay. لا يثبت تنفيذ model source الجديد، ولا يغير تاريخ Original S6، ولا يغلق Production Gate A تاريخيًا، ولا يُعد تشغيل السلالة الجديدة.

### 4.3 New S6 + C100 lineage — Preflight فقط
وفق سجل قرار المالك `docs/post_d/E2_OWNER_DECISION_APPROVED_A_2026-11-05.md`:
- S6 source pin candidate: `002b74893ca9dfea864e83fecc558f2388748ffe`.
- repair reference: `a5573eb1891ed2c56b01f6c9b3ccfe9619a08358`.
- S6 cohort candidate: `s6-v23-rebuild-20261105`.
- C100 cohort candidate منفصل: `c100-v23-rebuild-20261105`.
- seed المقترحة/الثابتة في القرار: `20270101`.
- Execution authorization state: `WAIT_FINAL_OWNER_CONFIRMATION`.

لا تُطلق أي S6/C100 Trial أو Golden revalidation أو D0'–D6' قبل تأكيد مالك نهائي مستقل يقبل صراحةً source pin، الهويتين، C100 comparison contract، workload/stop rules. كما أن C100_SOURCE_SHA يجب تثبيته صراحةً ولا يُستنتج من S6 source pin.

### 4.4 عقد C100 الذي ينتظر تأكيد المالك
- المسارات: `C100_G100`, `C100_G070`, `C100_G050`, `C100_G030`, `C100_G000`.
- 300 execution records لكل مسار (1,500 إجماليًا) إذا أُكد النطاق.
- C100 حتمي و`N_unique_paths=1`; التكرارات ليست 1,500 عينة مستقلة.
- يجب أن يحدد قرار المالك هل تتم مقارنة كل واحدة من 300 سجلات المسار مع Golden fingerprint المعتمد الوحيد لذلك المسار، لا الادعاء بوجود 1,500 historical independent matches.
- لا تدخل سجلات C100 في S6 stochastic N أو Stability/FWER.

---

## 5. خارطة الطريق والبوابات

### Gate 0 — Baseline & Preservation (قبل كل مرحلة)
**الغرض:** تثبيت المصدر والبيئة والأدلة قبل أي عمل.
- اقرأ HEAD للفرع وmain من GitHub API.
- اقرأ prompt library REV2، owner decisions، reference decision، status، handoff، E0/E1/E2 registers، D0–D6 closure/evidence.
- تحقق من PRs/Actions/Jobs/Artifacts/Releases المرتبطة.
- سجّل exact commit, file URL, blob SHA-1, Raw SHA-256, size, tested SHA وartifact metadata.
- قارن مع baseline السابق وسجل أي تغيّر Append-only.
**مخرج البوابة:** Baseline record وevidence index محدثان.  
**الرفض:** إذا تعذر تحديد exact HEAD أو تضاربت الهوية أو تعذر الوصول إلى مصدر حاكم؛ توقف قبل تعديل يعتمد على ذلك.

### E3 — Test/Fixture/Output Traceability
**الحالة الحالية:** `NOT_STARTED`; لا يبدأ إلا بعد إقرار E2 disposition النهائي في السجل. لا تعني نتيجة Old-identity Replay وحدها أن السلالة الجديدة أصبحت جاهزة.
**النطاق:**
1. تدقيق سجل الاختبارات المعياري: 193 صفًا = 177 executable unique tests + 15 aliases + 1 documentation row.
2. بناء سجل لكل اختبار: canonical ID، alias mapping، executable target، test file/function، fixture، fixture provenance، requirement clauses، result، run/tested SHA، output/artifact، limitations.
3. لا تُحسب aliases كاختبارات فريدة، ولا تُحسب الوثيقة كاختبار.
4. إثبات ما شُغّل فعليًا مقابل ما هو `NOT_RUN`; لا تُحوّل فحوص scoped إلى test invocation.
5. تصنيف fixtures: historical artifact bytes / committed fixture / inline workflow fixture / synthetic fixture. لا تصف synthetic بأنها historical.
6. إعداد `Required_Output × Scenario × Trial_Scope × Artifact × Evidence` matrix لكل 28 required outputs:
   - 24 مخرجًا لكل واحدة من 25 scenario groups حيث ينطبق تعريف المرجع.
   - 4 project-level outputs.
   - لكل خلية: required output ID، scenario ID، Trial range/cohort، source identity، schema/version، artifact member/path، expected/actual rows، date coverage، digest/size، source commit، tested SHA، result، gap.
7. التحقق من Full Logging: 105 keys ممثلة فقط؛ لا extrapolation إلى 48K.
8. التحقق من manifest: تبقى 105 statuses `NOT_VERIFIED` ما لم يظهر expected byte size مستقل لكل بند.
9. معالجة D3-18 تناسبيًا: `PASS_SCOPED` على مستوى artifact disposition لا يغير requirement invocation `NOT_RUN`.
**مخرجات E3:** Test Traceability Matrix، Fixture Provenance Ledger، 28-output Coverage Matrix، Full Logging Scope Report، Manifest Evidence Gap Report، E3 result/evidence/continuity.
**بوابة E3:** لا PASS إلا بعد تغطية كل requirement/output مطلوب أو تصنيفه بدقة كـ`MISSING_EVIDENCE`/ `NOT_RUN`/ `BLOCKED`، ونجاح الاختبارات المطلوبة على exact tested SHA مع remote readback. لا تُخفى فجوات التغطية.

### E4 — Financial/Statistical Gate Reconciliation
**الحالة الحالية:** `NOT_STARTED`; لا تشغيل Trials أو تغيير thresholds.
**النطاق:**
1. ربط كل Gate result بـSOURCE_SHA وcohort_id وseed وscenario وN وcheckpoint وRun ID وtested SHA وArtifact.
2. فصل Test 192 synthetic coverage proof عن Production Gate B. نجاح المنهج الاصطناعي ليس نتيجة Gate B إنتاجية.
3. تسوية التعارض المسجل حول Gate B عند N=2400 (ملخص الحالة يقول `FAIL_SCOPED (10/10)` بينما سجل `statistical_execution_gate.json` يذكر أن تقييم الإنتاج غير مكتمل/نقاط 300/600/1200 وN=2400 NOT_EXECUTED). لا تحسمه بالافتراض؛ حدد cohort/run/checkpoint scope وأضف reconciliation Append-only.
4. الحفاظ على Stability `NOT_CONVERGED (0/60)` ما لم تظهر أدلة جديدة صحيحة ضمن الهوية والنطاق المعتمدين.
5. إبقاء Financial Gate A `PASS_SCOPED` منفصلًا عن Production Gate A `NOT_DECLARED`.
6. لا N=4800 ولا Trial إضافي ولا إعادة Golden إلا بقرار مالك مستقل.
**مخرجات E4:** Gate-to-Identity Map، Gate B conflict reconciliation، Stability ledger، financial-vs-production gate matrix، E4 evidence and handoff.
**بوابة E4:** لا ترقية PASS ولا تغيير N/عتبة/منهج دون نص مرجعي وقرار مالك. إذا لم يمكن تسوية provenance، الحالة `CONFLICTED` أو `MISSING_EVIDENCE`.

### E5 — P17 Independent Acceptance Audit
**الحالة الحالية:** `NOT_STARTED`; مستقلة عن إغلاق D6.
**النطاق:**
1. مدقق مستقل لا يعتمد على builder أو authoring workflow وحده.
2. يعيد جلب artifacts الدقيقة بالـIDs ويفحص byte size/digest/manifest/member inventory/CRC/path safety.
3. يتحقق من lineage من كل قيمة رقمية إلى المصدر/registry، مع عدم تجاوز Test 176.
4. يتحقق من متطلبات المحاسبة والإغلاق والـdaily roll-forward على البيانات التي توجد لها أدلة فعلية فقط؛ لا يملأ الخمسة historical missing fields.
5. يتحقق من 28-output matrix، test/fixture provenance، full logging/manifest status، language/format integrity، reproducibility.
6. يثبت الاستثناءات والمخاطر والفجوات، ويصدر توصية مستقلة لا قرار قبول تلقائي.
**مخرجات E5:** Independent Audit Report، reproducibility manifest، exception ledger، P17 recommendation.
**بوابة E5:** لا يعلن `P17_FINAL_ACCEPTED` إلا بقرار مالك صريح وبالدليل المطلوب؛ نجاح التدقيق لا ينشئ الإذن.

### E6 — P18 Release Eligibility & Handoff
**الحالة الحالية:** `NOT_STARTED`; E6 لا تعني Release.
**النطاق:**
1. التحقق من أن P17 status والقرار/التوقيع المطلوبين موجودان.
2. التحقق من كل deliverable/manifest/identity/version/digest وملفات التسليم.
3. مراجعة المخاطر والاستثناءات وretention/archival والروابط الدائمة.
4. تجهيز release candidate checklist وhandoff للمستخدم والمالك.
5. عدم نشر Release أو إعلان `P18_RELEASED` دون إذن مالك مستقل.
**مخرجات E6:** Release Eligibility Report، delivery index، archive/retention report، final handoff draft.
**بوابة E6:** `ELIGIBLE_FOR_OWNER_REVIEW` لا تعني Release. النشر يتطلب قرار مالك منفصل.

---

## 6. مسار السلالة الجديدة (مسار مستقل ومشروط)

هذا المسار ليس جزءًا من صلاحية هذه الخطة التشغيلية، ويظل مشروطًا بتأكيد مالك نهائي منفصل:

1. إكمال Preflight بلا Trials: تثبيت S6 source pin وC100 source identity المنفصلة، cohort IDs، seed، Trial identity map، contract، expected outputs، resource estimate، stop conditions، retention.
2. توثيق قرار المالك النهائي وموافقته على كل عناصر القائمة صراحة.
3. بعد الموافقة فقط، تشغيل S6/C100 بالهوية المصرح بها دون تعديل القواعد/thresholds.
4. S6: 20 scenarios × 2,400 Trial = 48,000 identities. مقارنة one-to-one لكل financial `trial_fingerprint` مع counterpart التاريخي حسب scenario وTrial ID؛ أي mismatch واحد يوقف كامل المسار فورًا.
5. C100: مساراته الخمسة مستقلة؛ 300 records/path عند إقرار العقد؛ لا تُحسب كعينات مستقلة.
6. التحقق من كل daily row: اكتمال التواريخ/التغطية، عدم وجود nulls، full balance projection، `Total_Assets == Total_Equity` عندما تنطبق قاعدة liabilities=0، و`Balance_Difference == 0`; roll-forward لكل مكون وفق المرجع. أي صف غير متزن يوقف المسار.
7. فصل Financial Trial Fingerprint عن RNG Audit Fingerprint المرتبط بـSOURCE_SHA؛ اختلاف RNG provenance لا يُخلط مع اختلاف النتيجة المالية.
8. مقارنة الحقول/التواريخ اليومية المشتركة فقط بين old/new schema. لا تفرض تطابق Daily Path Fingerprints عند تغير schema دون تعريف معياري.
9. إنتاج D0'–D6' كخط مستقل تمامًا؛ لا تعِد تسمية أو استبدال Artifacts D0–D6 التاريخية.
10. لا تنتقل نتائج السلالة الجديدة إلى Production Gate A إلا بعد تدقيق مستقل على artifacts الدقيقة. ولا تُغيّر Gate B/Stability/N بسبب نتائج إعادة البناء.

**الشرط الحالي:** `WAIT_FINAL_OWNER_CONFIRMATION`. لا تنفيذ بموجب REV3.

---

## 7. مصفوفة القرارات والصلاحيات

| القرار/الفعل | الوضع الحالي |
|---|---|
| إنشاء/تحديث وثائق الخطة والحالة على فرع العمل Append-only | مسموح |
| قراءة GitHub والتحقق من الملفات والـRuns/Artifacts | مسموح |
| تشغيل اختبارات وثائقية/ساكنة غير منتجة للبيانات | فقط إذا كانت ضمن بوابة محددة ومصرح بها ولا تشغل Simulation/Trial |
| تعديل الكود أو الاختبارات | يتطلب تحديد defect ونطاق معتمد؛ لا يغير قواعد/هويات |
| تغيير v2.4.0 أو قواعد الأعمال/المحاسبة/RNG/العتبات | قرار مالك مستقل |
| تغيير SOURCE_SHA/cohort/MASTER_SEED/Trial IDs | قرار مالك مستقل |
| أي Trial/Simulation/Monte Carlo/Golden revalidation/N expansion | قرار مالك صريح منفصل |
| N=4800 | قرار مالك مستقل |
| backfill/estimate/zero-fill للحقول الخمسة | غير مسموح بهذه الخطة؛ لا يُنفذ دون قرار مستقل، ولا يوصف كتاريخ أصلي |
| تعديل/حذف Artifact أو manifest تاريخي | قرار مالك مستقل |
| تعديل main أو merge/force-push/rebase تاريخي | قرار مالك مستقل |
| نشر Release أو إعلان FINAL_ACCEPTED/P17_FINAL_ACCEPTED/P18_RELEASED/CONVERGED | قرار مالك مستقل |

---

## 8. المخاطر ووسائل التحكم

| الخطر | الأثر | التحكم/شرط الإيقاف |
|---|---|---|
| الخلط بين Replay القديم والسلالة الجديدة | ادعاء مصدر/فوج غير صحيح | Identity registry منفصل وربط كل تقرير بالـSOURCE_SHA/cohort |
| stale status snapshots | فتح/إغلاق مرحلة خطأ | اعتماد آخر سجل مؤرخ مع exact HEAD وإبقاء التاريخ |
| Workflow HEAD ≠ model source | attribution خاطئ | حقول مستقلة لكل SHA في manifest |
| missing accounting fields | Production Gate A غير قابل للإعلان | إبقاء MISSING_EVIDENCE وعدم التخمين |
| Gate B conflict | استنتاج قبول/فشل غير دقيق | ربط كل نتيجة بـrun/cohort/checkpoint ثم Append-only reconciliation |
| synthetic Test 192 ≠ production Gate B | ترقية زائفة | فصل evidence classes |
| 105 keys ≠ 48K logs | نقص تغطية | لا extrapolation؛ output/logging matrix |
| C100 repetitions ≠ independent samples | تضخيم N/FWER | `N_unique_paths=1` وعدم دمجه مع S6 |
| temporary artifact expiry | فقدان الوصول إلى الدليل | archive دائم مع owner approval حيث يلزم؛ لا تغيير artifact الأصلي |
| reference header conflict | التباس السلطة | قرار المالك هو الحاكم؛ توضيح Append-only دون تغيير المرجع |
| branch drift during validation | exact-head race | pin tested SHA وإعادة validation بعد آخر commit |
| test aliases/fixtures confusion | تضخيم الاختبارات أو provenance | canonical test registry وfixture source taxonomy |

---

## 9. السجلات والملفات المستهدفة

تُنشأ أو تُحدّث تدريجيًا حسب المرحلة، ولا يُنشأ ملف فارغ لمجرد وجوده في قائمة:

- `MASTER_EXECUTION_PLAN_REV3.md` — هذه الخطة.
- `PROJECT_MASTER_STATUS.md` — لقطة الحالة المحدثة ومؤشر المراحل.
- `PROJECT_REQUIREMENTS_TRACEABILITY.json` — requirement/test/output linkage.
- `PROJECT_EVIDENCE_INDEX.json` — URL/commit/blob/Raw SHA/size/Run/Artifact mapping.
- `PROJECT_GATE_LEDGER.json` — gate status by scope/identity/checkpoint.
- `PROJECT_IDENTITY_REGISTRY.json` — separate S6/C100/Stage12-13/Replay identities.
- `PROJECT_ARTIFACT_REGISTRY.json` — artifact IDs, digest, size, retention, members.
- `PROJECT_DECISION_REGISTER.json` — owner decisions and required approvals.
- `PROJECT_EXCEPTION_LEDGER.json` — conflicts, missing evidence, NOT_RUN, blockers.
- `PROJECT_RISK_REGISTER.md` — risks, impact, mitigations, stop rules.
- `PROJECT_FINAL_HANDOFF.md` — verified state and next authorized step.

يُفضّل إبقاء السجلات المعيارية machine-readable وربطها بملفات Markdown التفسيرية. كل ملف يُنشأ فقط عندما توجد بيانات حقيقية قابلة للتوثيق.

---

## 10. بروتوكول Artifact / Evidence

لكل ملف أو Artifact يُستشهد به:
- canonical path/URL.
- containing commit SHA.
- Git blob SHA-1.
- Raw SHA-256 محسوبة من بايتات GitHub Raw.
- exact byte size.
- Run ID / Job ID / tested SHA.
- Artifact ID / GitHub digest / downloaded digest / expiry.
- manifest and member inventory where applicable.
- classification: `VERIFIED_LIVE`, `VERIFIED_LOCAL`, `REPORTED_ONLY`, `MISSING_EVIDENCE`, `CONFLICTED`, `NOT_RUN`, `BLOCKED`, `PASS_SCOPED`.
- precise scope/limitations.

لا يُستخدم `VERIFIED_LIVE` إن غاب أحد عناصر ثلاثية (URL، Raw SHA-256، containing commit). لا تُحوّل البيانات المصرح بها أو المسجلة في تقرير إلى تحقق جديد دون إعادة قراءة البايتات.

---

## 11. تعريف الإغلاق لكل مرحلة

كل مرحلة E3–E6 تتطلب بحسب نطاقها:
1. requirement/acceptance matrix.
2. changes/tests with exact tested SHA.
3. results report and evidence ledger.
4. continuity/status/handoff update.
5. remote readback of all committed outputs.
6. SHA-256, Git blob SHA-1, size, containing commit.
7. exact final HEAD validation.
8. explicit open issues and owner approvals required.
9. no promotion beyond evidence scope.

عند فشل أي شرط: المرحلة `BLOCKED` أو `PASS_SCOPED` حسب الدليل، لا PASS مطلق ولا انتقال تلقائي.

---

## 12. ترتيب العمل العملي

1. Baseline refresh وartifact-retention review.
2. E2 disposition register update يميز Old-identity Replay الناجح عن New-lineage Preflight المنتظر، دون إعادة فتح/تشغيل E2.
3. إكمال E3 readiness matrix وتأكيد أن E2 disposition المسجل يسمح ببدء E3.
4. تنفيذ E3 فقط بعد استيفاء مدخلاته وبوابة الدخول.
5. E4 بعد إغلاق E3؛ تسوية Gate B scope conflict قبل أي نتيجة إحصائية جديدة.
6. E5 بعد E4؛ independent audit فقط.
7. E6 بعد E5؛ release eligibility فقط.
8. أي New S6/C100 lineage يبقى مسارًا منفصلًا مشروطًا بقرار المالك النهائي؛ لا يُدرج كعمل متزامن أو مفترض.
9. في كل نقطة توقف، حدّث master status وcontinuity/handoff وسجل الاستثناءات Append-only.

---

## 13. قرار التنفيذ لهذه النسخة

- REV3 أُعدت بموافقة المالك على إنشاء وثيقة الخطة فقط.
- لا تمنح REV3 إذنًا بتنفيذ E3–E6 تلقائيًا أو تشغيل أي Trial/Simulation/Monte Carlo/Golden revalidation/N expansion.
- لا تمنح REV3 إذنًا لتغيير المصدر أو cohort أو seed أو reference أو thresholds أو business rules.
- لا تمنح REV3 إذنًا لتعديل main أو الدمج أو Release أو إعلان قبول نهائي.
- الخطوة التالية المسموح بها بعد اعتماد هذه الوثيقة: مراجعة E2/E3 entry criteria وتحديث سجل الحالة/الأدلة فقط، ثم التوقف عند أي قرار مالك مطلوب.

**الخلاصة:** الخطة تضبط التنفيذ ولا توسّع الصلاحيات. لا ادعاء بلا دليل، لا انتقال بلا بوابة، ولا تغيير بلا قرار مالك.


---

## REV4 Operational Prompt Library Notice — 2026-11-05 (Append-only)

The current operational prompt library is [PROJECT_PROMPT_LIBRARY_AR_2026-11-05_REV4.md](../stage_d/PROJECT_PROMPT_LIBRARY_AR_2026-11-05_REV4.md) (relative link may be adjusted by the containing document). REV4 supersedes earlier prompt libraries for phase ordering, zero-gap exit gates, D3 scenario packaging, permanent-retention gate, and E3–E6 lock conditions. REV3/REV2 remain preserved as historical records only.

REV4 does not retroactively promote any phase. D0–D6 remain PASS_SCOPED_WITH_LIMITATIONS; E0/E1/E2 remain PASS_SCOPED within their documented scope; old-identity E2 replay is PASS_SCOPED_REPLAY_RECONSTRUCTION only. Five historical accounting fields remain MISSING_EVIDENCE; Production Gate A remains NOT_DECLARED; Gate B N=2400 remains FAIL_SCOPED (10/10); Stability remains NOT_CONVERGED (0/60); N=4800 remains NOT_EXECUTED. E3–E6 remain NOT_STARTED.

Global Preservation Gate remains BLOCKED / PERMANENT_RETENTION_NOT_COMPLETE. The 29 Actions artifacts were unexpired in the 2026-11-05 API check, but temporary availability is not permanent retention; six earlier temporary downloads do not prove phone storage or an independent archive. No new Trials, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity/reference/business-rule/threshold change, historical Artifact/manifest mutation, main write, merge, force-push, Release, or final acceptance declaration was performed.
