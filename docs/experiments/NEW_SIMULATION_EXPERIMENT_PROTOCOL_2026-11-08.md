# بروتوكول التجربة المستقلة لإعادة تشغيل محاكاة الدراجات النارية من الصفر

**المعرّف:** `NEW-SIM-EXP-2026-11-08`  
**الإصدار:** 1.0-DRAFT  
**الحالة:** `PREPARATION_ONLY — NOT_AUTHORIZED_FOR_EXECUTION`  
**تاريخ الإعداد:** 2026-11-08  
**المستودع:** `yasmin977209-ux/motorcycle-simulation`  
**فرع الوثيقة:** `docs/new-simulation-protocol-20261108`  
**الفرع الأساس:** `tmp/d1-rebuild-20261101` عند `f2ffb9743c8b9aff9fd9d4cadcdb5484e6069866`  
**main عند الإعداد:** `1d67cd56d326a9c42f7ecf324fa284dcc129acd4`

> هذه الوثيقة خطة تجربة ومراجعة وليست قرار تشغيل. لا تنشئ بذاتها تفويضاً لتشغيل Trial أو Simulation أو Monte Carlo، ولا تغيّر المرجع أو قواعد الأعمال أو العتبات أو هويات البيانات. لا يبدأ التنفيذ إلا بعد إغلاق بوابات ما قبل التشغيل وتسجيل تأكيد المالك النهائي المحدد في القسم 14.

---

## 1. الغرض والسؤال الذي ستجيب عنه التجربة

إنشاء سلالة تشغيل جديدة ومعزولة للمحاكاة، بهوية مستقلة ومخرجات جديدة غير قابلة للخلط مع السجلات التاريخية، ثم تقييمها بصورة مستقلة لتحديد ما إذا كانت النتائج قابلة لإعادة الإنتاج، ومكتملة، ومتوافقة مع المرجع الحاكم والقرارات المعتمدة.

السؤال الأساسي:

**هل يستطيع مصدر محرك مثبت، ضمن هوية جديدة ومعلنة، إنتاج مخرجات S6 وC100 مكتملة وقابلة للتحقق، مع حفظ provenance والـArtifacts وإثبات سلامة المحاسبة والتغطية والمقارنات؟**

هذه التجربة لا تهدف إلى:
- محو أو تصحيح أو استبدال أي Artifact أو Manifest أو Run تاريخي.
- تحويل Replay تاريخي إلى Original Historical Evidence.
- إثبات أن D0 التاريخية أصبحت `PASS_GAP_FREE`.
- ترقية Production Gate A أو Gate B أو Stability أو Final Acceptance تلقائياً.
- تغيير أي قاعدة عمل أو معادلة محاسبية أو RNG أو seed أو threshold.
- استئناف E3–E6 أو إعلان إصدار نهائي.

## 2. الأساس الحاكم وسلطة القرار

تُنفذ التجربة، إذا أجيزت، تحت المرجع الحاكم v2.4.0 وقرار المالك `D-2026-10-30-REFERENCE-V2.4.0`، مع الالتزام بحدود التفويض المكتوب. لا تُستخرج قواعد من مخرجات Workflow أو من هذه الخطة.

### 2.1 مانع تحقق المرجع قبل التشغيل

سجل القرار `D-2026-10-30-REFERENCE-V2.4.0` يعلن اعتماد المالك ويذكر SHA-256 المصرح به:

`225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`

لكن الملف الموجود على فرع العمل في المسار `docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md` يحمل في رأسه حالة `PROPOSED_FOR_OWNER_ADOPTION — NOT_EFFECTIVE_YET`، وGit blob SHA المقروء في هذا الفحص هو `9fe43bfbb2cbfd2bb7f7010866e7469506d22c33`. كما ينص قرار المالك نفسه على أن القيمة المصرح بها لا تثبت وحدها تحققاً تشفيرياً من بايتات الملف.

لذلك، قبل أي تشغيل:
1. استرجاع ملف المرجع الأصلي المعتمد الذي يطابق الاسم والبصمة المعلنين في قرار المالك، لا افتراض أن الملف ذي الرأس المتعارض هو النسخة المعتمدة.
2. جلب Raw bytes من GitHub أو المصدر المعتمد، وحساب SHA-256 محلياً من البايتات.
3. تسجيل Raw URL وSHA-256 والحجم وGit blob SHA-1 وCommit الحاوي.
4. مطابقة البصمة مع قرار المالك، وقراءة النص المعياري الكامل.
5. إذا تعذر التطابق أو بقي التعارض، تكون النتيجة `BLOCKED_REFERENCE_BYTES_NOT_VERIFIED` ولا يبدأ أي تشغيل يعتمد على قواعد المرجع.

## 3. فصل التجربة الجديدة عن التاريخ

تُنشأ هوية مستقلة وArtifacts وManifests جديدة. لا تُستخدم مسارات أو أسماء أو معرفات توحي بأن الناتج هو Artifact تاريخي.

| السلالة | الهوية | المعاملة |
|---|---|---|
| S6 التاريخية | `SOURCE_SHA=da1a9ea9b5cd789c944de3f07b08395bb67c49e7`; `cohort_id=s6-v23-da1a9ea9`; `MASTER_SEED=20270101` | تاريخ محفوظ غير قابل للتعديل |
| S6 الجديدة المقترحة | `SOURCE_SHA` المرشح `002b74893ca9dfea864e83fecc558f2388748ffe`; `cohort_id=s6-v23-rebuild-20261105`; `MASTER_SEED=20270101` | سلالة جديدة؛ لا تُقفل الهوية قبل preflight والتأكيد النهائي |
| C100 الجديدة المقترحة | `cohort_id=c100-v23-rebuild-20261105` | سلالة حتمية منفصلة تماماً عن S6 |
| Stage 12/13 | هويتها التاريخية المستقلة | لا تُستخدم كمدخل أو بديل لـS6 أو C100 |

**تنبيه بشأن SOURCE_SHA المرشح:** قرار E2 يذكر `002b748...` كـsource pin candidate، لكن commit `002b74893ca9dfea864e83fecc558f2388748ffe` الذي فُحص في هذه الجلسة يغير ملف Workflow واحداً فقط (تغيير `cancel-in-progress`). لذلك لا يكفي SHA هذا الـcommit وحده لإثبات أن شجرة كود المحرك هي المصدر المقصود. يجب في preflight إثبات source tree/model-source pin الفعلي، وتحديد الفرق بين Workflow HEAD وModel SOURCE_SHA، وتثبيت كليهما في Manifest منفصل. لا يجوز تمرير Workflow HEAD مكان SOURCE_SHA أو العكس.

## 4. نطاق التشغيل المقترح — من قرار E2، وليس تفويض تنفيذ

النطاق أدناه من وثيقة `docs/post_d/E2_OWNER_DECISION_APPROVED_A_2026-11-05.md`. القرار يجيز إعداد سلالة جديدة، لكنه يضع التنفيذ في حالة `WAIT_FINAL_OWNER_CONFIRMATION` ويشترط تأكيداً نهائياً قبل أي Trial.

### 4.1 S6 — stochastic lineage

- 20 سيناريو عشوائياً.
- Trial IDs من 1 إلى 2400 لكل سيناريو.
- الإجمالي: 48,000 هوية Trial.
- `MASTER_SEED=20270101` كما ورد في القرار.
- المصدر/الفوج المقترحان: القيم في جدول القسم 3، وتبقيان مرشحتين حتى اجتياز preflight والتوقيع النهائي.
- مقارنة كل `trial_fingerprint` مالي جديد مع نظيره التاريخي في السيناريو نفسه ورقم Trial نفسه.
- شرط المقارنة المحدد في قرار E2: 48,000 من 48,000 تطابقاً تاماً. أي اختلاف واحد يوقف إعادة البناء فوراً، ويحفظ المخرجات التشخيصية دون السماح لـD0' باستهلاك مجموعة غير مطابقة.

تُفصل بصمة النتائج المالية عن RNG/source-bound audit fingerprint؛ اختلاف بصمة provenance بسبب SOURCE_SHA لا يُفسر تلقائياً كاختلاف في السحب العشوائي أو النتيجة المالية.

### 4.2 C100 — deterministic lineage منفصلة

- خمسة مسارات: `C100_G100`, `C100_G070`, `C100_G050`, `C100_G030`, `C100_G000`.
- 300 تكرار مقترح لكل مسار؛ الإجمالي 1,500 سجل تنفيذ.
- `N_unique_paths=1` لكل مسار حتمي وفق المرجع.
- لا يجوز وصف 300 تكرار للمسار الواحد بأنها 300 عينة عشوائية مستقلة.
- قرار E2 يطلب تأكيد المالك على عقد المقارنة: هل تتم مقارنة كل سجل من 300 مع بصمة Golden الوحيدة المعتمدة لذلك المسار؟ يظل هذا البند `OWNER_CONFIRMATION_REQUIRED` حتى يُحسم صراحة.
- لا تُدمج سجلات C100 في عدد عينات S6 أو حسابات الاستقرار/FWER الخاصة به.

### 4.3 ما لا يدخل النطاق

- لا N=4800 ولا أي N expansion.
- لا سيناريوهات جديدة أو Trial IDs إضافية.
- لا Golden revalidation خارج الخمس مسارات والعقد الذي يؤكده المالك.
- لا backfill أو zero-fill أو inferred accounting.
- لا أي تعديل إلى المرجع أو business logic أو accounting rules أو RNG implementation أو thresholds.

## 5. بوابات ما قبل التشغيل (Preflight)

لا يكفي نجاح فحص واحد. يجب تسجيل كل بوابة منفصلة بدليل قابل لإعادة الفحص.

| الرمز | الفحص | الدليل المطلوب | شرط الإيقاف |
|---|---|---|---|
| PF-01 | اعتماد المرجع | Raw URL، SHA-256 محسوب، الحجم، Git blob SHA-1، Commit، قرار المالك | عدم تطابق المرجع أو غياب بايتاته |
| PF-02 | تثبيت المصدر | Model source tree، Workflow HEAD، commit/tree IDs، file hashes، diff reviewed | التباس Workflow HEAD وSOURCE_SHA |
| PF-03 | تثبيت الهوية | S6 SOURCE_SHA/cohort/seed/scenario/Trial map؛ C100 cohort/path IDs | أي قيمة غير مؤكدة أو متعارضة |
| PF-04 | مراجعة كود المحرك | مراجعة مستقلة للتغييرات، accounting snapshot، RNG، Trial fingerprint، date engine | أي تغيير غير مصرح أو غير مفسر |
| PF-05 | بيئة التشغيل | Python/runtime، dependencies lock، OS/container، locale/timezone، configuration | اختلاف غير مثبت أو dependency غير مثبتة |
| PF-06 | Workflows | مراجعة triggers وpermissions وconcurrency وcancel behavior وcheckout refs وartifact paths | Trigger قد يطلق تجربة غير مقصودة أو يلغي Run آخر |
| PF-07 | اختبارات غير تشغيلية | static validation وunit tests آمنة لا تطلق Trials/Simulation/Monte Carlo | اختبار يطلق محاكاة أو يغير الهوية |
| PF-08 | تخزين الأدلة | سعة كافية، أسماء فريدة، retention، نسختان مستقلتان، readback/restore plan | غياب مسار حفظ أو عدم كفاية السعة |
| PF-09 | أمن البيانات | secret scan، منع tokens/credentials من logs/artifacts، صلاحيات أقل امتيازاً | تسرب سر أو صلاحيات زائدة |
| PF-10 | خطة الإيقاف | fail-fast conditions، cancellation plan، run/job owner، استرداد جزئي | عدم القدرة على إيقاف التشغيل أو عزل مخرجاته |
| PF-11 | مراجعة مستقلة | اسم/دور المراجع، الملفات والـSHAs التي راجعها، تعارض المصالح | غياب المراجع المستقل |
| PF-12 | موافقة المالك النهائية | نص التأكيد الكامل في القسم 14 بعد إغلاق PF-01..PF-11 | عدم وجود تأكيد صريح مطابق للنطاق |

تكون نتيجة كل بند إحدى: `PASS_SCOPED`, `FAIL`, `BLOCKED`, `NOT_RUN`, `NOT_APPLICABLE_WITH_REASON`. لا تستخدم `PASS` المجردة.

## 6. خطة التنفيذ بعد التفويض فقط

### المرحلة A — تجهيز غير تشغيلي

- إنشاء branch/commit مستقل للتجربة؛ عدم العمل على `main`.
- تثبيت workflow ref وmodel source pin في Manifest قبل الإطلاق.
- تشغيل static/unit checks التي ثبت أنها لا تطلق Trials أو تغير بيانات.
- إجراء dry-run على مستوى parsing/configuration فقط إذا ثبت أنه لا ينفذ أي Trial أو Monte Carlo.
- اعتماد خطة Artifact naming، والـmanifest schema، وretention، وrestore.

### المرحلة B — إطلاق S6

بعد التوقيع النهائي فقط:
1. تشغيل Workflow واحد مضبوط على هوية S6 الجديدة.
2. تسجيل Run ID وWorkflow HEAD وModel SOURCE_SHA وCommit وseed وcohort وscenario/Trial ranges قبل أي انتظار.
3. عند بدء تشغيل طويل (10 دقائق أو أكثر)، الإبلاغ عن Run ID وCommit SHA والتوقف عن انتظار اكتماله في جلسة الإطلاق؛ لا تُترك الجلسة في انتظار غير محدود.
4. تقسيم نتائج السيناريوهات إلى artifacts محددة الهوية، مع aggregate منفصل.
5. عند أول mismatch في financial fingerprint، أو نقص Trial، أو فساد Artifact، أو اختلاف هوية، يوقف المسار fail-closed وتُحفظ الأدلة الجزئية كتشخيص فقط.
6. لا يُعاد التشغيل تلقائياً ولا يُغيّر seed أو Trial IDs أو source pin لمعالجة الفشل.

### المرحلة C — إطلاق C100

- لا يبدأ قبل تثبيت عقد المقارنة النهائي كتابةً.
- تشغيل المسارات الخمسة تحت cohort مستقل.
- توثيق أن التكرارات 300 لكل مسار ليست عينات مستقلة.
- حفظ Golden comparison لكل مسار، دون دمج بيانات C100 مع S6.

### المرحلة D — التجميع والتحقق

- إنشاء manifest شامل يربط كل Artifact بـRun/Job/Commit/Workflow HEAD/SOURCE_SHA/cohort/seed/scenario/Trial range.
- التحقق من SHA-256 من bytes الفعلية لكل Artifact، GitHub artifact digest، الحجم، ZIP CRC، member hashes، Parquet schema، row counts، nulls، duplicates، partitions، lineage، وrestore.
- التحقق من اكتمال 48,000 Trial وحقول daily balance الخمسة في كل daily row مطلوب.
- فحص `Total_Assets == Total_Equity` و`Balance_Difference == 0` لكل daily row وفق قرار E2، دون balancing plug أو inferred values.
- التحقق من كامل date/Trial coverage وعدم وجود فجوات أو ازدواجية.
- حفظ سجل الفشل كما هو؛ لا تُحذف النتائج غير المطابقة.

### المرحلة E — بناء D0'–D6' المنفصل

لا يبدأ أي stage من D0'–D6' إلا وفق الترتيب والبوابات المعتمدة، وبناءً على artifacts الجديدة المطابقة فقط. يجب أن تكون lineage الجديدة صريحة (`D0'` ... `D6'`) وألا تُسمى أو تُعرض على أنها السجلات التاريخية D0–D6. لا يُستنتج انتقال مرحلة من نجاح Run أو Job منفرد.

هذه الخطة لا تتجاوز ترتيب D0→D1→D2→D3→D4→D5→D6، ولا تجعل D6 قبولاً نهائياً. أي مراحل لاحقة خارج النطاق تحتاج قراراً منفصلاً.

## 7. معايير التقييم والقبول

يتم التقييم من مراجع مستقل، على exact tested SHA وexact final HEAD، وبالاستناد إلى ملفات وأرقام فعلية لا إلى عناوين artifacts.

### 7.1 سلامة الهوية والمصدر
- كل سجل يطابق SOURCE_SHA/cohort/seed/scenario/Trial المعلن.
- لا خلط بين Workflow HEAD وModel SOURCE_SHA.
- لا خلط بين S6 وC100 وStage 12/13.
- fingerprints ومقارنات Golden كاملة وفق عقد المقارنة الموقع.

### 7.2 اكتمال المحاكاة والمحاسبة
- 48,000/48,000 Trial IDs في S6 دون نقص أو تكرار.
- daily output schema يتضمن الحقول الخمسة: `Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Total_Assets`.
- لا nulls أو gaps غير مفسرة في التغطية المطلوبة.
- `Total_Assets == Total_Equity` و`Balance_Difference == 0` لكل daily row المطلوب.
- لا استنتاج أو تصفير أو backfill لأي حقل.

### 7.3 سلامة الأدلة وإعادة الإنتاج
- hashes محسوبة من bytes الفعلية، وليست من أسماء الملفات أو metadata وحدها.
- manifests تربط المصدر والهوية والـrun والـartifact والصفوف والملفات.
- نسختان دائمتان مستقلتان فعلياً، مع readback وrestore ناجحين لكل منهما.
- إعادة تشغيل/تحقق مستقل وفق التفويض، دون تغيير الهوية أو النتائج الأصلية.
- logs لا تحتوي أسراراً أو بيانات اعتماد.

### 7.4 أحكام النتيجة

| الحكم | متى يستخدم |
|---|---|
| `ACCEPT` | كل معايير النطاق الموقع اجتازت، وكل الأدلة مكتملة ومتحقق منها مستقلاً |
| `ACCEPT_WITH_LIMITATIONS` | نجاح محدود فقط؛ تُذكر القيود ولا يُرفع أي gate خارج النطاق |
| `REJECT` | إخفاق مثبت في الهوية أو المقارنة أو المحاسبة أو التغطية أو سلامة الأدلة |
| `INCONCLUSIVE` | لا توجد أدلة كافية أو تعذر التحقق؛ لا يعني نجاحاً ولا فشلاً مثبتاً |

حتى حكم `ACCEPT` لهذه التجربة لا يعني تلقائياً `FINAL_ACCEPTED` أو `PRODUCTION_GATE_A=PASS` أو `CONVERGED` أو إغلاق D0 التاريخية. كل إعلان يحتاج بوابته وقراره وأدلته الخاصة.

## 8. شروط الإيقاف الفوري

يوقف التنفيذ أو المسار المتأثر فوراً عند:
- اختلاف SOURCE_SHA أو cohort أو seed أو Trial identity عن القيم المعتمدة.
- أي mismatch في fingerprint المقارنة المحددة في قرار E2.
- نقص أو تكرار Trial ID أو scenario أو partition.
- غياب أحد الحقول المحاسبية الخمسة، أو null غير مفسر، أو عدم توازن يومي.
- Artifact corrupt أو hash mismatch أو فشل restore.
- استخدام Workflow HEAD على أنه SOURCE_SHA أو العكس.
- اكتشاف تغيير غير مصرح في business logic أو RNG أو accounting أو threshold.
- تسرب secret أو ظهور credential في log/artifact.
- Trigger غير متوقع أو احتمال إلغاء Run آخر أو الكتابة فوق Artifact سابق.
- نفاد السعة أو عدم كفاية مساحة التخزين أو فقدان provenance.
- ظهور حاجة إلى قرار مالك إضافي أو تفسير قاعدة غير محسومة.

عند الإيقاف: احفظ الحالة والـlogs والـmanifests الجزئية مع تصنيفها `INCOMPLETE/DIAGNOSTIC_ONLY`، ولا تعاود التشغيل أو تغير الهوية دون موافقة صريحة.

## 9. حفظ الأدلة والتسمية

- كل اسم Artifact يبدأ ببادئة lineage جديدة واضحة، مثلاً `NEW-SIM-20261108-S6-` أو `NEW-SIM-20261108-C100-`.
- لا تستخدم IDs تاريخية أو أسماء توحي بأن artifact جديد هو الأصلي.
- Manifest إلزامي لكل Artifact، ويحتوي على الأقل: experiment_id، lineage، run_id، job_id، workflow_name، workflow_head_sha، model_source_sha، source_tree_sha، cohort_id، master_seed، scenario_id، trial_id/range، schema_version، row_count، file/member hashes، size_bytes، creation time، tool/runtime/dependency versions، status، reviewer، restore evidence.
- لا تسجل secrets أو tokens أو بيانات اعتماد.
- تحفظ نسختان مستقلتان في failure domains مختلفة، وتُختبر إعادة القراءة والاستعادة. مجرد وجود رابطين أو مزودين لا يثبت الاستقلال.
- لا تعدّل Artifacts أو manifests التاريخية ولا تعيد تسميتها.

## 10. الفصل بين نتائج التجربة والبوابات التاريخية

الحالة المعروفة عند إعداد البروتوكول:
- D0 التاريخية: `BLOCKED / MISSING_EVIDENCE` لـ`PASS_GAP_FREE`؛ يحتفظ بـ`PASS_SCOPED_WITH_LIMITATIONS` التاريخي ولا يُمحى.
- Financial Gate A: `PASS_SCOPED` فقط.
- Production Gate A: `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`.
- Gate B عند N=2400: `FAIL_SCOPED (10/10)`.
- Stability: `NOT_CONVERGED (0/60)`.
- N=4800: `NOT_EXECUTED`.
- Full Logging: 105 representative keys فقط.
- الحقول المالية الخمسة في التاريخ الأصلي تظل `MISSING_EVIDENCE` ولا تُستبدل بنتائج السلالة الجديدة.

نجاح إعادة البناء الجديدة يمكن أن يقدم أدلة جديدة لسلالة جديدة فقط؛ ولا يثبت أن السجلات التاريخية كانت مكتملة أو أن الحقول الخمسة كانت محفوظة فيها.

## 11. تقدير الموارد والمدة

قرار E2 يورد تقديراً تخطيطياً يقارب **24 ساعة** لعبء إعادة البناء، قبل إضافة احتياطيات retries ونقل artifacts والتدقيق المستقل وGolden checks وD0'–D6'. هذا تقدير تخطيطي غير مقاس وليس ضمان runtime.

قبل التوقيع النهائي يجب:
- تقدير حجم artifacts المتوقع وسعة التخزين والنقل.
- التأكد من حدود وقت GitHub Actions ووقت كل job.
- وضع خطة استئناف آمنة لا تعيد Trial identities أو تضاعف نتائجها.
- تحديد من يراقب التشغيل وكيف تُرسل تقارير Run ID وtested SHA.
- عدم إطلاق Workflow طويل ثم انتظار اكتماله في جلسة واحدة.

## 12. التقييم المستقل والتقرير النهائي

يجب أن يكون المراجع المستقل مختلفاً عن منفذ التشغيل قدر الإمكان. التقرير النهائي يتضمن:
1. القرار النهائي `ACCEPT / ACCEPT_WITH_LIMITATIONS / REJECT / INCONCLUSIVE`.
2. هوية التجربة الكاملة والـsource/Workflow SHAs.
3. مصفوفة كل معيار: المتوقع، المنفذ، النتيجة، الدليل، hash، النطاق.
4. ملخص fingerprints ومقارنات Golden والتغطية.
5. تدقيق المحاسبة اليومية والحقول الخمسة والتوازن.
6. نتائج فحص artifacts والـmanifests والنسخ والاستعادة.
7. جميع الأخطاء والتوقفات والانحرافات والقيود.
8. بيان صريح بما لا تثبته التجربة، بما في ذلك D0 التاريخية وProduction Gate A وGate B وStability والقبول النهائي.
9. توصية مستقلة: اعتماد التجربة ضمن نطاقها، رفضها، أو طلب إعادة تجربة بقرار جديد.

## 13. حالة المراجعة الحالية — ملاحظات مانعة معروفة

| البند | المعلومة الحية/المصدر | الحالة |
|---|---|---|
| working branch | `tmp/d1-rebuild-20261101` عند `f2ffb9743c8b9aff9fd9d4cadcdb5484e6069866` | تم التحقق |
| main | `1d67cd56d326a9c42f7ecf324fa284dcc129acd4` | تم التحقق، لم يُعدّل |
| PR #82 | Draft مفتوح، head `2b763c7...`، base `f2ffb974...` | غير مدمج؛ لا علاقة له بتفويض التشغيل |
| D0 | `BLOCKED / MISSING_EVIDENCE` وفق سجل D0 Gap-Free Recovery | لا يتغير |
| قرار E2 rebuild | `OWNER_APPROVES_DETERMINISTIC_ACCOUNTING_REBUILD`، التنفيذ `WAIT_FINAL_OWNER_CONFIRMATION` | التحضير فقط |
| source pin المرشح | `002b748...` | يحتاج تحقق source-tree/model-source |
| E2 القديم Run | `41958935113` ناجح بوصف replay للهوية القديمة | ليس تشغيل السلالة الجديدة |
| C100 contract | مقارنة 300 تكرار مع Golden واحد لكل path تحتاج تأكيداً | غير محسوم |
| v2.4.0 bytes | القرار يصرح SHA، لكن الملف المقروء يحمل رأساً متعارضاً | مانع PF-01 |
| Releases | يوجد Draft Release لأرشيف S6 التاريخي | لا يُعدّل ولا يُنشر ضمن هذه التجربة |

لا تُستخدم لقطة الحالة أعلاه بديلاً عن إعادة التحقق الحي في يوم التنفيذ.

## 14. تأكيد المالك النهائي المطلوب قبل أي تشغيل

بعد إغلاق PF-01 إلى PF-11 وتقديم تقرير preflight للمراجعة، يجب أن يرسل المالك تأكيداً صريحاً يطابق النطاق أدناه. عبارة الموافقة العامة على إعداد البروتوكول أو مراجعة الوثيقة لا تكفي.

**نص التأكيد المقترح:**

> أؤكد بدء تنفيذ تجربة إعادة البناء الجديدة فقط وفق البروتوكول NEW-SIM-EXP-2026-11-08، بعد مراجعة تقرير preflight النهائي. أوافق على Model SOURCE_SHA الذي تم التحقق منه وتثبيته في Manifest، وعلى S6 cohort `s6-v23-rebuild-20261105` و`MASTER_SEED=20270101` و20 سيناريو × 2,400 Trial (48,000 Trial)، وعلى شرط التطابق المالي 48,000/48,000 مع fail-fast عند أول mismatch. أوافق على C100 cohort `c100-v23-rebuild-20261105` والخمس مسارات و300 تكرار لكل مسار، وعلى عقد المقارنة المحدد كتابةً في تقرير preflight. أقر بتقدير العبء التخطيطي البالغ نحو 24 ساعة وما قد يضاف إليه، وبأن السلالة الجديدة منفصلة تماماً عن التاريخ، وأن التجربة لا تعدّل main أو artifacts التاريخية ولا تعلن قبولاً نهائياً أو تغلق D0 التاريخية. أجيز إطلاق Trials/Simulation/Monte Carlo ضمن هذا النطاق فقط.

**سجل الموافقة:**
- Owner: `PENDING`
- Date/time: `PENDING`
- Preflight report commit/SHA: `PENDING`
- Verified Model SOURCE_SHA: `PENDING`
- S6 cohort: `s6-v23-rebuild-20261105`
- C100 cohort: `c100-v23-rebuild-20261105`
- C100 comparison contract: `PENDING`
- Authorization status: `NOT_AUTHORIZED_FOR_EXECUTION`

## 15. سجل الإصدارات

| الإصدار | التاريخ | التغيير |
|---|---|---|
| 1.0-DRAFT | 2026-11-08 | إعداد البروتوكول؛ لا تشغيل ولا تغيير هوية أو قواعد |

---

**الحكم الحالي:** `PREPARATION_ONLY — BLOCKED_BEFORE_EXECUTION`  
**الخطوة التالية المسموحة:** مراجعة البروتوكول، ثم استكمال PF-01..PF-11 وإعداد تقرير preflight منفصل.  
**الخطوة غير المسموحة حالياً:** أي Trial أو Simulation أو Monte Carlo أو Golden revalidation أو D0'–D6' execution قبل تأكيد المالك النهائي.


---

## 16. تصحيح نتائج التحقق الأولي — 2026-11-08 (Append-only)

هذا القسم يصحح/يستكمل الملاحظات الأولية في الأقسام السابقة دون حذفها:

### 16.1 المرجع v2.4.0 — تحقق بايتات مكتمل

تم جلب Raw bytes من GitHub عند commit `1491aefa84d061ef2b08cd3ea1e290a0bf3fb58b` للمسار:

`docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md`

- Raw URL: `https://raw.githubusercontent.com/yasmin977209-ux/motorcycle-simulation/1491aefa84d061ef2b08cd3ea1e290a0bf3fb58b/docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md`
- Raw-byte SHA-256: `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`
- Size: `401397 bytes`
- Git blob SHA-1: `9fe43bfbb2cbfd2bb7f7010866e7469506d22c33`
- Containing commit: `1491aefa84d061ef2b08cd3ea1e290a0bf3fb58b`

البصمة تطابق تماماً قيمة قرار المالك `D-2026-10-30-REFERENCE-V2.4.0` وحجم عضو المرجع داخل الأرشيف المرفق. إذن تحقق هوية البايتات `VERIFIED_LIVE`. يظل رأس الوثيقة يعرض `PROPOSED_FOR_OWNER_ADOPTION — NOT_EFFECTIVE_YET`، بينما قرار المالك يسجل `APPROVED_BY_OWNER` وتاريخ السريان 2026-10-30؛ كما أن اسم الملف في القرار يختلف عن مسار Git الحالي. يجب حفظ هذه الملاحظة في تصحيح حوكمي append-only، ولا تُعدّل بايتات المرجع المعتمد.

### 16.2 تصحيح ملاحظة SOURCE_SHA المرشح

الملاحظة السابقة بأن commit `002b748...` لا يثبت وجود Model Source لمجرد أن direct commit diff يغير Workflow فقط كانت استنتاجاً غير مكتمل. قرار E2 يحدد `002b74893ca9dfea864e83fecc558f2388748ffe` صراحةً كمصدر مرشح، وشجرة commit الكاملة `9cfaa2a8a57cfaf62beeb4a4166c042553173159` تحتوي كود المحرك المُصلح. لذلك يُقبل كـModel SOURCE_SHA مرشح ضمن PF-02، مع وجوب فصل Model SOURCE_SHA عن Workflow HEAD في Manifest التنفيذ.

### 16.3 مانع هوية جديد ومثبت

فحص المصدر عند `002b748...` أثبت أن قرار E2 الحالي لا يطابق عقود الهوية في الكود:
- `scripts/s6_first_checkpoint.py` يشتق cohort حصراً بصيغة `s6-v23-{SOURCE_SHA[:8]}` ولا يوفر `--cohort-id`. مع SOURCE_SHA الحالي تكون القيمة `s6-v23-002b7489`، لا `s6-v23-rebuild-20261105`.
- `scripts/s6_daily_path_identity.py` لا يقبل C100 cohort الجديد؛ الاستثناء الوحيد هو C100 التاريخي المثبت بمصدره وفوجه القديمين.
- `scripts/s6_checkpoint_config.json` ما زال مثبتاً على المصدر والفوج التاريخيين `da1a9ea9...` و`s6-v23-da1a9ea9`، وActions code يحمل هذا الإعداد تلقائياً ويرفض SOURCE_SHA الجديد، كما أن إعداد الاستئناف يشير إلى Run تاريخي بدلاً من clean start.
- لا توجد في CLI الحالية وسيلة لتعيين cohort جديد صراحةً، ولا Workflow مستقل يطلق السلالة الجديدة بهويتها المعتمدة.

هذا مانع `BLOCKED` لا يجوز تجاوزه بتغيير أسماء الـcohort أو patch مؤقت أو إعادة استخدام artifacts التاريخية. يلزم قرار مالك يختار إما تعديل هوية E2 لتتوافق مع الكود، أو السماح بتعديل محدود لعقد الهوية/الإعدادات وتثبيت SOURCE_SHA جديد. لا يغير هذا التصحيح أي هوية أو كود.

### 16.4 وضع بوابات Preflight بعد المراجعة الحية

التقرير التفصيلي في `docs/experiments/NEW_SIMULATION_PREFLIGHT_REPORT_2026-11-08.md` هو المرجع لسجل الفحوص. الملخص:
- PF-01 `PASS_SCOPED` — بايتات المرجع `VERIFIED_LIVE`، مع ملاحظة رأس الحالة/اسم المسار.
- PF-02 `PASS_SCOPED` — Model SOURCE_SHA وشجرة المصدر محددان.
- PF-03 `BLOCKED` — cohort/config mismatch.
- PF-04 `PASS_SCOPED` — مراجعة static محدودة لهوية ملفات المحرك؛ المراجعة المستقلة الكاملة لم تتم.
- PF-05 `BLOCKED` — لا dependency lock/runtime manifest دقيق.
- PF-06 `BLOCKED` — لا Workflow جاهز للسلالة الجديدة؛ Workflows الحالية مثبتة على نطاقات وهويات مختلفة.
- PF-07 `NOT_RUN` — لم تُشغل الاختبارات الآمنة على exact pin.
- PF-08 `BLOCKED` — لا نسختان دائمتان مستقلتان واختبار restore للسلالة الجديدة.
- PF-09 `NOT_RUN` — لم ينفذ secret scan/redaction audit.
- PF-10 `BLOCKED` — لا orchestrator جديد يطبق fail-fast والتعافي الآمن.
- PF-11 `BLOCKED` — لا independent reviewer ولا final owner confirmation.

**الحكم المصحح:** `BLOCKED_BEFORE_EXECUTION`. لا Trial أو Simulation أو Monte Carlo أو Golden revalidation أو D0'–D6' قبل حسم قرار الهوية وإغلاق البوابات ثم تأكيد المالك النهائي.

## 17. Owner decision and explicit identity-contract implementation — 2026-11-08

At 2026-11-08T16:30:32Z, the owner explicitly approved Path B: update the identity contract to accept `cohort_id` explicitly, pin the resulting source, and review/approve its exact fingerprint before any Trial. This is an operational authorization for the narrow identity-contract change only; it is **not** authorization to execute the experiment, create a Golden, expand N, merge, or publish a Release.

Approved new identities:
- S6: `s6-v23-rebuild-20261105`
- C100: `c100-v23-rebuild-20261105`

Implementation is isolated on branch `fix/explicit-cohort-identity-20261108`, Draft PR #84, based on PR #83's protocol branch:
- S6 now requires explicit `--cohort-id`; no longer derives the cohort from SOURCE_SHA's first eight characters.
- The daily-path validator accepts the explicit S6 and C100 rebuild families separately. The exact pinned historical C100 exception remains narrowly scoped.
- The S6 checkpoint config is reset to a fresh N=300 / trial IDs 1..300 baseline and no longer contains historical run IDs or a source pin copied from the previous cohort.
- Actions execution requires `S6_SOURCE_SHA` to equal both the CLI source SHA and exact `GITHUB_SHA`; the fresh checkpoint config rejects historical resume.
- C100 validates its new cohort family separately and preserves only the exact historical source/cohort exception.
- Safe identity tests and a read-only Actions workflow were added.

Safe verification evidence:
- Run `42500734407` passed the identity tests and non-execution guard before the dependency lock was added.
- Run `42500791300` passed the same tests and guard using the exact Python 3.11 dependency-version lock.
- The final candidate run after all append-only status updates must be checked before assigning the final code/Workflow HEAD as the reviewed pin.
- These runs perform no Trials, Simulation, Monte Carlo, or Golden generation.

Environment evidence currently scoped to the safe test workflow: Ubuntu 24.04, CPython 3.11.18, pip 26.2.2, and exact package versions in `requirements-lock-py311.txt`. This is a version lock, not a hash-locked wheel manifest or immutable runner image; the full simulation environment remains blocked until that stronger reproducibility requirement is closed.

Remaining blockers: dedicated simulation Workflow with independent fail-fast/recovery; two durable failure-domain storage destinations and a successful restore/readback; security/secrets scan and redaction audit; exact final source fingerprint and independent review. The S6 aggregator still treats the old C100 evidence as read-only historical reuse; it is not evidence for the new C100 cohort.

**Execution remains NOT AUTHORIZED.** No Trial, Simulation, Monte Carlo, Golden revalidation, N expansion, D0'–D6' execution, historical evidence mutation, main write, merge, or Release occurred. Overall status remains `BLOCKED_BEFORE_EXECUTION`.

## Identity-scope clarification — exact owner-approved values only — 2026-11-08

This addendum narrows any earlier wording that referred to a cohort “family” or pattern. The implementation accepts only the exact E2-approved values:
- S6: `s6-v23-rebuild-20261105`
- C100: `c100-v23-rebuild-20261105`

Other date variants or cohort IDs matching the same textual pattern are rejected. The exact historical C100 source/cohort exception remains unchanged and narrowly pinned. This is a fail-closed clarification; it does not authorize any additional cohort, Trial, or N expansion.

## Final verification and guard-scope correction — 2026-11-08

- The approved cohort contract is exact, not pattern-based: S6 `s6-v23-rebuild-20261105`; C100 `c100-v23-rebuild-20261105`. All other date variants are rejected. Historical C100 remains an exact source/cohort exception only.
- Final safe test run before the PR-trigger-only workflow correction: Run `42501711253`, candidate HEAD `1293d883071355200e90948fcce801f45aac7b7c`, `success`. It ran both approved safe suites: 13 passed in 0.95s; py_compile passed; non-execution guard passed; `SIMULATION_TRIALS=NOT_EXECUTED`.
- The safe workflow's pull-request base filter was corrected to `docs/new-simulation-protocol-20261108`, matching PR #84's actual base. The new branch HEAD must be re-read and the safe workflow run on that exact final HEAD before source-pin acceptance.
- Storage inspection: Dropbox rescue folder ~2.74 GB and OneDrive rescue folder ~4.11 GB / 85 children exist. Dropbox's `secondary_verified_mirror` is still the same Dropbox provider, not a second failure domain. OneDrive raw readback returned HTTP 403 `Database Is Read Only`; no byte-for-byte verification or restore test is complete. PF-08 remains `BLOCKED`.
- PR #84 remains Draft/open/unmerged with zero independent reviews/comments. PF-11 remains `BLOCKED`; dedicated simulation workflow, fail-fast/recovery, security scan/redaction, and separate final owner execution confirmation remain outstanding.
- No Trial, Simulation, Monte Carlo, Golden generation/revalidation, N expansion, main write, merge, Release, or historical evidence mutation occurred. Overall `BLOCKED_BEFORE_EXECUTION`.

## 2026-11-08 — Security, storage, environment, and owner-approval follow-up

- Model-source identity is now separate from the workflow/event HEAD. The exact candidate model-source commit is `ac0d009aa004976009ed01e97f96d019945e9ad6`; the workflow branch HEAD is separately pinned through protected environment variable `S6_EXECUTION_APPROVED_WORKFLOW_SHA`. S6 manifests record model `git_commit` and `workflow_head_sha` separately. C100 validates its checked-out model source.
- The manual execution workflow is owner-gated, uses a separate `execution-source` checkout, least-privilege read permissions, N=300 only, sequential fail-fast scenario execution, diagnostic-only partial artifacts, and no repository writes. It is not dispatchable until the workflow is present on the default branch and the protected environment is configured. It has not been dispatched.
- Runtime lock now contains 15 exact Linux x86_64 / CPython 3.11.18 wheel SHA-256 hashes. Hash-lock SHA-256: `074944b6a48090723f51a1f25e0d9dcf5e29f3a5df025b064bef485c2daa6fbf`. Safe CI regenerated all 15 hashes and matched the committed lock.
- Safe CI at branch HEAD `059ca9b6202b7cf02140a73f9d1bca9819e86856`: Run `42505862577`, success; 22 tests passed in 1.17s; compile checks passed; `SIMULATION_TRIALS=NOT_EXECUTED`.
- Gitleaks PR-diff scan found no leaks. Full reachable-history scan found nine unclassified `generic-api-key` findings. No secret values were emitted. Security remains blocked pending human classification and rotation of any confirmed live credentials. See `docs/experiments/SECURITY_STORAGE_ENVIRONMENT_REVIEW_2026-11-08.md`.
- One C100 reuse archive was fetched raw from OneDrive, restored, and ZIP-validated; its bytes matched Dropbox's provider content hash. This is scoped evidence only: Dropbox raw download and full-folder restore remain incomplete; storage is not PASS.
- Independent review remains pending. The review packet is `docs/experiments/INDEPENDENT_REVIEW_PACKET_2026-11-08.md`; it is explicitly not represented as an independent review.
- Conditional owner request is `docs/experiments/OWNER_FINAL_EXECUTION_APPROVAL_REQUEST_2026-11-08.md`. It asks for one initial checkpoint only: 20 S6 scenarios × 300 = 6,000 stochastic Trials and 5 C100 scenarios × 300 = 1,500 deterministic Trials, MASTER_SEED 20270101. No N expansion or final acceptance is authorized.
- The S6 aggregate still uses historical C100 reuse evidence; the new C100 Golden remains a separate evidence artifact and is not yet consumed by the S6 aggregate.
- No Trial, Simulation, Monte Carlo, Golden generation/revalidation, N expansion, main write, merge, Release, or historical evidence mutation occurred. PR #84 remains unmerged. Execution remains blocked.

## Final 2026-11-08 security and validation update

- Safe contract CI Run `42506231384` on workflow branch commit `d22257b46af426c6796d7e7d51a450b2ba708e55`: `success`; 23 tests passed in 1.26 seconds; 15 wheel hashes regenerated and matched; Python compilation passed; `SIMULATION_TRIALS=NOT_EXECUTED`. The later branch commits after this run are documentation-only.
- Security CI Run `42506266426` on workflow branch commit `e5d6a61e22c0cee0ef181735b01abea756b564ff`: PR-diff Gitleaks scan found no leaks; full reachable-history scan found 9 unclassified `generic-api-key` matches across 3,534 commits; no secret values were emitted. Security workflow remains failed/blocked on these findings.
- In the same security run, `pip-audit==2.10.1` on CPython 3.11.18 audited the exact 15-package hash lock and reported `No known vulnerabilities found`. The previous CPython 3.12/hash mismatch was corrected by explicitly setting up Python 3.11.18 in the security workflow.
- Storage remains `PASS_SCOPED` only for one OneDrive-restored C100 archive whose bytes matched Dropbox's server-side content hash. Dropbox raw download and full-folder restore are still outstanding.
- Operations guide: `docs/experiments/S6_EXECUTION_WORKFLOW_OPERATIONS_2026-11-08.md`.
- Independent review is still not performed by a different reviewer. The review packet remains a self-review/checklist, not independent approval.
- Owner approval request updated with the passing dependency audit; Gitleaks findings, independent review, protected environment setup, and full storage restore remain preconditions.
- No simulation workflow dispatch, Trial, Monte Carlo, Golden generation/revalidation, N expansion, merge, main write, Release, or final acceptance occurred.
