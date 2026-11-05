# مكتبة البرومبتات التشغيلية الشاملة — Motorcycle Simulation
## REV5 | دمج الإصدارات الأربعة، بوابات الإغلاق الصارم، تقسيم السيناريوهات، وحفظ الأدلة | 2026-11-05

**الحالة:** إصدار تشغيلي جديد مقترح للاستخدام على فرع العمل بعد المراجعة. يحفظ REV1/REV2/REV3/REV4 دون حذف أو إعادة كتابة، ويجمع أفضل ما فيها ويحل تعارضاتها وفق سجل التسوية أدناه.  
**Repository:** `yasmin977209-ux/motorcycle-simulation`  
**Working branch:** `tmp/d1-rebuild-20261101`  
**Branch HEAD عند بدء هذا التحديث:** `a4d120bb65360dfa1fbeb8e4600b1fc773411bdf`  
**main HEAD عند بدء هذا التحديث:** `01a6f79eedc522bb734ed9c5ea31beee581f2468`  
**Branch comparison:** diverged؛ ahead 957 / behind 2؛ merge base `c6e54349a5e94f65d5aa9f83141f225d777bb474`.  
**Governing reference:** v2.4.0 — `D-2026-10-30-REFERENCE-V2.4.0` — `APPROVED_BY_OWNER`.

> هذه المكتبة تضبط التنفيذ والتدقيق ولا تنشئ قواعد أعمال ولا تمنح صلاحيات محمية. GitHub الحي هو مصدر الحقيقة التشغيلية. لا يتحول غياب الدليل إلى نجاح بإعادة صياغة البرومبت، ولا يتحول النجاح النطاقي إلى إغلاق كامل.

---

# 0. الغرض ونموذج التشغيل

## 0.1 الهدف التشغيلي

يستطيع المالك إرسال اسم مرحلة واحد فقط مثل `D0` أو `E2`. وعلى الوكيل أن ينفذ تلقائياً كل ما يقع ضمن صلاحياته لهذه المرحلة: استعادة الحالة الحية، قراءة الملفات والأدلة، بناء مصفوفة المتطلبات، كشف العيوب، إصلاح العيوب التقنية المسموح بها، تشغيل الاختبارات المصرح بها، التحقق من النتائج، توثيقها، ثم التوقف عند بوابة المرحلة.

لا يطلب الوكيل من المالك إعادة إرسال ملف أو معلومة موجودة في GitHub أو في الملفات المتاحة فعلياً. لا يسأل عن تفضيلات شكلية يمكن حسمها من المرجع أو المكتبة. يسأل فقط عند قرار مالك محمي أو إجراء مادي لا يستطيع تنفيذه، ويحدد السؤال/القرار المطلوب بدقة.

## 0.2 قاعدة اسم المرحلة فقط

عند وصول رسالة تحتوي اسماً معتمداً واحداً من `D0..D6` أو `E0..E6`:
1. نفّذ Bootstrap حيّاً في الجلسة نفسها، ثم نفّذ المرحلة المطلوبة فقط.
2. لا تعتبر الرسالة إذناً لتجاوز بوابات المراحل السابقة؛ تحقق من إغلاقها أولاً.
3. إذا كانت مرحلة سابقة غير مغلقة، عالج المانع الذي يمنع المرحلة المطلوبة فقط إذا كان الإصلاح ضمن الصلاحيات؛ وإلا أوقف وبيّن اسم المرحلة المالكة للمانع.
4. لا تنتقل تلقائياً إلى المرحلة التالية بعد الإغلاق. انتظر رسالة المالك التالية.
5. إذا كان الاسم غير واضح أو يطابق أكثر من مرحلة، اسأل سؤالاً واحداً قصيراً.
6. كلمة `تحقق` وحدها تعني Bootstrap + تقرير حالة فقط، ولا تعني بدء أي مرحلة.

**حد واقعي لا يجوز إخفاؤه:** لا يمكن للوكيل حفظ ملف داخل هاتف المالك أو تأكيد نسخة على وسيط غير متصل لا يستطيع الوصول إليه. كما لا يمكنه اتخاذ قرارات المالك المحمية نيابة عنه. لذلك لا تعد المكتبة بتنفيذ هذه الأفعال دون تدخل؛ بل تمنع إعلان اكتمال البوابة حتى تتوفر وسيلة مصرح بها أو يصدر القرار المطلوب.

## 0.3 المبدأ الحاكم: لا انتقال مع فجوة

الإغلاق الكامل للمرحلة يعني اجتماع كل ما يلي:
- جميع المتطلبات الإلزامية محددة ومغطاة في مصفوفة قابلة للتتبع.
- لكل متطلب مصدر أصلي وهوية واضحة ودليل حي واختبار مناسب ونتيجة قابلة لإعادة الفحص.
- كل اختبار إلزامي نُفذ فعلياً على المدخل والهوية والـcommit الصحيحين ونجح.
- لا يوجد متطلب إلزامي بحالة `NOT_RUN` أو `MISSING_EVIDENCE` أو `NOT_VERIFIED` أو `CONFLICTED` أو `REPORTED_ONLY` أو `BLOCKED`.
- لا توجد فروق غير مفسرة في الأعداد أو البصمات أو القيم أو lineage أو manifests أو مخرجات المصنفات والتقارير والحزم.
- جميع العيوب ذات الصلة أُصلحت، وأعيدت الاختبارات المتأثرة، وأثبتت إعادة الفحص زوال السبب الجذري.
- تم حفظ كل Artifact إلزامي في نسختين دائمتين مستقلتين، وأعيدت قراءة النسختين واختبار استعادتهما.
- تم Raw readback للوثائق بعد Commit، وحساب SHA-256 من bytes، وتسجيل Git blob SHA-1 والحجم وCommit الحاوي.
- تم التحقق من `exact final HEAD`، ولم تُنسب نتائج Run إلى SHA مختلف.
- لا يوجد قرار مالك مطلوب لم يُحسم.

إذا تعذر أي شرط إلزامي، فالحالة `BLOCKED` وليست `PASS`. لا تُخفّض العتبة، ولا تحذف المتطلب، ولا تستبدل الدليل المفقود بنتيجة replay أو قيمة مستنتجة.

## 0.4 فصل أنواع الإغلاق

| المصطلح | معناه | هل يسمح بالانتقال؟ |
|---|---|---|
| `PASS_SCOPED` | نجاح في نطاق محدد ومعلن | لا |
| `PASS_SCOPED_WITH_LIMITATIONS` | نجاح محدود مع قيود معلنة | لا |
| `PASS_SCOPED_REPLAY_RECONSTRUCTION` | نجاح إعادة بناء لهوية تاريخية محددة | لا يثبت الدليل الأصلي |
| `PASS_GAP_FREE` | جميع شروط المرحلة الإلزامية مثبتة بلا فجوة | نعم، بعد التحقق من البوابة |
| `BLOCKED` | مانع أو دليل/قرار/اختبار ناقص | لا |
| `NOT_RUN` | لم يُنفذ | لا |
| `NOT_DECLARED` | لا يوجد إعلان/قبول رسمي | لا |

لا تستخدم `PASS` المجردة. نجاح Workflow أو Artifact Acceptance أو عدد اختبارات جزئي لا يثبت وحده `PASS_GAP_FREE`.

---

# 1. السلطة والصلاحيات والثوابت

## 1.1 ترتيب السلطة

1. تعليمات المنصة والصلاحيات الفعلية.
2. قرار المالك الصريح وحدوده المكتوبة.
3. المرجع الحاكم v2.4.0 وفق `D-2026-10-30-REFERENCE-V2.4.0` بحالة `APPROVED_BY_OWNER`.
4. أدلة GitHub الحية ذات الـSHA والـcommit المثبتين.
5. مصفوفات المتطلبات وسجلات التصحيح والقرارات Append-only.
6. هذه المكتبة REV5.
7. REV1/REV2/REV3/REV4 والملفات القديمة كسجلات تاريخية فقط، إلا حيث يُشار إلى مطلب فني فريد ما زال سارياً ولا يتعارض مع سلطة أعلى.

افصل دائماً بين:
- `current_governing_reference_sha256`: مرجع v2.4.0 المعتمد.
- `historical_execution_reference_sha256`: مرجع v2.3 التاريخي.

رأس المرجع v2.4.0 الذي يصفه `PROPOSED` معروف التعارض مع قرار المالك `APPROVED_BY_OWNER`. قرار المالك هو الحاكم. لا تعدل بايتات المرجع أو قواعد الأعمال لتسوية التعارض دون قرار مالك.

## 1.2 مسموح دون موافقة جديدة

- قراءة GitHub وفحص الفروع والـcommits والـPRs والـActions والـArtifacts والـReleases.
- إنشاء فرع عمل من HEAD موثق إذا لزم.
- تعديل الكود والاختبارات والوثائق لإصلاح عيب تقني مثبت لا يغير business rules أو المرجع أو الهوية أو العتبات.
- تحديث مكتبة البرومبتات وسجلات الاستمرارية Append-only.
- إنشاء Commits ورفعها إلى فرع العمل.
- تشغيل الاختبارات وWorkflows المصرح بها التي لا تطلق Trials/Simulation/Monte Carlo أو تغير هوية التجربة.
- إنشاء Draft PR للمراجعة بعد اجتياز بوابات التغيير.

## 1.3 يتطلب قرار مالك منفصلاً

- تغيير المرجع أو قواعد الأعمال أو العتبات أو طرق الاستدلال.
- تغيير `SOURCE_SHA` أو `cohort_id` أو `MASTER_SEED` أو Trial identity.
- تشغيل Trials جديدة أو Simulation أو Monte Carlo أو Golden revalidation أو توسيع N، بما في ذلك N=4800، إلا ضمن تفويض مالك صريح ومحدد الهوية والنطاق.
- backfill أو تخمين أو zero-fill لبيانات محاسبية تاريخية مفقودة.
- تعديل/حذف Artifact أو manifest تاريخي.
- تعديل `main` أو الدمج إليه أو force-push أو حذف تاريخ Git.
- نشر Release أو إعلان `FINAL_ACCEPTED` أو `P17_FINAL_ACCEPTED` أو `P18_RELEASED` أو `CONVERGED`.
- أي تغيير يجعل Replay Reconstruction بديلاً عن Original Historical Evidence.

اسم المرحلة وحده لا يمنح أي صلاحية من هذه الصلاحيات.

## 1.4 ثوابت لا يجوز ترقيتها بلا دليل وقرار

- Financial Gate A: `PASS_SCOPED` فقط.
- Production Gate A: `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`.
- Gate B عند N=2400: `FAIL_SCOPED (10/10)`.
- Stability: `NOT_CONVERGED (0/60)`.
- N=4800: `NOT_EXECUTED`.
- Full Logging: 105 مفاتيح تمثيلية فقط، وليس 48K Full Logging.
- Normalized manifest: 105 حالات `NOT_VERIFIED` حيث لا يوجد expected byte size مستقل.
- C100 Golden revalidation: `NOT_RUN` ما لم يظهر تشغيل حي صحيح الهوية.
- Full 177-unique-test suite: `NOT_RUN` ما لم يظهر Run موثق.
- Potential_Coverage_Cells=604 حساب محتمل فقط؛ لا يساوي Required_Output_Coverage_Cells.
- لا تخلط 125 role assignments مع 105 unique keys.
- الحقول الخمسة التالية تبقى `MISSING_EVIDENCE` حتى يظهر الدليل الأصلي المطابق للهوية، ولا تخمن أو تصفر أو تستنتج:
  - `Accounts_Receivable`
  - `Accumulated_Depreciation`
  - `Gross_Bike_Assets`
  - `Guarantee_Claim_Receivable`
  - `Total_Assets`
- افصل S6 وC100 وStage 12/13 في كل الملفات والجداول والاختبارات والـmanifests.

---

# 2. سجل دمج الإصدارات الأربعة وتسوية التعارضات

تمت قراءة النسخ الحية الأربع على فرع العمل:
1. REV1: `docs/stage_d/PROJECT_PROMPT_LIBRARY_AR_2026-11-01.md`.
2. REV2: `docs/stage_d/PROJECT_PROMPT_LIBRARY_AR_2026-11-01_REV2.md`.
3. REV3: `docs/stage_d/PROJECT_PROMPT_LIBRARY_AR_2026-11-05_REV3.md`.
4. REV4: `docs/stage_d/PROJECT_PROMPT_LIBRARY_AR_2026-11-05_REV4.md`.

## 2.1 ما تم الاحتفاظ به

| النسخة | أفضل ما فيها وتم دمجه |
|---|---|
| REV1 | تعليمات المشروع الأساسية، ترتيب مراحل D/E، prompts تفصيلية لكل مرحلة، فصل الصلاحيات والهوية، نماذج التقارير. |
| REV2 | تصحيح السلطة، exact SHA/commit، شروط D3 والدليل، تفصيل اختبارات Registry والـDOCX والحزم، البرومبتات الفرعية. |
| REV3 | استعادة الحالة الحية، أولويات الاحتفاظ، ترتيب Artifact expiry، تقسيم ملفات Excel حسب C، فصل E3 readiness عن execution، E2 identity split. |
| REV4 | تعريف zero-gap، Hard Stop، Global Preservation Gate، D3 split sub-gate، قيود E3–E6، التمييز بين scoped closure وfinal acceptance. |

## 2.2 التعارضات التي حُسمت

| التعارض | الحكم الموحد في REV5 |
|---|---|
| لقطات الحالة الثابتة داخل النسخ القديمة | تاريخية فقط؛ GitHub HEAD الحي يعاد استخراجه كل جلسة. |
| D2 أو E0–E2 موصوفة NOT_STARTED في نسخ أقدم | لا تعتمد الحالة التاريخية؛ اقرأ أحدث stage evidence على الفرع الحي. |
| D0–D6/E0–E2 مغلقة scoped مقابل طلب صفر فجوات | تبقى scoped تاريخياً؛ لا ترقى إلى gap-free حتى استيفاء جميع المتطلبات الإلزامية. |
| تقسيم Excel عمل موازٍ أم مرحلة | أصبح `D3-S` بوابة فرعية إلزامية داخل D3؛ لا ينشئ مرحلة رئيسية جديدة ولا يغير ترتيب D/E. |
| عدد أوراق المصنف مقابل 25 سيناريو | لا يُفترض أن هناك 25 ورقة فقط؛ كل ورقة من المصدر يجب تصنيفها كسيناريو أو shared/supporting مع سبب. |
| تقسيم XLSX كحل لحد 100MB | الملفان الأصليان نحو 27.7MB لكل منهما، أي دون 100MB؛ التقسيم لتنظيم التسليم وسهولة التعامل، ولا يحل انتهاء Actions Artifacts. |
| Replay مقابل Original Evidence | Replay Reconstruction منفصل تماماً ولا يعوض الدليل التاريخي الأصلي. |
| الهاتف/التخزين الدائم | لا يُدعى الحفظ دون وصول فعلي أو تأكيد المالك وإثبات البصمة؛ الهاتف وحده ليس نسختين مستقلتين. |
| نجاح Workflow مقابل صحة المنتج | لا يكفي؛ يلزم exact tested SHA وArtifact readback وفحص المحتوى والـlineage والـfinal HEAD. |
| طلب المرحلة التالية مقابل تجاوز البوابة | اسم المرحلة يطلبها فقط؛ لا يتجاوز المتطلبات السابقة ولا القرارات المحمية. |

## 2.3 مبدأ عدم حذف التاريخ

لا تحذف REV1–REV4 ولا تعِد كتابة محتواها التاريخي. REV5 ملف مستقل. كل تصحيح لحالة سابقة يضاف في سجل جديد مع رابط المصدر والتاريخ والـcommit.

---

# 3. Bootstrap إلزامي في بداية كل جلسة

## 3.1 GitHub live state

قبل أي تعديل أو تشغيل:
1. استخرج HEAD الفعلي للفرع `tmp/d1-rebuild-20261101` و`main` من GitHub API.
2. تحقق من وجود الفرع، default branch، الصلاحيات، visibility وحالة المستودع.
3. قارن الفرعين وسجل status/ahead/behind/merge-base.
4. اقرأ آخر 20 Commit ذي صلة، وحدد أي Commit أحدث من handoff السابق.
5. افحص كل Branch ذي صلة وPRs المفتوحة والمغلقة وDrafts وReleases.
6. افحص Actions workflows/runs/jobs/logs/artifacts على الـSHAs ذات الصلة.
7. افحص exact current HEAD status؛ لا تنسب نتائج Run قديم إلى HEAD جديد.
8. لا تكتب على `main` ولا تدمج ولا force-push.

## 3.2 قراءة الملفات الحاكمة

اقرأ من فرع العمل أولاً، ثم `main` للمقارنة عند الحاجة:
- REV5 ثم REV4 ونسخ المكتبة التاريخية عند الحاجة للتحقق من provenance.
- `docs/PROJECT_CONTINUITY.md`.
- أحدث Session Status وContinuity Handoff.
- `MASTER_EXECUTION_PLAN` وسجل القرارات.
- قرار اعتماد v2.4.0 والمرجع الحاكم وبايتاته.
- مصفوفات D0–D6 وسجلات الاختبارات والأدلة.
- E0/E1/E2 continuity وgap disposition وowner decisions.
- Retention inventory وسجلات محاولات النشر والتصحيح.
- `state.json` و`docs/STATE_SHA_SEMANTICS.md` عند تأثيرها على قرار التنفيذ.

لا تفترض أسماء المسارات. إذا فشل مسار، ابحث في Git tree؛ فشل القراءة لا يثبت غياب الملف.

## 3.3 فحص Artifacts

- أعد الاستعلام عن Artifact IDs من Actions API؛ لا تعتمد على inventory قديم.
- سجل Run ID وJob ID وtested SHA وArtifact ID/name/size/digest/expiry/expired.
- رتب حسب أقرب expiry، ثم الحجم والأهمية، ولا تؤخر الملفات الكبيرة المهددة.
- نزّل exact Artifact ID. احسب SHA-256 من ZIP bytes الفعلية وقارن digest، ثم افحص CRC وpaths وduplicate entries وmanifest/member hashes وsource identity.
- لا تعتبر metadata digest إعادة hashing مستقلة.
- لا تخلط source run مع acceptance run أو publication commit.
- إذا كان Workflow متوقعاً أن يستغرق 10 دقائق أو أكثر: شغله، أبلغ Run ID وCommit SHA، ثم توقف ولا تنتظر اكتماله.

## 3.4 تقرير Bootstrap

أخرج جدولاً يميز:
`VERIFIED_LIVE`, `VERIFIED_LOCAL`, `REPORTED_ONLY`, `MISSING_EVIDENCE`, `CONFLICTED`, `NOT_RUN`, `BLOCKED`, `PASS_SCOPED`, `PASS_GAP_FREE`.

اذكر:
- branch HEAD وmain HEAD وcomparison.
- أحدث Commit وPR/Actions/Release.
- آخر حالة لكل مرحلة مع رابط الدليل.
- أقرب Artifact expiry وملفات >100 MiB.
- المتطلبات/القرارات التي تمنع المرحلة المطلوبة.
- هل المرحلة المطلوبة مؤهلة للبدء أم يجب معالجة مانع سابق.

لا تبدأ أي مرحلة إذا لم يرسل المالك اسمها.

---

# 4. سياسة الإثبات والملفات

## 4.1 ملف نصي في GitHub

لا تستخدم `VERIFIED_LIVE` إلا عند وجود الثلاثية:
1. رابط GitHub Raw دقيق للمسار والـCommit.
2. SHA-256 محسوبة من bytes المسترجعة فعلياً.
3. Commit SHA يحتوي تلك البايتات.

سجل أيضاً Git blob SHA-1 والحجم بالبايت. عند غياب أي عنصر استخدم `REPORTED_ONLY` أو `MISSING_EVIDENCE` بحسب الحالة.

## 4.2 Artifact ثنائي

يلزم:
- Run/Job ID وtested SHA.
- Artifact ID واسم الملف والحجم وGitHub digest وexpiry.
- رابط exact download.
- SHA-256 محسوبة من ZIP bytes المنزلة.
- CRC وZIP safety وmember inventory وmanifest/hash verification.
- identity/lineage وsource commit.
- نسختان دائمتان مستقلتان، بصمة لكل نسخة بعد إعادة القراءة، وrestore test.

لا تستخدم Artifact name وحده لتحديد الملف. لا تستبدل Artifact تاريخياً بآخر أحدث لمجرد تشابه الاسم.

## 4.3 الحالات

- `VERIFIED_LIVE`: الثلاثية مكتملة للملف.
- `VERIFIED_LOCAL`: فحص محلي موثق، دون ادعاء remote provenance.
- `REPORTED_ONLY`: معلومة في سجل لم يعاد التحقق منها.
- `MISSING_EVIDENCE`: الدليل اللازم غير موجود أو لم يصل.
- `CONFLICTED`: أدلة أو هويات متعارضة لم تُحسم.
- `NOT_RUN`: الاختبار أو الإجراء لم ينفذ.
- `BLOCKED`: شرط يمنع المتابعة.
- `PASS_SCOPED`: نجاح محدود لا يفتح البوابة.
- `PASS_GAP_FREE`: نجاح جميع المتطلبات الإلزامية بعد exact-head validation.

---

# 5. الاحتفاظ ومنع فقدان الملفات

## 5.1 Global Preservation Gate

تعمل بوابة الاحتفاظ قبل E3، لكن حماية الأدلة تبدأ من أول جلسة ولا تنتظر نهاية D6.

لا تعتبر البوابة PASS إلا عند:
1. فحص كل Artifact ID من Actions API.
2. تنزيل كل Artifact إلزامي من ID الدقيق.
3. حساب SHA-256 من ZIP bytes ومطابقتها مع GitHub digest.
4. فحص ZIP وmembers وsource identity وmanifest.
5. حفظ نسختين دائمتيْن في failure domains مستقلين ومصرح بهما.
6. إعادة قراءة النسختين وحساب SHA-256 لكل منهما.
7. نجاح restore test.
8. retention manifest يربط Run/Job/tested SHA/Artifact ID/expiry/locations/hashes.
9. لا Artifact إلزامي مفقود أو منتهي أو غير محفوظ.
10. توثيق نسخة الهاتف فقط بعد تأكيد المالك؛ لا تدّعِ وصولاً مباشراً للهاتف.

إذا لم توجد وجهة تخزين دائمة متصلة ومصرح بها، تبقى البوابة `BLOCKED / PERMANENT_RETENTION_NOT_COMPLETE`. لا تستخدم Release أو خدمة خارجية أو Box دون اتصال أو صلاحية مالك.

## 5.2 أولوية >100 MiB

في كل جلسة أعد ترتيب Artifacts حسب expiry الفعلي، ولا تعتمد الترتيب الثابت القديم. أولوية الإنقاذ:
1. Artifact كبير وقريب الانتهاء.
2. مصدر D0 aggregate والأدلة الأصلية التي لا يمكن إعادة إنتاجها.
3. D3 workbook package وD5 package.
4. D1 Full Logging وE2 scenario outputs.
5. أدلة D6 وD0-D4 الصغيرة.

في لقطة الجرد المؤرخة 2026-11-05 كان هناك 29 Artifact، و23 منها أكبر من 100 MiB، بمجموع تقريبي 4.865 GiB. كان أقرب expiry المسجل 2026-11-27 للـD0 aggregate. هذه لقطة مرجعية فقط؛ أعد فحص metadata كل مرة.

الملفان الأصليان:
- `deliverables/Full_Results_EN.xlsx`: 27,722,355 bytes.
- `deliverables/النتائج_الكاملة_AR.xlsx`: 27,734,273 bytes.

كلاهما أقل من 100MB؛ لا تصف تقسيمهما بأنه حل لحد GitHub للملف الواحد أو لاحتفاظ Actions. Artifacts الحزم الكبيرة مسألة منفصلة.

## 5.3 الهاتف والنسخ الدائمة

- أعط المالك رابط تنزيل حديثاً من Artifact ID الحي مع الحجم والبصمة وحالة التحقق.
- لا تستخدم signed URL قديمة.
- لا تدّعِ أن الملف نُقل إلى الهاتف.
- لا تعد الهاتف وحده نسختين مستقلتين.
- إذا أكد المالك حفظ نسخة هاتف، سجّلها `OWNER_REPORTED_PHONE_COPY` إلى أن يمكن مطابقة bytes/hash.
- يجب توفير نسخة ثانية مستقلة وrestore test قبل إغلاق Preservation Gate.
- لا ترفع ZIPs ضخمة إلى Git history لمجرد الاحتفاظ بها.
- لا تنشر GitHub Release دون قرار مالك صريح.

---

# 6. التسلسل المرحلي الرسمي

**Bootstrap → Preservation Review (عابر) → D0 → D1 → D2 → D3 (ويشمل D3-S) → D4 → D5 → D6 → E0 → E1 → E2 → Global Preservation Gate → E3 → E4 → E5 → E6.**

- D3-S بوابة فرعية إلزامية ضمن D3 وليست مرحلة رئيسية إضافية.
- لا تُنفذ E3 قبل إغلاق D0–D6 وE0–E2 gap-free واجتياز Global Preservation Gate.
- لا تبدأ E4 قبل E3 gap-free؛ ولا E5 قبل E4؛ ولا E6 قبل E5.
- لا تبدأ أكثر من مرحلة رئيسية واحدة في طلب واحد.
- إذا اكتشفت مرحلة لاحقة عيباً في مرحلة سابقة، أعد فتح البوابة المتأثرة بدليل وتصحيح append-only، ثم أعد الاختبارات التابعة.
- لا تعِد Trials أو Simulation لمجرد بدء دردشة جديدة؛ أعد التحقق من الأدلة أولاً.
- لا تواصل تلقائياً بعد إغلاق المرحلة؛ انتظر اسم المرحلة التالي.

---

# 7. عقد موحد لتنفيذ أي مرحلة

عند استلام اسم مرحلة:
1. Bootstrap حي.
2. تحقق من أن جميع المراحل السابقة اجتازت بواباتها؛ وإلا أوقف.
3. اقرأ المرجع والملفات الحاكمة ذات الصلة.
4. أنشئ/حدّث Requirements Matrix قبل التعديل.
5. اربط كل requirement بمصدر ومالك ودليل واختبار ومخرج.
6. نفذ العمل التقني المصرح به فقط.
7. سجل كل عيب: ID، severity، root cause، affected files/data, remediation, test, commit.
8. أعد الاختبارات المرتبطة بكل إصلاح.
9. افحص source identity وlineage وnumeric integrity وartifact outputs.
10. نفذ independent review لا يعتمد على تقرير المنفذ وحده.
11. حدّث Evidence Ledger وRetention Manifest وClosure Report.
12. Commit على فرع العمل فقط.
13. اقرأ الملفات من GitHub Raw بعد Commit واحسب SHA-256 وblob SHA-1 والحجم.
14. تحقق من exact final HEAD وActions status.
15. صنف النتيجة `PASS_GAP_FREE` أو `BLOCKED`؛ لا تستخدم scoped PASS كإغلاق.
16. توقف. لا تبدأ المرحلة التالية تلقائياً.

---

# 8. متطلبات الإغلاق المشتركة لكل مرحلة

يجب أن تنتج كل مرحلة، بحسب نطاقها:
- Requirements & Traceability Matrix.
- Inputs/Identity Matrix.
- Test/Run/Job Matrix.
- Defect & Root-Cause Register.
- Remediation & Regression Evidence.
- Evidence Ledger.
- Artifact/Retention Manifest.
- Closure Report.
- Continuity & Handoff update.
- Remote readback/hash/exact-head proof.

لكل requirement سجل:
`requirement_id`, description, normative source/clause, source file/path, source SHA-256, source blob SHA-1, size, commit, tested SHA, run/job/test ID, output/artifact ID, result, limitation, owner decision, status.

لا تسمح بصف واحد بلا evidence pointer أو status واضح. لا تملأ الحقول المفقودة بقيم صفرية أو افتراضية.

---

# 9. البرومبتات الرئيسية — مرتبة حسب التنفيذ

## PROMPT 00 — Bootstrap

«ابدأ من GitHub الحي للمستودع yasmin977209-ux/motorcycle-simulation. استخرج branch HEAD وmain HEAD عبر API، وقارن ahead/behind/merge-base. اقرأ REV5 والمرجع v2.4.0 وقرار D-2026-10-30 وPROJECT_CONTINUITY وSession Status وHandoff وMASTER_EXECUTION_PLAN ومصفوفات المراحل وE0/E1/E2 continuity وRetention Inventory. افحص branches/PRs/Actions runs/jobs/artifacts/expiry/releases. أعد التحقق من exact IDs والـSHAs. لا تعدّل ولا تشغل Trial/Simulation/Monte Carlo. أخرج live-state matrix يميز VERIFIED_LIVE وREPORTED_ONLY وMISSING_EVIDENCE وCONFLICTED وNOT_RUN وBLOCKED وPASS_SCOPED، وحدد المرحلة المؤهلة والمانع التالي وأقرب expiry. لا تبدأ مرحلة دون اسمها من المالك.»

## PROMPT 01 — Preservation Review

«نفذ Preservation Review فقط. أعد الاستعلام عن كل Artifact ID في Actions API، وحدّث run/job/tested SHA/size/digest/expiry. رتب حسب expiry والحجم والأهمية. نزّل exact IDs، احسب SHA-256 من ZIP bytes، وافحص ZIP/CRC/path traversal/duplicate members/manifest/member hashes/source identity. أنشئ retention manifest append-only. تحقق من وجود وجهتي حفظ مستقلتين مصرح بهما، وأعد قراءة النسختين واختبر restore. لا تنشر Release ولا تدّعِ حفظ الهاتف. إذا لم تتوفر وجهة دائمة أو قرار مطلوب، BLOCKED.»

## PROMPT D0 — Input Integrity & Provenance

«نفذ D0 فقط. تحقق من source identities وSOURCE_SHA/cohort/seed/Trial identity دون تغييرها، وRun/Job/Artifact IDs وSHA-256 والحجم والـblob/commit. افحص ZIP safety وParquet metadata/schema/row counts/columns/nulls/duplicates/partitions وsource_run_metadata. تحقق من اكتمال السجلات الأصلية لكل 48K Trial ولكل السيناريوهات المطلوبة. افصل 125 role assignments عن 105 unique keys. افحص S6 وC100 كلّاً على حدة، ولا تستخدم Stage 12/13 لسد نقص S6. لا تستنتج الحقول المحاسبية الخمسة. أخرج مصفوفة لكل متطلب. أي missing source, schema, row count, identity أو original ledger يبقي D0 BLOCKED.»

## PROMPT D1 — Independent Builder & Governing Reference

«نفذ D1 فقط. اقرأ قرار D-2026-10-30 والمرجع v2.4.0 من Raw bytes، وتحقق من current_governing_reference_sha256 منفصلاً عن historical_execution_reference_sha256 لـv2.3. افحص التعارض النصي PROPOSED مقابل APPROVED_BY_OWNER دون تعديل المرجع. افحص builder/importer ومصدره وإصداره وdependencies. أعد بناء مستقلاً من inputs المثبتة، واختبر reproducibility وdeterminism وerror handling وschema/contract. افحص كل normalized manifest key. لا تخمن expected byte sizes؛ كل حالة دون دليل مستقل تبقى NOT_VERIFIED وتمنع gap-free. 105 Full Logging keys لا تعني 48K logging. لا تغلق D1 مع requirement غير محسوم.»

## PROMPT D2 — Number Registry & Numeric Lineage

«نفذ D2 فقط. تحقق من Registry الفعلي وsource commit والـmanifest. أعد التحقق من الأعداد المتوقعة تاريخياً (2,640 entries و1,000 daily series و2,086,550 daily points) ولا تفترضها إن تغير المصدر. اختبر uniqueness وreferential integrity وscenario/cohort/source identity وmissing/duplicate keys وdate coverage وnumeric precision/overflow/null semantics. اربط كل قيمة مالية بـnumber_id/source/Trial/Date/Scenario. اختبر resolver على كل النقاط وليس عينة فقط. Registry لا يعوض 48K detailed ledgers أو Parquet/SQLite الأصلي. لا تستخدم C100 أو Stage 12/13 لسد S6.»

## PROMPT D3 — Full Excel Delivery

«نفذ D3 فقط. اقرأ bytes المصنفين الأصليين من GitHub/Artifact exact source. تحقق من source identity وSHA-256 والـblob/commit والـmanifest. افحص جميع الأوراق وترتيبها وhidden states وformulas/cached values/errors/named ranges/merged cells/hyperlinks/RTL-LTR/number formats/financial values/print settings/external links/protection. تحقق من السيناريوهات الـ25: C030/C050/C070/C085/C100 × G000/G030/G050/G070/G100، ومن كل required output. نفذ D3-18 requirement invocation فعلياً؛ لا تساوِ artifact-level acceptance مع test invocation. لا تغلق D3 قبل D3-S وجميع فحوص التكافؤ.»

## PROMPT D3-S — Scenario Partitioning (بوابة فرعية إلزامية داخل D3)

«نفذ D3-S فقط بعد تثبيت مصدر المصنفين الأصليين. أنشئ عشرة مشتقات: خمسة EN وخمسة AR. كل ملف يمثل قيمة C واحدة ويحتوي مستويات G الخمسة الخاصة بها. تحقق من sheet mapping من bytes الفعلية والـmanifest؛ لا تفترض 25 ورقة فقط، إذ قد توجد 185 ورقة تشمل أوراق دعم/ملخص/تعريف. لا تبتكر mapping. صنف كل ورقة مصدر إلى scenario أو shared/supporting أو excluded with justified reason. إذا كانت ورقة مشتركة مكررة في الأجزاء، أثبت canonical identity. لا تعدل المصدرين الأصليين. أنشئ manifest لكل لغة يتضمن source URL/commit/blob/size/SHA-256، sheet names/order، scenario IDs، shared sheets، part paths/sizes/SHA-256، tool/library versions وmerge procedure. افتح كل جزء وافحص البيانات والأنواع والقيم المالية والتنسيقات والعناوين والروابط والـhidden states. نفذ coverage assertion: كل واحد من 25 scenario موجود مرة واحدة بالضبط ضمن part C الصحيح؛ لا فقد ولا duplicate. أعد تجميعاً تجريبياً في مسار منفصل وقارن canonical sheet hashes وworkbook structure والقيم والأنواع والصيغ والأنماط والروابط. التكافؤ المطلوب semantic/content equivalence؛ لا تدّعِ byte-identical ZIP بعد إعادة الحفظ. إذا فشل أي invariant أو تعذر mapping، BLOCKED ولا تمس الأصل. التقسيم لا يضمن خفض مجموع bytes ولا يعالج Artifact expiry.»

### مصفوفة D3-S الملزمة

| Part | سيناريوهات G الخمسة |
|---|---|
| C030 | C030_G000, C030_G030, C030_G050, C030_G070, C030_G100 |
| C050 | C050_G000, C050_G030, C050_G050, C050_G070, C050_G100 |
| C070 | C070_G000, C070_G030, C070_G050, C070_G070, C070_G100 |
| C085 | C085_G000, C085_G030, C085_G050, C085_G070, C085_G100 |
| C100 | C100_G000, C100_G030, C100_G050, C100_G070, C100_G100 |

الناتج: `Full_Results_EN_C030.xlsx` ... `Full_Results_EN_C100.xlsx` وخمسة أسماء مقابلة للعربية، مع manifest منفصل لكل لغة. الأسماء النهائية تُثبت في manifest ولا تُكتب فوق المصدر.

## PROMPT D4 — DOCX & Numeric Provenance

«نفذ D4 فقط بعد D3 وD3-S gap-free. تحقق من كل DOCX عربي/إنجليزي والملخصات ودراسة الجدوى وفق قائمة المخرجات المعتمدة. افحص OOXML، RTL/LTR، الخطوط، الصفحات، الجداول، العناوين، الروابط، الإفصاحات، الأرقام، تواريخها، الوحدات، التقريب، والربط إلى Registry/manifest. نفذ Test 176 وكل اختبارات D4 الإلزامية. اربط كل numeric token بمصدره أو صنفه صراحةً كغير مالي/معادلة/نص. لا تساوِ 112 explicit Registry IDs مع lineage لكل رقم. لا تدّعِ مراجعة بصرية لكل صفحة دون rendered page inspection فعلي.»

## PROMPT D5 — Package, Manifest & Reproducibility

«نفذ D5 فقط بعد D4 gap-free. ابنِ الحزمة من المخرجات المعتمدة المثبتة دون تعديل originals. افحص manifest وSHA256SUMS وكل member path/size/hash وZIP CRC وduplicate/path traversal/encoding. أثبت وجود ومطابقة جميع المخرجات المطلوبة. افصل tested SHA عن publication-evidence commit. شغل Full 177-unique-test suite إذا كانت إلزامية ومصرحاً بها؛ لا تصف focused tests بأنها full suite. تحقق من exact Artifact ID/bytes/digest/expiry بعد النشر، ثم نزّل exact ID وأعد الفحص. لا تعتبر Actions Artifact احتفاظاً دائماً.»

## PROMPT D6 — Independent Post-write Audit

«نفذ D6 فقط باستقلال عن Builder/Publisher. نزّل exact published Artifact ID، وأعد فحص كل عضو وبصمة وبيانات workbook/DOCX/Registry lineage/manifest. شغل جميع الاختبارات الإلزامية فعلياً، بما فيها 176/179/180/181/183، وسجل 175/182/186 كمنفذة فقط عند استدعائها فعلياً. افحص كل required output cell، وكل scenario وnumeric lineage. لا تساوِ scoped check مع historical test invocation. لا تعتمد على تقرير D5 وحده. أي mismatch أو missing output أو NOT_RUN إلزامي يمنع الإغلاق. D6 ليس P17/P18 ولا قبولاً نهائياً.»

## PROMPT E0 — Full Gap Inventory & Traceability

«نفذ E0 فقط بعد D6 gap-free. طابق المرجع v2.4.0 بنداً بنداً وكل clauses والـ28 required outputs والبيانات والاختبارات والمخرجات. لا تعتمد على قائمة 15 gap القديمة؛ أعد discovery من الملفات والكود والبيانات والـActions. أنشئ traceability requirement→normative clause→source→code→test→output→artifact→SHA/commit→retention. صنف gaps حسب أثرها على النتيجة النهائية والدقة والاكتمال. أدرج gaps الجديدة وغير المعروفة. E0 جرد فقط؛ لا يحذف أو يخفي gap ولا يمنح موافقة ولا يعلن قبولاً.»

## PROMPT E1 — Conflict Reconciliation & Owner Decisions

«نفذ E1 فقط بعد E0. راجع كل تعارض بين reference/owner decision/code/test/manifest/artifact/report/status/lineage. احتفظ بالتاريخ وأضف correction append-only. أنشئ decision register: decision ID, issue, evidence, options, impact, affected identities/references, cost/risk, required authority, explicit approval and scope. لا تعتبر الصمت أو طلب تحديث المكتبة موافقة. لا تعدل المرجع أو business rules أو thresholds أو identities أو artifacts التاريخية. إذا بقي قرار مالك مطلوب، E1 BLOCKED ولا تتجاوزه.»

## PROMPT E2 — Accounting Evidence, Original Ledgers & Replay Separation

«نفذ E2 فقط بعد E1. ابحث عن original identity-matching records للحقول الخمسة والدفاتر اليومية لكل 48K Trial. افحص producer code path وserialization schema وParquet bytes وmanifest وsource/cohort/seed. افصل S6 وC100 وStage 12/13. لا تستخدم proxy أو inferred value أو zero-fill أو backfill.

افصل صراحةً:
1. Original historical evidence.
2. Read-only forensic audit.
3. Old-identity replay reconstruction.
4. New S6/C100 proposal.

Run 41958935113 هو old-identity replay reconstruction فقط: 20×2,400=48,000 Trial identities و98,323,918 replay daily rows. لا يحول replay إلى original historical evidence ولا يغلق الحقول الخمسة. Production Gate A يبقى NOT_DECLARED ما لم يظهر دليل أصلي مطابق.

السلالة الجديدة S6/C100 candidate لا تبدأ دون قرار مالك نهائي يحدد source/cohort/seed/scope. موافقة Option A الخاصة بالهوية القديمة لا تتوسع تلقائياً.

أخرج E2 gap disposition. إذا بقيت الحقول الخمسة أو أدلة all-48K accounting الأصلية مفقودة، E2 BLOCKED ولا يبدأ E3.»

## PROMPT E3 — Acceptance Tests & Fixtures

«لا تبدأ E3 إلا بعد D0–D6 وE0–E2 gap-free وGlobal Preservation Gate PASS، مع جميع قرارات المالك محسومة. اقرأ acceptance criteria/fixtures/tests من v2.4.0. اربط كل requirement بالاختبار والمدخل والنتيجة والـartifact والهوية. افحص fixture completeness/version/identity and negative cases. نفذ الاختبارات المصرح بها فقط؛ لا تغير identities ولا تشغل Trials جديدة تلقائياً. أي Test NOT_RUN أو fixture/source mismatch أو failed assertion يوقف E3. لا تنتقل إلى E4 دون exact-head evidence.»

## PROMPT E4 — Financial & Statistical Reconciliation

«لا تبدأ E4 قبل E3 gap-free. أعد تدقيق Gate A/Gate B/Stability من بيانات identity-matching كاملة ومستقلة. احفظ النتائج السابقة كما هي: Gate B N=2400 FAIL_SCOPED (10/10)، Stability NOT_CONVERGED (0/60)، N=4800 NOT_EXECUTED. لا تشغل N=4800 أو Monte Carlo أو Trials جديدة دون قرار مالك صريح يحدد scope/identity/seed/cost/stop conditions. لا تستخدم scaling أو سيناريو آخر أو replay بديلاً عن المصدر. افحص الحسابات والـprecision والـconfidence intervals والـmultiplicity والـstopping criteria حسب المرجع فقط. أي نقص بيانات يبقي E4 BLOCKED.»

## PROMPT E5 — Independent P17 Acceptance

«لا تبدأ E5 قبل E4 gap-free. نفذ مراجعة مستقلة لا تعتمد على Builder evidence وحده. أعد فحص كل requirement/output/disclosure/manifest/hash/lineage/retention واختبارات القبول. افحص جميع required output cells والـ28 outputs وكل القيم المالية. وثق reviewer independence وreproducibility. لا تعلن P17_FINAL_ACCEPTED إلا بعد جميع المعايير وقرار المالك المطلوب. أي conflict أو missing evidence أو NOT_RUN يمنع القبول.»

## PROMPT E6 — P18 Release Eligibility & Final Decision Package

«لا تبدأ E6 قبل E5 gap-free. تحقق من release eligibility والاحتفاظ الدائم وإعادة الإنتاج واتساق source/identity/manifest/versions والوثائق والمخاطر والقيود. أعد تقرير قرار نهائي مع كل الأدلة والروابط والبصمات والـcommits. جهّز توصية إصدار فقط. لا تنشر Release ولا تعدل main ولا تدمج ولا تعلن P18_RELEASED أو FINAL_ACCEPTED أو CONVERGED دون قرار مالك صريح منفصل. إغلاق D6 أو E6 readiness لا يساوي القبول النهائي.»

---

# 10. بوابة كل مرحلة — تعريف دخول وخروج

| المرحلة | شرط الدخول | الحد الأدنى للخروج قبل Gap-free |
|---|---|---|
| D0 | المصدر والهوية معرّفان | صحة المدخلات الأصلية والـschema والصفوف والهوية والـcoverage والـhash |
| D1 | D0 gap-free | Builder مستقل، reference verified، manifest مكتمل، reproducibility واختبارات |
| D2 | D1 gap-free | Registry كامل، uniqueness/referential integrity، كل daily points وnumeric lineage |
| D3 | D2 gap-free | المصنفان الأصليان مفحوصان، 25 scenario cells، D3-S، D3-18 وكل invariants |
| D3-S | D3 source workbook verified | عشرة أجزاء، mapping كامل، 25/25 scenarios، manifests، semantic merge equivalence |
| D4 | D3/D3-S gap-free | كل DOCX والـnumeric lineage والـRTL/LTR والاختبارات الإلزامية |
| D5 | D4 gap-free | package/manifest/SHA256SUMS، كل الأعضاء، full required tests، exact artifact readback |
| D6 | D5 gap-free | independent audit، جميع outputs والاختبارات والـlineage والـretention |
| E0 | D6 gap-free | كل requirements/gaps موثقة وtraceable |
| E1 | E0 gap-free | كل conflicts حُسمت وكل owner decisions موثقة؛ لا قرار معلق |
| E2 | E1 gap-free | original accounting evidence والدفاتر والهوية كاملة؛ replay منفصل |
| E3 | D0–D6 + E0–E2 gap-free وPreservation PASS | كل acceptance tests/fixtures تنفذ وتنجح |
| E4 | E3 gap-free | financial/statistical reconciliation كامل وفق المرجع وبصلاحيات مالك |
| E5 | E4 gap-free | independent P17 review وكل outputs/tests pass |
| E6 | E5 gap-free | release eligibility/reproducibility/retention وقرار المالك النهائي |

أي شرط لا ينطبق يجب إثبات عدم انطباقه بمصدر موثق؛ لا يُترك فارغاً.

---

# 11. البرومبتات الفرعية الإلزامية

## A. BLOCKED Root-Cause Handler

«حدد requirement الذي يمنع الإغلاق، ومرحلة ملكيته، والسبب الجذري، والدليل الذي ينقص، وأصغر إصلاح مسموح. لا تعالج أعراضاً خارج المانع. لا تنتقل لمرحلة لاحقة. نفذ الإصلاح التقني إن كان مصرحاً، ثم أعد الاختبارات المتأثرة والـreadback. إذا احتاج قرار مالك أو بيانات أصلية مفقودة، جهز طلب قرار واحداً محدداً وتوقف.»

## B. Artifact Expiry Rescue

«أعد فحص expiry عبر Actions API الآن. نزّل exact Artifact IDs الأقرب انتهاءً، خصوصاً >100 MiB. تحقق من bytes/hash/CRC/member manifest. جهز روابط حديثة للمالك واحتفاظاً دائماً فقط في وجهة مصرح بها. لا ترفع binary history ولا تنشر Release دون قرار. أبلغ عن أي artifact لم يُحفظ قبل expiry.»

## C. Source/Identity Validation

«تحقق من SOURCE_SHA/cohort_id/MASTER_SEED/Trial identity من المصدر الأصلي والـmanifest والـrun. قارنها بكل artifact والـdaily rows. أي اختلاف يعني CONFLICTED/BLOCKED. لا تصلح الاختلاف بإعادة تسمية أو نسخ قيم من سلالة أخرى.»

## D. Numeric/Accounting Lineage

«تتبع كل قيمة من التقرير إلى Registry إلى daily ledger إلى Trial/Date/Scenario إلى المصدر الأصلي. تحقق من precision/rounding/units/sign/null semantics. الحقول الخمسة المفقودة تظل missing ولا تملأ. لا تعتمد على رقم نهائي دون lineage.»

## E. XLSX Partition & Reassembly

«نفذ D3-S وفق هذا المستند. احفظ originals byte-exact. سجل sheet-level canonical hashes. تحقق من كل السيناريوهات الخمسة والعشرين ومن عدم فقد أو تكرار أو تغيير أي قيمة. افحص ملفات الأجزاء ثم reassemble في مسار منفصل. إذا تعذر إثبات التكافؤ الدلالي، BLOCKED.»

## F. Independent Review

«أعد الفحص من الصفر باستخدام المصدر والـArtifact IDs، لا تنسخ تقرير التنفيذ. أعد حساب الأعداد والبصمات، ونفذ الاختبارات المستقلة، وسجل اختلافاتك. إذا لم تكن مستقلاً عن builder، صرّح بذلك ولا تسم المراجعة independent.»

## G. Session Close & Handoff

«حدّث REV5 عند الحاجة بملف revision لاحق أو correction append-only؛ لا تعدل REV1–REV4. حدّث PROJECT_CONTINUITY وSession Status وContinuity Handoff وstage evidence ذات الصلة. سجل before/after HEAD، commits، tests، artifacts، expiry، defects، owner decisions. أعد Raw readback لكل ملف جديد واحسب SHA-256 وblob SHA-1 والحجم والـcommit. تحقق من exact final HEAD. إذا تعذرت الكتابة أو hashing أو readback، صرّح بذلك وقدّم handoff دون ادعاء.»

---

# 12. تقرير نهاية المرحلة — قالب إلزامي

كل تقرير نهاية مرحلة يتضمن:
1. اسم المرحلة ونتيجتها: `PASS_GAP_FREE` أو `BLOCKED`، مع سبب دقيق.
2. branch HEAD وmain HEAD وahead/behind/merge-base.
3. مصفوفة المتطلبات: ID/clause/source/evidence/hash/blob/size/commit/test/result/status.
4. defect/root-cause/remediation matrix.
5. Actions Run/Job/tested SHA/conclusion.
6. Artifact IDs/digests/sizes/expiry/download verification/permanent retention.
7. numeric/source identity/lineage checks.
8. raw readback والـfinal HEAD.
9. قرارات المالك المطلوبة وحدودها.
10. ما أصلح، وما بقي، وسبب BLOCKED إن وجد.
11. `READY_FOR_NEXT_STAGE` فقط إذا اجتازت كل بوابة؛ وإلا `BLOCKED`.
12. لا تذكر المرحلة التالية باعتبارها قابلة للبدء إذا بقي أي شرط إلزامي ناقص.

---

# 13. سياسة الاختبارات وGitHub Actions

- لا تشغل Workflow قبل قراءة ملفه وفهم triggers/permissions/inputs/cost/side effects.
- لا تستخدم Workflow تجريبياً على production identity.
- لا تشغل أكثر من run متعارض على نفس artifact/identity.
- اختبر على branch commit موثق.
- سجل `head_sha` الفعلي وtested SHA؛ إذا اختلفا، وضح علاقة البناء والـartifact.
- لا تعتبر check suite خضراء دليلاً على اكتمال outputs أو correctness.
- افحص jobs وsteps وlogs وartifacts لكل Run ذي صلة.
- Workflow طويل 10 دقائق أو أكثر: trigger ثم اذكر Run ID وCommit SHA وتوقف دون انتظار.
- بعد كل Commit جديد، أعد فحص exact final HEAD؛ نتائج SHA السابق لا تغطيه.
- إذا كان اختبار محمي يتطلب Trial/Simulation/Monte Carlo، توقف واطلب قرار مالك محدداً.

---

# 14. خطة الترتيب العملي حسب الأولوية

1. استعادة الحالة الحية ومراجعة صلاحية الملفات والأدلة.
2. إنقاذ Artifacts المهددة بالانتهاء حسب expiry الفعلي والحجم.
3. إثبات الاحتفاظ الدائم والنسختين المستقلتين.
4. تنفيذ D0 ثم D1 ثم D2 ثم D3/D3-S ثم D4 ثم D5 ثم D6.
5. تنفيذ E0 ثم E1 ثم E2.
6. إعادة تقييم Global Preservation Gate.
7. تنفيذ E3 ثم E4 ثم E5 ثم E6 بعد قرار المالك عند اللزوم.
8. لا يتم الإعلان عن اكتمال المشروع إلا بعد قرار المالك النهائي ومتطلبات المرجع.

هذه الخطة لا تضمن أن المراحل ستنجح؛ بل تضمن ألا تُعلن ناجحة إذا لم تنجح.

---

# 15. حالة المشروع المرجعية عند إعداد REV5

هذه بيانات استمرارية من REV4 وسجلاتها، وليست بديلاً عن التحقق الحي في الجلسة التالية:
- D0–D6: `PASS_SCOPED_WITH_LIMITATIONS` تاريخياً، مع القيود الموضحة في REV4.
- E0/E1/E2: `PASS_SCOPED` ضمن نطاقاتها؛ لا تعني gap-free.
- Old-identity E2 replay: `PASS_SCOPED_REPLAY_RECONSTRUCTION` فقط.
- Five historical accounting fields: `MISSING_EVIDENCE`.
- Production Gate A: `NOT_DECLARED`.
- Gate B N=2400: `FAIL_SCOPED (10/10)`.
- Stability: `NOT_CONVERGED (0/60)`.
- N=4800: `NOT_EXECUTED`.
- Full Logging: 105 representative keys فقط.
- E3–E6: `NOT_STARTED` في آخر سجل REV4.
- Global Preservation Gate: `BLOCKED / PERMANENT_RETENTION_NOT_COMPLETE`.
- `FINAL_ACCEPTED`, `P17_FINAL_ACCEPTED`, `P18_RELEASED`, `CONVERGED`: `NOT_DECLARED`.

لا تنقل هذه الحالات إلى تقرير حي دون إعادة فحص GitHub.

---

# 16. سجل REV5

- دمج REV1 وREV2 وREV3 وREV4 بعد قراءة النسخ الأربع الحية.
- الحفاظ على أفضل تفاصيل prompts المراحل والهوية والاختبارات والـlineage والاحتفاظ.
- توحيد جميع حالات الإغلاق على Hard Stop يمنع انتقال أي مرحلة مع gap إلزامي.
- اعتماد `D3-S` كـsub-gate إلزامية داخل D3 لتقسيم المصنفين إلى 10 مشتقات مع 25 سيناريو و5 مستويات G.
- تصحيح الخلط بين تقسيم Excel وحد 100MB واحتفاظ Actions Artifacts.
- إضافة عقد تشغيل "اسم المرحلة فقط" مع الحفاظ على قرارات المالك المحمية.
- عدم تغيير المرجع v2.4.0 أو business rules أو source identities أو أي Artifact تاريخي.
- REV1–REV4 تبقى محفوظة تاريخياً ولا تحذف.

**المعيار النهائي:** لا ادعاء بلا دليل، لا فجوة إلزامية عند الإغلاق، لا انتقال بلا بوابة، لا تغيير بلا صلاحية، ولا فقدان للأدلة قبل انتهاء صلاحيتها.
