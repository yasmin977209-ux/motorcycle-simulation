# مكتبة البرومبتات التشغيلية الشاملة — Motorcycle Simulation
## REV6 | إعادة تأسيس تشغيلية شاملة فوق REV1–REV5 | 2026-11-05

**الحالة:** REV6 operational candidate — supersedes REV5 operational clauses; owner-final approval is not implied. يحفظ REV1/REV2/REV3/REV4 دون حذف أو إعادة كتابة، ويجمع أفضل ما فيها ويحل تعارضاتها وفق سجل التسوية أدناه.  
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


---

# 17. REV6 — المواصفة التشغيلية الحاكمة والمحدّثة بالكامل

**تاريخ المراجعة:** 2026-11-05  
**الإصدار:** REV6  
**الأساس:** REV1 + REV2 + REV3 + REV4 + REV5 بعد قراءة النسخ الحية من GitHub.  
**نطاق هذا الإصدار:** تحديث حوكمة التنفيذ، ترتيب البرومبتات، بوابات المراحل، التغطية والاختبارات، إدارة العيوب، التقسيم، الاحتفاظ، الاستعادة، والتوثيق.  
**لا يغيّر:** المرجع v2.4.0، قواعد الأعمال، المعادلات، العتبات، SOURCE_SHA، cohort_id، MASTER_SEED، Trial identity، أو أي Artifact/manifest تاريخي.

## 17.1 السلطة التشغيلية لهذه النسخة

1. REV6 هي النسخة التشغيلية الأحدث للمكتبة عند وجودها على فرع العمل، بعد التحقق من Commit وRaw bytes.
2. تبقى REV1–REV5 محفوظة كما هي لأغراض التاريخ والتدقيق، ولا تحذف أو يعاد تحريرها.
3. كل ما سبق في نص REV5 المضمّن هنا يبقى مادة مصدرية وتاريخية؛ وعند التعارض التشغيلي تسود أحكام REV6 الواردة في الأقسام 17–27.
4. المرجع الحاكم v2.4.0 وقرار المالك أعلى سلطة من هذه المكتبة. لا تستطيع REV6 تعديل المرجع أو توسيع تفويض المالك.
5. لا يُعلن أن REV6 اعتماد مالك نهائي لمجرد إنشائها أو نشرها. حالتها OPERATIONAL_CANDIDATE_PENDING_OWNER_REVIEW إلى أن يصدر قرار مستقل إذا طلب المالك ذلك. ويجوز استخدامها لضبط أعمال التوثيق والتدقيق المصرح بها دون اعتبارها تفويضاً لأعمال محمية.

## 17.2 تعريف الإغلاق الدقيق وحدود اليقين

PASS_GAP_FREE يعني: اجتياز جميع المتطلبات الإلزامية المعروفة والمحددة في المرجع الحاكم، مصفوفة المتطلبات، موافقات المالك، عقود البيانات، ومعايير الاختبار المعتمدة للمرحلة، مع أدلة قابلة لإعادة الفحص على exact source/identity/commit/artifact.

لا يعني هذا المصطلح إثبات استحالة وجود أي خطأ مجهول مطلقاً. لذلك يجب:
- تحديد حدود النظام والبيانات والفترة والسيناريوهات والمخرجات صراحة.
- إجراء completeness discovery مستقلة، وليس الاكتفاء بالقائمة المعروفة.
- إضافة الاختبارات السلبية وحالات الحدود والتكرار والفقد والتلف وعدم الاتساق.
- تسجيل أي افتراض أو قيد أو مصدر غير متاح؛ لا يُخفى في صياغة التقرير.
- عدم تحويل غياب الدليل إلى نجاح أو افتراض أن عدم اكتشاف الخطأ يساوي صحة مطلقة.

أي مطلب إلزامي غير قابل للتحقق يجعل المرحلة BLOCKED، حتى لو كانت بقية الاختبارات خضراء.

## 17.3 عقد «اسم المرحلة فقط» — سلوك الوكيل

عندما يرسل المالك اسماً واحداً مثل D3:
1. ينفذ الوكيل Bootstrap حياً في GitHub في نفس الجلسة.
2. يحدد كل المراحل السابقة غير المغلقة PASS_GAP_FREE.
3. يعالج المتطلبات المعلقة في المراحل السابقة بالترتيب، وبالقدر الذي تسمح به صلاحياته، قبل بدء المرحلة المطلوبة.
4. لا ينفذ أعمال المرحلة المطلوبة قبل إغلاق كل أسلافها. إذا كان إكمال سلف يتطلب قرار مالك أو مصدراً أصلياً غير متاح، يتوقف عند ذلك المانع ولا يتجاوزه.
5. بعد استكمال الأسلاف، ينفذ المرحلة التي طلبها المالك فقط، ولا يبدأ المرحلة التالية تلقائياً.
6. لا تعني رسالة اسم المرحلة إذناً بتشغيل Trial أو Simulation أو Monte Carlo أو تغيير الهوية أو العتبات أو المرجع أو إجراء backfill أو Release أو Merge.
7. إذا احتاج التنفيذ موافقة محمية، يقدم طلب قرار محدداً يتضمن الخيارات والأثر والتكلفة والمخاطر والهوية الدقيقة، ثم ينتظر القرار.
8. إذا كانت المرحلة المطلوبة مغلقة مسبقاً، يعيد التحقق من أدلة إغلاقها؛ لا يعيد بناءها أو تشغيلها لمجرد تكرار الرسالة إلا عند وجود عيب أو دليل متغير.
9. لا يسأل المالك عن معلومة متاحة بالفعل في GitHub أو في ملفات المشروع المقروءة.
10. لا يطلب من المالك تنفيذ إجراءات تقنية يمكن للوكيل تنفيذها. يستثنى ما يتطلب وصولاً مادياً إلى الهاتف أو وسيط غير متصل أو حساباً/وجهة غير متصلة.

## 17.4 نموذج الحالات الموحد

الحالات الوحيدة المعتمدة:
- VERIFIED_LIVE
- VERIFIED_LOCAL
- REPORTED_ONLY
- MISSING_EVIDENCE
- CONFLICTED
- NOT_RUN
- BLOCKED
- PASS_SCOPED
- PASS_SCOPED_WITH_LIMITATIONS
- PASS_SCOPED_REPLAY_RECONSTRUCTION
- PASS_GAP_FREE

لا تستخدم PASS أو DONE أو COMPLETE أو ACCEPTED منفردة لتقرير حالة مرحلة. لا تُسند PASS_GAP_FREE إلى ملف أو اختبار أو Artifact؛ هي حكم بوابة مرحلة كامل، بينما الملفات تصنف وفق سياسة الإثبات.

## 17.5 بوابة ما قبل التنفيذ — Bootstrap & Safety Gate

قبل أي كتابة أو تشغيل:
- تحقق من المستودع والفرع وHEAD الحالي وmain HEAD عبر GitHub API.
- قارن الفرعين وسجل ahead/behind/merge-base.
- اقرأ مكتبة البرومبتات الحية الأحدث من فرع العمل، ثم قرار المالك والمرجع الحاكم.
- اقرأ الاستمرارية والحالة والـhandoff وسجلات المرحلة السابقة وسجل الأدلة.
- افحص PRs وcommits وworkflows/runs/jobs/steps/logs/artifacts/expiry/releases ذات الصلة.
- افحص صلاحيات GitHub الفعلية، ولا تفترض صلاحية من وجود اتصال.
- افحص workflow YAML قبل تشغيله: triggers، inputs، permissions، secrets، concurrency، side effects، retention، والعمليات التي قد تطلق محاكاة أو تغير الهوية.
- تحقق من نظافة/تعارض الفرع ومن أن التغيير سيبقى على فرع العمل.
- أنشئ Snapshot للـHEAD والملفات والبصمات قبل التغيير.
- إذا تعذر إثبات نقطة العمل أو المرجع أو الصلاحية: BLOCKED قبل التعديل.

## 17.6 مصفوفة التغطية الإلزامية

يجب إنشاء Requirement Traceability Matrix مستقلة لكل مرحلة، وتحتوي لكل بند:
REQ_ID | normative_clause | acceptance_criterion | source_identity | input_path | input_sha256 | input_blob_sha1 | input_size | input_commit | code_path | test_id | test_command | tested_sha | run_id | job_id | output_path | artifact_id | output_sha256 | retention_locations | reviewer | result | status | defect_id | owner_decision_id.

قواعد المصفوفة:
- لا صف بلا REQ_ID ثابت وفريد.
- لا صف إلزامي بلا معيار قبول قابل للاختبار.
- لا تستخدم روابط عامة أو أسماء ملفات بدلاً من روابط exact paths/IDs.
- لا تعتبر التغطية كاملة إلا بعد reconciliation بين عدد المتطلبات في المرجع والمصفوفة.
- أضف NOT_APPLICABLE فقط مع مبرر ودليل ومراجعة مستقلة، ولا تترك الخانة فارغة.
- افصل requirements عن tests وعن outputs؛ وجود واحد لا يثبت الآخر.
- راجع جميع السيناريوهات الـ25 وكل مخرجات المرجع الـ28 دون استنتاج أو اختزال.

## 17.7 سياسة الاختبارات وإثبات النتيجة

لكل اختبار:
1. سجل الاختبار كما هو معرف في المرجع أو test catalog، مع ID واسم وهدف.
2. سجل الأمر/الـworkflow الفعلي، وإصدارات الأدوات والاعتماديات.
3. سجل المدخلات وبصماتها وهوياتها.
4. سجل exact tested SHA، وRun ID وJob ID ونتيجة كل خطوة.
5. احفظ stdout/stderr أو Logs وملفات النتائج.
6. افحص أن الاختبار نفذ فعلاً؛ لا تساوِ وجود test file أو test name أو workflow success باستدعاء الاختبار.
7. لا تستخدم focused tests بديلاً عن full suite.
8. نفذ negative tests وboundary tests وcorruption tests وduplicate/missing/null/overflow tests حيث تنطبق.
9. أعد الاختبارات المتأثرة بعد كل إصلاح، ثم نفذ regression suite.
10. لا تنسب نجاح اختبار على SHA قديم إلى HEAD أحدث.
11. إذا كانت البيئة أو الـdependency أو البيانات غير متاحة، الحالة NOT_RUN أو BLOCKED، لا PASS.
12. لا تغيّر expected values لمجرد جعل الاختبار ينجح؛ أي تغيير معيار قبول يتطلب مصدر سلطة وقراراً مناسباً.

## 17.8 إدارة العيوب والجذر السببي

لكل عيب:
DEFECT_ID, severity, requirement_ids, detection_method, observed_result, expected_result, root_cause, affected_identities, affected_commits, affected_artifacts, containment, corrective_action, regression_tests, independent_retest, residual_risk, closure_evidence.

تصنيف الأثر:
- CRITICAL: يغير النتيجة المالية/الإحصائية أو الهوية أو اكتمال بيانات أصلية أو قبول المخرجات.
- HIGH: يمنع إعادة الإنتاج أو سلامة الأدلة أو اكتمال مخرج إلزامي.
- MEDIUM: يؤثر على متطلب أو تقرير أو قابلية استخدام دون تغيير النتيجة الأساسية.
- LOW: عيب تحريري/تنسيقي لا يؤثر على البيانات أو المعنى.

لا يغلق العيب بتعديل النص وحده. يجب إثبات root-cause fix واختبار regression مستقل. أي Critical/High مفتوح يمنع إغلاق المرحلة.

## 17.9 قواعد البيانات والمحاسبة والدقة

- لا تُنشئ قيمة محاسبية مفقودة من inference أو proxy أو صفر أو جمع/طرح غير موثق.
- لا تستخدم Replay Reconstruction لإثبات Original Historical Evidence.
- لا تخلط S6 وC100 وStage 12/13 أو cohorts أو seeds أو SOURCE_SHA.
- افحص null semantics وsign conventions والوحدات والعملات والتقريب والدقة الرقمية والتواريخ والمنطقة الزمنية.
- اختبر roll-forward والمعادلات والتوازنات على كامل نطاق البيانات، لا على عينة فقط، إلا إذا كانت العينة منصوصاً عليها وتُسمى كذلك.
- أثبت عدد الصفوف المتوقع والموجود والمفقود والمكرر، ومفتاح uniqueness، وreferential integrity.
- لا تصف قاعدة بيانات بأنها كاملة اعتماداً على summary أو aggregate فقط.

## 17.10 بوابة D3-S الموسعة — التقسيم والتجميع

تُسمى بوابة التقسيم D3-S، وتتكون من عمليتين إلزاميتين:
- D3-S1 / D3-PARTITION: إنتاج خمسة أجزاء لكل لغة حسب C.
- D3-S2 / D3-REASSEMBLY: اختبار إعادة التجميع والتكافؤ من الأجزاء.

المصفوفة الثابتة:

| C-part | السيناريوهات الخمسة التي يجب أن تبقى داخل الجزء |
|---|---|
| C030 | C030_G000, C030_G030, C030_G050, C030_G070, C030_G100 |
| C050 | C050_G000, C050_G030, C050_G050, C050_G070, C050_G100 |
| C070 | C070_G000, C070_G030, C070_G050, C070_G070, C070_G100 |
| C085 | C085_G000, C085_G030, C085_G050, C085_G070, C085_G100 |
| C100 | C100_G000, C100_G030, C100_G050, C100_G070, C100_G100 |

الناتج المتوقع: 10 ملفات مشتقة بالضبط:
- EN: خمسة ملفات، واحد لكل C.
- AR: خمسة ملفات، واحد لكل C.
- يحتوي كل ملف على جميع مستويات G الخمسة التابعة لقيمة C.
- لا يُحذف أي سيناريو من الـ25 ولا يُكرر داخل ملفين على أنه السيناريو الأصلي نفسه.

إجراءات D3-S:
1. تثبيت الملفين الأصليين byte-exact وتسجيل SHA-256/blob/size/commit ومصدرهما.
2. قراءة المصنفين فعلياً بأداة XLSX موثوقة وتسجيل إصدار المكتبة.
3. استخراج كل أسماء الأوراق وترتيبها وحالتها (visible/hidden/veryHidden)، والـtables/named ranges/formulas/links/print areas/merged cells.
4. بناء mapping موثق من scenario ID إلى sheets/ranges/records. لا تفترض أن هناك 25 sheet فقط؛ أوراق الدعم والملخصات قد تكون جزءاً من الـ185 ورقة.
5. تصنيف كل sheet إلى scenario-specific أو shared/supporting أو excluded، مع مبرر لكل استثناء.
6. لا تكرر shared sheets إلا إذا كان ذلك مطلوباً للحفاظ على استقلال الملف؛ إذا كررت، عرّف canonical identity وسجل النسخ.
7. إنتاج خمسة ملفات AR وخمسة EN، بأسماء ثابتة في manifest، ودون overwrite للمصدرين.
8. احسب لكل ملف: bytes، SHA-256، Git blob إن دخل Git، sheet inventory، scenario coverage، عدد القيم/السجلات، ومؤشرات مالية.
9. تحقق من حدود GitHub قبل commit: لا ترفع ملفاً يقترب من حد GitHub hard limit؛ استهدف أقل من 50 MiB لكل ملف مشتق، وأوقف الرفع إلى Git history إذا تجاوز الملف 100 MiB. لا تفترض أن التقسيم سيقلل مجموع الحجم؛ قد تزيد shared sheets الحجم الإجمالي.
10. افتح كل ملف مشتق مستقلاً، وتحقق من جميع scenario IDs وG levels والقيم والأنواع والصيغ والتنسيقات والـhidden states والروابط.
11. أعد التجميع إلى ملفات اختبار منفصلة، وقارن المحتوى البنيوي والدلالي مع الأصل: sheet order، values، types، formulas، styles، names، links، visibility، financial cells، scenario coverage.
12. لا تشترط ZIP byte-identical بعد إعادة الحفظ؛ اشترط semantic equivalence موثقة مع فروق metadata المسموح بها حصراً.
13. نفذ اختبار round-trip مرتين على الأقل ببيئة وأداة مثبتتين للتحقق من determinism.
14. تحقق من كل scenario مرة واحدة بالضبط في الجزء الصحيح، مع توثيق أوراق الدعم المشتركة.
15. أي mapping غير مؤكد أو سيناريو مفقود/مكرر أو قيمة مختلفة أو ملف غير قابل للفتح يجعل D3-S BLOCKED.

تنبيه الحجم والاحتفاظ:
- تقسيم المصنفين إجراء تنظيمي وتقني لمعالجة حدود الملف الواحد وسهولة النقل؛ لا يضمن تخفيض إجمالي التخزين.
- GitHub Git history ليس مخزناً دائماً مناسباً لملفات ثنائية ضخمة متكررة.
- Actions Artifacts مؤقتة ولها expiry؛ لا تعتبرها نسخة دائمة.
- كل جزء مهم يجب أن يكون له manifest وبصمة وموقعان دائمان مستقلان واختبار restore.
- لا تنشر Release أو تستخدم LFS أو خدمة خارجية دون صلاحية/قرار مناسب وسياسة التخزين والتكلفة.
- الهاتف نسخة احتياطية إضافية يحمّلها المالك من روابط تنزيل حديثة؛ لا يدعي الوكيل حفظها مادياً أو فحص الهاتف. سجّلها OWNER_REPORTED_PHONE_COPY إلى أن تُطابق bytes/hash عبر قناة متاحة.

## 17.11 Global Preservation Gate — بوابة مستقلة قبل E3

لا تبدأ E3 حتى تتحقق جميع الشروط:
- inventory حي لجميع Artifacts المطلوبة، لا لقطة قديمة.
- كل Artifact مطلوب exact ID وrun/job/tested SHA وname وsize وdigest وexpiry.
- تنزيل البايتات الفعلية وفحص SHA-256 وZIP CRC وmember paths وduplicate names وpath traversal وmanifest/member hashes.
- وجود نسختين دائمتين مستقلتين في وجهتين مختلفتين ومصرح بهما.
- readback مستقل للنسختين ومطابقة البصمات.
- restore test فعلي على كل نسخة، مع سجل زمن الاستعادة والنتيجة.
- خطة استعادة عند فساد نسخة واحدة.
- توثيق ما حمله المالك إلى الهاتف بوصفه إجراءً خارجياً، دون ادعاء التحقق من الجهاز.
- لا يوجد Artifact إلزامي مفقود أو منتهي أو لا يمكن تنزيله أو غير محفوظ.
- لا يُقبل GitHub Actions retention كنسخة دائمة.

إذا تعذر اتصال وجهة تخزين دائمة، يبقى Gate BLOCKED. لا تُخفّض البوابة لأن انتهاء الصلاحية قريب؛ بل تعطى عملية الإنقاذ أولوية عاجلة مع توثيق أي عنصر تعذر إنقاذه.

## 17.12 إغلاق المرحلة — تسلسل إلزامي

قبل كتابة تقرير الإغلاق:
1. إكمال كل المتطلبات.
2. إصلاح العيوب المفتوحة.
3. تشغيل اختبارات الوحدة والتكامل والقبول والـregression ذات الصلة.
4. مراجعة مستقلة لا تعتمد على تقرير المنفذ وحده؛ إن تعذر الاستقلال، صرّح بذلك.
5. إنشاء closure matrix نهائية.
6. commit على فرع العمل.
7. fetch Raw bytes لكل ملف إثبات جديد وحساب SHA-256.
8. تسجيل Git blob SHA-1 والحجم والرابط والـcommit.
9. التحقق من exact final HEAD بعد آخر commit، لا HEAD سابق.
10. ربط كل Run بالـtested SHA والـArtifact ID.
11. تحديث الاستمرارية والحالة والـhandoff.
12. إخراج تقرير يبين PASS_GAP_FREE أو BLOCKED فقط للمرحلة.

لا تنتقل إلى المرحلة التالية تلقائياً حتى لو كانت جاهزة.

---

# 18. البرومبتات الرئيسية REV6 — الصياغة التنفيذية المعتمدة

> تستخدم هذه البرومبتات عند إرسال اسم المرحلة فقط. على الوكيل تطبيق عقد REV6 كاملاً، ولا يطلب من المالك إعادة كتابة التعليمات.

## PROMPT 00 — LIVE BOOTSTRAP & AUTHORITY

«استعد من GitHub الحي للمستودع yasmin977209-ux/motorcycle-simulation. استخرج HEAD الفعلي للفرع النشط وmain عبر API، وتحقق من refs والـcommit/tree والـahead/behind/merge-base. اقرأ أحدث مكتبة برومبتات وقرار v2.4.0 والمرجع نفسه من Raw bytes، وPROJECT_CONTINUITY وSession Status وHandoff وملفات الحالة والأدلة والقرارات وسجلات المراحل. افحص branches/PRs/commits/workflows/runs/jobs/steps/logs/artifacts/expiry/releases. لا تستخدم أسماء أو SHAs من الذاكرة دون إعادة التحقق. أخرج جدولاً يفصل VERIFIED_LIVE وREPORTED_ONLY وMISSING_EVIDENCE وCONFLICTED وNOT_RUN وBLOCKED وPASS_SCOPED. حدد أسلاف المرحلة المطلوبة وحالة كل بوابة. لا تنفذ المرحلة التالية ولا Trials/Simulation/Monte Carlo ولا أي تغيير محمي أثناء Bootstrap.»

## PROMPT 01 — PRESERVATION & EXPIRY RESCUE

«أعد جرد Artifacts من Actions API الآن. رتب كل عنصر حسب expiry ثم الحجم والأهمية والاعتماد المرحلي. لكل Artifact سجل exact run/job/tested SHA/Artifact ID/name/size/digest/expiry/expired. نزّل البايتات الفعلية للعناصر المهددة، واحسب SHA-256، وافحص ZIP safety وCRC وmembers وmanifest. أعط الأولوية للملفات >100 MiB وقريبة الانتهاء، لكن لا تهمل الملفات الصغيرة التي تمثل المصدر أو manifest. أنشئ retention manifest append-only. تحقق من وجهتي حفظ دائمتين مستقلتين ومصرح بهما، readback، restore test. جهز روابط تنزيل حديثة للمالك ليحفظ الملفات المهمة على هاتفه، وصرّح بأن الفعل المادي على الهاتف مسؤولية المالك ولا تدّعِ إتمامه. لا تنشر Release ولا ترفع إلى خدمة خارجية دون إذن.»

## PROMPT D0 — SOURCE INPUTS, IDENTITY & DATA INTEGRITY

«نفذ D0 بعد Bootstrap. اجرد جميع مصادر D0 الأصلية والمشتقة. ثبّت المصدر والهوية وSOURCE_SHA/cohort_id/MASTER_SEED/Trial identity وRun/Job/Artifact IDs. نزّل exact source bytes. تحقق من SHA-256/blob/size/commit. افحص ZIP/Parquet/SQLite/CSV حسب النوع: CRC، schema، dtypes، row counts، partitions، date ranges، null semantics، duplicates، primary/foreign keys، ordering، compression، truncation، source metadata. طابق كل 48K Trial والسجلات اليومية المطلوبة مع manifests والمجاميع. افصل 125 role assignments عن 105 unique keys. افحص S6 وC100 مستقلاً ولا تستخدم Stage 12/13 لسد نقص. تحقق من كل الحقول المحاسبية الخمسة من مصدر أصلي مطابق فقط. نفذ اختبارات corruption/missing/duplicate/wrong identity/partial partition. أخرج input inventory وidentity matrix وcoverage reconciliation وdefect register. أي نقص أصل/هوية/صفوف/حقل مطلوب/بصمة يجعل D0 BLOCKED.»

## PROMPT D1 — BUILDER, REFERENCE & REPRODUCIBILITY

«نفذ D1 بعد D0 gap-free. تحقق من قرار D-2026-10-30-REFERENCE-V2.4.0 ومن بايتات المرجع v2.4.0، واحسب current_governing_reference_sha256 منفصلة عن historical_execution_reference_sha256 لـv2.3. وثق التعارض PROPOSED/APPROVED_BY_OWNER مع حسم سلطة القرار دون تعديل المرجع. افحص Builder/importer code وdependencies وversion pins وconfiguration. ابنِ من مدخلات D0 المثبتة في مسار نظيف ومعزول. أعد البناء مرتين وقارن المخرجات deterministically. افحص schema transformations، field preservation، units, rounding, nulls, timezone, error paths. طابق كل normalized manifest key والـexpected byte size مع مصدر مستقل. لا تخمن expected sizes. نفذ unit/integration/negative tests وسجل exact tested SHA. أي key غير متحقق أو nondeterminism غير مفسر يمنع D1 gap-free.»

## PROMPT D2 — NUMBER REGISTRY & COMPLETE NUMERIC LINEAGE

«نفذ D2 بعد D1 gap-free. اقرأ Registry وmanifest ومصدر كل entry. أعد حساب entry count/daily series/daily points من المصدر الحي، ولا تفترض الأعداد القديمة. تحقق من uniqueness، completeness، referential integrity، scenario/cohort/source identity، date coverage، missing/duplicate/orphan keys، numeric precision، overflow، null/sign/unit/currency semantics. اختبر resolver على كامل نطاق النقاط، وليس sample فقط. اربط كل قيمة مالية بـnumber_id/source file/source SHA/Trial/Date/Scenario/field/units. طابق registry مقابل ledgers والـoutputs. أثبت أن Registry لا يحل محل daily accounting ledgers ولا Parquet/SQLite الأصلية. لا تخلط S6/C100/Stage 12/13. أي رقم بلا lineage أو أي اختلاف غير مفسر يبقي D2 BLOCKED.»

## PROMPT D3 — EXCEL DELIVERY + D3-S PARTITION/ROUND-TRIP

«نفذ D3 بعد D2 gap-free. ثبت bytes المصنفين الأصليين AR/EN. افحص كل ورقة من الـworkbooks: الاسم والترتيب والظهور، الخلايا والقيم والأنواع والصيغ وcached values والأخطاء والـtables/named ranges/merged cells/hyperlinks/external links/protection/RTL-LTR/number formats/print settings. طابق الـ28 required outputs وجميع السيناريوهات الـ25. نفذ requirement D3-18 فعلياً بالاختبار المحدد، ولا تعتبر artifact acceptance بديلاً عن test invocation.

نفذ D3-S1: أنشئ خمسة أجزاء لكل لغة، جزء لكل C من C030/C050/C070/C085/C100، ويحتوي كل جزء مستويات G000/G030/G050/G070/G100 التابعة له. تحقق من sheet mapping من المصدر الفعلي؛ صنف أوراق الدعم والمشتركة والمستبعدة مع السبب. احفظ الأصلين دون تعديل. أنشئ manifests لكل جزء ولكل لغة مع المصدر والبصمات والـsheet inventory والسيناريوهات والحجم والأداة والإصدار.

نفذ D3-S2: افتح الأجزاء العشرة مستقلاً، تحقق من coverage 25/25 exactly once، لا فقد ولا duplicate، ثم أعد التجميع في ملفات اختبار منفصلة وقارن المحتوى والبنية والقيم والصيغ والأنواع والأنماط والروابط. لا تدّعِ byte-identical ZIP؛ أثبت semantic equivalence. تحقق من حدود GitHub لكل ملف، ولا ترفع ملفاً >100 MiB إلى Git history. افحص كل required output وD3-18 وD3-S. أي mapping أو قيمة أو scenario غير مثبت يجعل D3 BLOCKED.»

## PROMPT D4 — DOCX, REPORT CONTENT & NUMERIC TOKEN LINEAGE

«نفذ D4 بعد D3 gap-free. اجرد كل وثيقة مطلوبة AR/EN والملخصات ودراسة الجدوى. ثبت مصدر كل DOCX وبصمته. افحص OOXML package/relationships/styles/sections/page breaks/fonts/tables/headers/footers/fields/links/embedded objects. تحقق من RTL/LTR واتجاه النص والخطوط والترقيم والتواريخ والعملات والوحدات والتقريب. استخرج كل numeric token من المستند واربطه بالمصدر/Registry/المعادلة أو صنفه نصاً/رقماً تعريفياً/غير مالي. طابق الأرقام بين AR وEN وبين الملخص والتقرير الكامل. Render كل صفحة إلى صورة/PDF وفحصها آلياً وبصرياً؛ لا تدّعِ visual review إن لم يحدث. نفذ Test 176 وكل اختبارات D4 الإلزامية. أي رقم غير متتبع أو اختلاف ترجمة/تنسيق يغير المعنى يمنع الإغلاق.»

## PROMPT D5 — PACKAGE, MANIFEST, HASHES & RETENTION

«نفذ D5 بعد D4 gap-free. ابنِ الحزمة من الملفات المعتمدة فقط وبإصدارات مثبتة. لا تعدل originals. أنشئ manifest شامل يضم كل member path/role/language/scenario/source identity/size/SHA-256/creation tool/version. أنشئ SHA256SUMS. افحص ZIP CRC، duplicate names، path traversal، symlinks، case collisions، Unicode normalization، missing/extra members، size limits. تحقق من جميع المخرجات المطلوبة والـ10 Excel partitions. شغّل Full 177-unique-test suite إذا كانت متطلبات المرجع تتطلبها وبصلاحية التشغيل؛ لا تسم focused tests full suite. سجل exact tested SHA منفصلاً عن publication commit. انشر فقط إلى الوجهة المصرح بها. نزّل exact Artifact ID بعد النشر، وأعد hash/member verification. لا تعتبر Actions Artifact نسخة دائمة. أي mismatch أو expiry risk غير معالج يمنع D5 gap-free.»

## PROMPT D6 — INDEPENDENT POST-WRITE AUDIT

«نفذ D6 باستقلال عن Builder وPublisher وبعد D5 gap-free. لا تعتمد على تقاريرهم أو checksums المنسوخة. نزّل exact Artifact IDs والبايتات المنشورة، واحسب SHA-256 من جديد. افحص كل member وكل workbook/DOCX/Registry/manifest والـ28 outputs والـ25 scenarios والـ10 partitions. أعد اختبارات acceptance المحددة، بما فيها 176/179/180/181/183، ولا تسجل 175/182/186 منفذة إلا باستدعاء حقيقي. افحص كل output cell وnumeric lineage والـsource identity والـretention. قارن results مع المرجع والمصدر. سجل reviewer independence. أي اختلاف أو test NOT_RUN إلزامي أو artifact لا يمكن استعادته يبقي D6 BLOCKED. D6 لا يعلن P17/P18 ولا القبول النهائي.»

## PROMPT E0 — COMPLETE GAP DISCOVERY & REQUIREMENT TRACEABILITY

«نفذ E0 بعد D6 gap-free. أعد اكتشاف المتطلبات من المرجع v2.4.0 وكل ملاحقه والقرارات والكود والـschemas والاختبارات والـworkflows والـoutputs والبيانات، ولا تعتمد على سجل فجوات قديم وحده. أنشئ traceability لكل clause إلى requirement إلى source إلى code إلى test إلى output إلى artifact إلى retention. طابق جميع الـ28 required outputs والـ25 scenarios وكل الأبعاد المالية والإحصائية والتشغيلية. نفذ discovery للـunknown/missing requirements عبر مراجعة مستقلة. صنف الأثر والأولوية والمرحلة المالكة. E0 جرد فقط؛ لا يخفي ولا يصلح ولا يغلق gap بمجرد إعادة تصنيفه.»

## PROMPT E1 — CONFLICT, DECISION & AUTHORITY RECONCILIATION

«نفذ E1 بعد E0. قارن المرجع وقرارات المالك والكود والاختبارات والـmanifests والـartifacts والتقارير والحالة والـlineage. لكل تعارض أنشئ issue record وevidence links وhashes وoptions وimpact/risk/cost وrequired authority. حدد ما يحسمه المرجع أو قرار سابق وما يحتاج قراراً جديداً. حافظ على append-only history وأضف correction record. لا تستخدم أحدث تاريخ وحده لترجيح سلطة أقل. لا تعتبر الصمت أو طلب تحسين المكتبة موافقة. لا تغير rules/thresholds/identity/reference/historical artifacts. أي قرار مالك مطلوب وغير محسوم يبقي E1 BLOCKED.»

## PROMPT E2 — ORIGINAL ACCOUNTING EVIDENCE & REPLAY SEPARATION

«نفذ E2 بعد E1. تتبع مسار البيانات من الحساب داخل المحرك إلى callback ثم serialization ثم daily ledger ثم Parquet/SQLite ثم manifest. حدد موضع فقد الحقول الخمسة وأصلح الكود فقط إذا كان الإصلاح لا يغير قواعد الأعمال أو هوية تجارب تاريخية. ابحث عن Original Evidence المطابق للـidentity؛ افحص الحقول الخمسة والدفاتر اليومية لكل 48K Trial. افصل original historical evidence عن forensic audit وعن old-identity replay وعن new-cohort proposal. لا تستخدم replay أو proxy أو inference أو zero-fill أو backfill لإكمال التاريخ. أي تجربة جديدة أو Golden/Monte Carlo أو N expansion تحتاج قرار مالك محدداً قبل التشغيل. سجل النتائج والهوية والـlineage كاملة. Production Gate A لا يترقى دون الأصل. إذا بقيت فجوة أصلية، E2 BLOCKED ولا يبدأ E3.»

## PROMPT E3 — ACCEPTANCE TESTS, FIXTURES & NEGATIVE COVERAGE

«نفذ E3 فقط بعد D0–D6 وE0–E2 gap-free وGlobal Preservation Gate PASS. استخرج جميع acceptance criteria والـfixtures من المرجع. أنشئ مصفوفة requirement→fixture→test→expected result→actual result→source identity→artifact. افحص fixture completeness والنسخ والتغطية والحدود والحالات السلبية والتلف والبيانات المفقودة والمكررة وعدم الاتساق. نفذ كل الاختبارات المصرح بها على exact SHA. لا تنشئ بيانات اختبار مشتقة على أنها تاريخية. لا تطلق Trials/Simulation/Monte Carlo تلقائياً. أي test أو fixture ناقص أو غير مطابق يبقي E3 BLOCKED.»

## PROMPT E4 — FINANCIAL, STATISTICAL & REPRODUCIBILITY RECONCILIATION

«نفذ E4 بعد E3 gap-free. أعد حساب كل مؤشرات Gate A/Gate B/Stability من البيانات الصحيحة والهوية المطابقة، مع التحقق من sample sizes والـdenominators والـconfidence intervals والـmultiplicity/stopping criteria والـprecision والـrounding. أعد التحقق من الحسابات independently. احتفظ بالنتائج الثابتة: Financial Gate A PASS_SCOPED؛ Production Gate A NOT_DECLARED عند غياب الحقول؛ Gate B N=2400 FAIL_SCOPED (10/10)؛ Stability NOT_CONVERGED (0/60)؛ N=4800 NOT_EXECUTED. لا تشغل N=4800 أو Trials/Monte Carlo أو تغير seed/cohort دون قرار مالك صريح. لا تعلن convergence بالاستقراء أو scaling. أي نقص أو فشل يبقي E4 BLOCKED.»

## PROMPT E5 — INDEPENDENT P17 ACCEPTANCE

«نفذ E5 بعد E4 gap-free. عيّن مسار تدقيق مستقل لا يعتمد على builder أو publisher. أعد قراءة المصادر والـartifacts، وتحقق من كل requirement و28 output و25 scenario والـ10 partitions والـnumeric lineage والـfinancial/statistical results والـdisclosures والـmanifest والـretention. أعد الاختبارات الأساسية وnegative tests. وثق استقلال المراجع وحدود الاستقلال. أخرج قرار P17 evidence-based مع قائمة residual risks. لا تعلن P17_FINAL_ACCEPTED دون تفويض مالك صريح ومعايير المرجع. أي gap أو conflict أو missing evidence يمنع الإغلاق.»

## PROMPT E6 — P18 RELEASE ELIGIBILITY & FINAL DECISION PACKAGE

«نفذ E6 بعد E5 gap-free. تحقق من release eligibility/reproducibility/retention/version consistency/source identity/manifest/docs/known limitations/security/privacy/license and operational readiness. تحقق من وجود نسختين دائمتين واختبار restore. أنشئ final decision package مع كل الأدلة والروابط والبصمات والـcommits والـtested SHAs والـruns والـartifacts والقيود. قدم توصية موثقة فقط. لا تنشر Release ولا تعدل main ولا تدمج ولا تعلن P18_RELEASED أو FINAL_ACCEPTED أو CONVERGED دون قرار مالك مستقل وصريح.»

---

# 19. بوابات الدخول والخروج الرسمية لكل مرحلة

| المرحلة | شرط الدخول | شروط الخروج الإلزامية |
|---|---|---|
| D0 | Bootstrap ومرجع/مصادر محددة | source identity + byte hashes + schemas + complete row/partition coverage + no unexplained null/duplicate/missing |
| D1 | D0 PASS_GAP_FREE | reference verified + builder reproducible + manifest complete + all required tests |
| D2 | D1 PASS_GAP_FREE | full registry integrity + all-point resolver + complete numeric lineage |
| D3 | D2 PASS_GAP_FREE | original AR/EN workbook audits + 28 outputs + 25 scenarios + D3-18 + D3-S1/S2 |
| D4 | D3 PASS_GAP_FREE | all DOCX outputs + all numeric tokens traced + rendered-page QA + required tests |
| D5 | D4 PASS_GAP_FREE | complete package + manifest/checksums + full required suite + exact artifact readback |
| D6 | D5 PASS_GAP_FREE | independent full audit + all required test invocations + exact outputs + retention proof |
| E0 | D6 PASS_GAP_FREE | complete requirement/gap discovery and traceability |
| E1 | E0 PASS_GAP_FREE | all conflicts reconciled; no pending owner decision affecting E2/E3 |
| E2 | E1 PASS_GAP_FREE | original accounting evidence/identity/ledger complete; replay separated |
| E3 | D0–D6 + E0–E2 PASS_GAP_FREE + Preservation PASS | all acceptance tests/fixtures/negative coverage pass |
| E4 | E3 PASS_GAP_FREE | independent financial/statistical reconciliation under authorized identities |
| E5 | E4 PASS_GAP_FREE | independent P17 acceptance evidence and owner authorization where required |
| E6 | E5 PASS_GAP_FREE | P18 eligibility package, durable retention, final owner decision |

أي شرط لا ينطبق يجب إثبات عدم انطباقه بمصدر موثق؛ لا يُترك فارغاً. إذا بقيت فجوة في E2 فلا يبدأ E3. لا تُفسر كلمة «مكتمل» على أنها إعفاء من أي قرار مالك محمي.

---

# 20. مصفوفة المسؤوليات وحدود التنفيذ

| العمل | الوكيل ينفذ تلقائياً؟ | القيد |
|---|---|---|
| قراءة GitHub والبحث والمقارنة | نعم | لا ادعاء دون مصدر |
| تحديث مكتبة البرومبتات | نعم | لا يغير المرجع أو business rules |
| إنشاء فرع وCommit على فرع العمل | نعم | لا main/merge/force-push |
| إصلاح code/tests/docs | نعم | فقط عيب تقني مثبت ضمن القواعد |
| تشغيل unit/integration tests | نعم | افحص الآثار الجانبية أولاً |
| تشغيل Trials/Monte Carlo/N expansion | لا | قرار مالك محدد |
| backfill/zero-fill للحسابات التاريخية | لا | محظور |
| تغيير SOURCE_SHA/cohort/seed | لا | قرار مالك |
| تعديل/حذف Artifact تاريخي | لا | قرار مالك |
| حفظ ملف على هاتف المالك | لا | فعل مادي خارج وصول الوكيل |
| تنزيل artifact وإعداد رابط | نعم إذا الأداة متاحة | لا يعني حفظ الهاتف |
| نسختان دائمتان في خدمات خارجية | فقط إذا الوجهة متصلة ومصرح بها | وإلا BLOCKED |
| Merge إلى main/Release/final acceptance | لا | قرار مالك صريح منفصل |

---

# 21. معايير إدارة الحجم والملفات المهمة

1. أعد فحص حجم كل ملف وArtifact وexpiry في كل جلسة؛ لا تعتمد على لقطة 2026-11-05.
2. اعتبر 50 MiB حد تحذير داخلي للملفات الثنائية في Git، و100 MiB حد توقف صارم قبل إدخال ملف إلى Git history.
3. D3-S ينتج عشرة أجزاء مع manifest لكل جزء؛ لا يرفع الأجزاء قبل التحقق من أحجامها وبصماتها ومحتواها.
4. لا تحذف المصدرين الأصليين ولا تنقلهما ولا تستبدلهما بالمشتقات.
5. لا تكرر ملفات support المشتركة بلا داعٍ؛ سجل أثر التكرار على الحجم.
6. إذا بقي ملف مشتق أكبر من الحد، أوقف Git commit لذلك الملف، وافحص وجهات التخزين المصرح بها أو Artifact workflow المؤقت مع خطة تنزيل/استعادة.
7. لا تخلط حد GitHub single-file مع Actions Artifact retention؛ هما مشكلتان مختلفتان.
8. قدم للمالك قائمة مرتبة بالملفات >100 MiB: الاسم، الحجم، SHA-256، Artifact ID، expiry، رابط تنزيل حديث.
9. أعط المالك وقتاً كافياً لتنزيل النسخة الهاتفية قبل expiry، واذكر صراحةً أن اكتمال التنزيل والحفظ على الهاتف يحتاج تأكيده.
10. لا تعلن Global Preservation PASS إلا بعد نسختين دائمتين وrestore tests.

---

# 22. التوثيق والاستمرارية — Append-only

لكل مرحلة:
- REQUIREMENTS_MATRIX_<PHASE>_<DATE>.csv|json
- INPUT_IDENTITY_MATRIX_<PHASE>_<DATE>.json
- TEST_RUN_MATRIX_<PHASE>_<DATE>.json
- DEFECT_REGISTER_<PHASE>_<DATE>.json
- EVIDENCE_LEDGER_<PHASE>_<DATE>.json
- RETENTION_MANIFEST_<PHASE>_<DATE>.json
- CLOSURE_REPORT_<PHASE>_<DATE>.md
- SESSION_HANDOFF_<DATE>.md

الأسماء الفعلية يمكن أن تتبع conventions المستودع، لكن لا يجوز أن تضيع هذه الوظائف. لا تستبدل ملفات تاريخية بصمت؛ أضف revision جديداً أو correction ledger. حدّث docs/PROJECT_CONTINUITY.md وSession Status وHandoff في نهاية كل جلسة تنفيذية. احسب Raw SHA-256 وGit blob SHA-1 والحجم والـcommit. تحقق من exact final HEAD بعد آخر Commit.

---

# 23. نموذج تقرير الإغلاق النهائي

يجب أن يتضمن التقرير:
1. النتيجة: PASS_GAP_FREE أو BLOCKED.
2. اسم المرحلة المطلوبة وأي أسلاف تم إصلاحها قبلها.
3. المستودع والفرع وbefore/after HEAD وmain HEAD والمقارنة.
4. مرجع v2.4.0 وقرار المالك وبصماتهما.
5. Requirement Matrix كاملة مع عدد المتطلبات ومغطى/ناقص.
6. Source/identity matrix.
7. جميع الاختبارات: المطلوب والمنفذ فعلياً والناجح والفاشل وNOT_RUN.
8. Run/Job/tested SHA/logs.
9. Defects/root causes/fixes/regression.
10. outputs/artifacts/size/hash/expiry/retention/restore.
11. independent review وحدودها.
12. exact raw readback لكل وثيقة جديدة.
13. exact final HEAD.
14. جميع القيود والقرارات المطلوبة.
15. بيان واضح بأن المرحلة التالية لم تبدأ.
16. رابط كل ملف evidence وكل commit.

---

# 24. سياسة Actions وعمليات طويلة المدة

- افحص workflow YAML ومصدره وpermissions والـinputs قبل trigger.
- افحص concurrency لمنع تعارض تشغيلين على نفس identity/artifact.
- لا تشغل workflow قد يطلق Trial/Simulation/Monte Carlo أو N expansion دون قرار مالك.
- سجل workflow SHA وrun ID وjob IDs وtested SHA.
- إذا كان متوقعاً أن يستغرق 10 دقائق أو أكثر: شغله، أعط المالك Run ID وCommit SHA، ثم توقف ولا تنتظر النتيجة.
- لا تنسب نتيجة workflow إلى commit لم يختبره فعلياً.
- بعد كل commit وثائقي أو برمجي، أعد فحص HEAD النهائي؛ أي commit لاحق يبطل وصف HEAD السابق بأنه النهائي.
- فشل أداة GitHub أو API لا يثبت غياب الملف أو Artifact؛ جرّب مساراً آخر مناسباً ثم صنف النتيجة.

---

# 25. ترتيب التنفيذ العملي

1. Bootstrap حي.
2. إنقاذ Artifacts حسب expiry.
3. إكمال D0.
4. إكمال D1.
5. إكمال D2.
6. إكمال D3 الأصلي وD3-S1/D3-S2.
7. إكمال D4.
8. إكمال D5.
9. إكمال D6.
10. إكمال E0.
11. إكمال E1.
12. إكمال E2.
13. Global Preservation Gate.
14. E3.
15. E4.
16. E5.
17. E6.

لا تُنشأ مرحلة رئيسية جديدة خارج D0–D6/E0–E6. D3-S1/S2 بوابات فرعية داخل D3. أعمال إنقاذ الاحتفاظ وBootstrap أنشطة عابرة لا تتجاوز أو تستبدل بوابة أي مرحلة.

---

# 26. مراجعة REV5 وتصنيف ما تغير

| مجال REV5 | حكم المراجعة | تحديث REV6 |
|---|---|---|
| GitHub-first/bootstrap | سليم أساساً | أضيفت preflight للصلاحيات وworkflow side effects |
| owner authority | سليم | أضيف عقد تفصيلي لرسالة اسم المرحلة |
| zero-gap | سليم من حيث المبدأ | حُددت حدود completeness وعدم ادعاء اليقين المطلق |
| D0–D6 prompts | جيدة لكنها موجزة في بعض الاختبارات | توسعت عقود البيانات والاختبارات والـnegative cases |
| E0–E6 prompts | جيدة أساساً | توسعت traceability/decision/acceptance/release controls |
| D3-S | صحيح من حيث 5×5 و10 files | أضيف D3-S1 partition وD3-S2 round-trip وإدارة حجم GitHub |
| retention | يحدد نسختين دائمتين | أضيف restore test وdistinction الهاتف/وجهة دائمة |
| tests | يطلب exact SHA | أضيف test catalog/expected-vs-actual/regression evidence |
| defects | غير مفصل بما يكفي | أضيف root-cause register وseverity وclosure evidence |
| stage gates | موجودة | أعيد تعريف شروط الدخول والخروج ومصفوفة التتبع |
| session close | append-only | exact final HEAD بعد آخر commit وRaw readback |
| assurance wording | قد يوحي بصفر مطلق | قُيد PASS_GAP_FREE بالنطاق والمتطلبات المعتمدة |

## 26.1 قرارات التعارض

1. لا تنشأ مرحلة رئيسية جديدة بين D0–D6 أو E0–E6؛ التقسيم D3-S بوابة فرعية داخل D3 حتى لا يختل التسلسل.
2. لا يعتبر تقسيم المصنفين حلاً لاحتفاظ Actions Artifacts؛ يجب إنقاذ النسخ الأصلية والمشتقات كل على حدة.
3. لا يكتب ملف >100 MiB في Git history؛ يوقف commit ويستخدم وجهة مصرح بها.
4. لا يبدأ الوكيل المرحلة المطلوبة قبل إصلاح أسلافها، لكنه لا يبدأ أي مرحلة لاحقة بعد هدف المالك.
5. لا تعني عبارة «صفر فجوات» غياب unknown unknowns؛ تعني تغطية كل المتطلبات المحددة مع completeness discovery مستقلة وحدود معلنة.
6. لا يمكن للوكيل تأكيد نسخة الهاتف؛ يمكنه توفير تنزيلات موثقة فقط.
7. لا تتجاوز مكتبة REV6 صلاحيات المالك ولا تحول الموافقات القديمة المحدودة إلى تفويض دائم.

---

# 27. سجل إصدار REV6

- احتفظت REV6 بنص REV5 كاملاً كأساس للمقارنة، وأضفت مواصفة تشغيلية حاكمة مفصلة.
- لم تحذف REV1 أو REV2 أو REV3 أو REV4 أو REV5.
- لم تغير المرجع v2.4.0 أو قرار المالك أو أي قواعد أعمال.
- لم تشغل أي Trial أو Simulation أو Monte Carlo.
- لم تغير SOURCE_SHA أو cohort_id أو MASTER_SEED أو Trial identity.
- لم تعدل أو تحذف أي Artifact أو manifest تاريخي.
- لم تعدل main ولم تدمج ولم تنشر Release ولم تعلن قبولاً نهائياً.
- إنشاء REV6 لا يغلق D0 أو أي مرحلة أخرى ولا يجيز بدء D0 قبل مراجعة صلاحيتها التشغيلية وقرار المالك إن كان مطلوباً.
- يظل Global Preservation Gate مستقلاً وإلزامياً قبل E3.
- المعيار: لا انتقال دون بوابة سابقة PASS_GAP_FREE، ولا ادعاء بلا دليل، ولا صلاحية محمية دون قرار مالك.

**نهاية المواصفة التشغيلية REV6.**
