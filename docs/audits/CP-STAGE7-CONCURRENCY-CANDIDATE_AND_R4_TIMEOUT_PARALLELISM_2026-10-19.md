# CP-Stage 7: إصلاح التزامن على مرشح + R4 للمهلة والتوازي — 2026-10-19

## الحكم التنفيذي

- **إصلاح التزامن الموافق عليه:** نُفِّذ على فرع مرشح مستقل، ثم قُرئت الملفات المعدلة مرة أخرى من GitHub. الاختبار: NOT_RUN؛ لم يُشغَّل Workflow.
- **إلغاء حد 40 دقيقة، ورفع التوازي من 10 إلى 25، وتغيير مهلة المهمة، والتحقق النهائي fail-closed:** لم تُعدّل بعد. هذا التقرير يقدّم R4 منفصلًا للحزمة لأن حذف المهلة بلا استبدال آمن للحفظ والاستئناف قد يفقد مخرجات أو يسمح بتصنيف تشغيل غير مكتمل كنجاح.
- لم يحدث تشغيل Monte Carlo أو Trial أو Checkpoint أو CLI. لا تغيير إلى main أو state.json أو SOURCE_SHA أو master_seed أو RNG أو البيانات التاريخية/Parquet أو sampling أو cohort أو Trial IDs أو القواعد الإحصائية. لم يُفتح PR جديد ولم يُدمج أي PR.

## الهوية الحية والأدلة

- المستودع: yasmin977209-ux/motorcycle-simulation.
- main HEAD / base: 647c19826b90d8224ce73ef9b90c306a45e03fb0.
- main/state.json blob: 2178260bb18efeb81437486f13b6d10cf5e85936؛ stage=12-CLOSED؛ repository_status=FINAL_DELIVERY_BLOCKERS_OPEN؛ source_sha=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b؛ sha_semantics=parent_state_commit_pointer.
- PR #46 ما زال OPEN / DRAFT / UNMERGED، base main عند SHA أعلاه، ورأس فرع الاستمرارية tmp/cp-session-continuity-20261017 عند 1881c3c02d990ab4a2192061418ef5ad24611b9b قبل هذا التقرير.
- فرع المرشح: tmp/cp-stage7-shared-concurrency-20261019، أُنشئ من main عند 647c19826b90d8224ce73ef9b90c306a45e03fb0.
- Commit تعديل Workflow: 0af3ad310857578fe733c208884ef0767055c431؛ Workflow blob بعد التعديل: 1e8bc05f357e74a2fb06fe2e0a68279bdf2ad1a2.
- Commit تعديل الاختبار ورأس الفرع الحالي: f08b1da2357680d5b29655d9bad875e131e15dfc؛ test blob بعد التعديل: a71b2e93873f4eadc1068fa169b4aad2725a4bd5.
- مقارنة GitHub تؤكد أن المرشح متقدم باثنين commits عن base ومن دون commits متأخرة عن base، والمساران المتغيران فقط هما .github/workflows/stage7-full-run.yml وtests/test_stage7_authoring.py.

## ما نُفِّذ في نطاق الإذن الحالي

| العنصر | قبل | بعد | نتيجة القراءة الراجعة |
|---|---|---|---|
| مفتاح concurrency في Workflow | stage7-full-run مع github.run_id | stage7-full-run مع github.ref | المفتاح الجديد موجود، والمفتاح القديم غير موجود. cancel-in-progress: false بقي كما هو. |
| اختبار test_stage7_workflow_has_concurrency_guard | يثبت حرفيًا المفتاح الفريد لكل Run | يتوقع المجموعة المشتركة بحسب github.ref ويتحقق من غياب github.run_id داخل إعداد concurrency | نص الاختبار الجديد موجود في القراءة الراجعة. |

هذه القراءة الراجعة تثبت محتوى الفرع، وليست نتيجة Pytest أو YAML parser. تعذّر تشغيل نسخة محلية لأن محاولة clone لم تستطع حل github.com (network/DNS unavailable في بيئة التنفيذ)، كما لم يُطلق أي Workflow عن قصد؛ الفرع لا يطابق فرع محفّز Stage 7 full-run.

**اختبار CP:** NOT_RUN؛ tested_sha=NOT_RUN. لا تنقل أي PASS إلى main.

## R4 — نطاق المهلة والتوازي وسلامة الاكتمال

| العنصر | الحالة الحالية والدليل | الحكم / أقل إصلاح مقترح | الحالة |
|---|---|---|---|
| الحد الداخلي | JOB_TIMEOUT_MINUTES=40 يُمرر إلى الموجّه. عند بلوغ 40 دقيقة يكتب final_status=timeout، يستبعد النتائج من الإحصاءات النهائية، ويحفظ الحالة ثم يخرج. | لا يُحذف هذا الحد بمفرده؛ إنه مسار خروج منظم يتيح لخطوات الرفع اللاحقة أن تعمل. يجب استبداله بحدود حفظ/استئناف موثوقة قبل إلغائه، لا بمجرد إزالة المتغير أو فرع if. | K_CODE / R4_REQUIRED |
| الحد الخارجي للمحاكاة | matrix-simulation.timeout-minutes=45. فحص الزمن الداخلي يحصل بين دفعات الإحصاء؛ تنفيذ دفعة trial block نفسها متزامن حتى نهايتها. | قد تبدأ دفعة طويلة قبل بلوغ الحد الداخلي ثم تتجاوز 45 دقيقة؛ عند قتل المهمة من المنصة لا يمكن افتراض أن خطوات الرفع اللاحقة ستنشر الملفات المحلية. يلزم تقسيم التنفيذ إلى دفعات حفظ محددة، واستمرار موثق لنفس هوية البيانات، وإتاحة استئناف لا يعيد IDs المكتملة. | K_CODE / R4_REQUIRED |
| حفظ واستئناف Parquet | all_results() يقرأ ملفات results_stage7/<scenario>/blocks محليًا؛ ملفات Parquet تُرفع كـArtifact في خطوات لاحقة بعد انتهاء الموجّه. الحالة البعيدة تحمل completed_trials وnext_trial_id وبصمة، لكن ليس محتوى Parquet نفسه. | يجب أن تُحفظ كل دفعة Parquet مكتملة بصورة دائمة قبل اعتبار تقدمها محفوظًا، ثم تُطابق البصمة وتسلسل Trial IDs مع الحالة. لا نعلن أن إزالة المهلة آمنة حتى يثبت هذا المسار. | K_CODE / MISSING_EVIDENCE |
| عدد السيناريوهات المتزامنة | 25 سيناريو فريدًا في المصفوفة، وfail-fast=false، لكن max-parallel=10. | رفع حد المصفوفة إلى 25 للسماح بأن تكون السيناريوهات الـ25 مؤهلة للتنفيذ المتوازي، من دون تغيير قائمة السيناريوهات أو عدد التجارب أو قواعدها. عدد العاملين الفعلي قد يبقى أقل حسب حصة التزامن في خطة GitHub وتوفر العاملين. | K_CODE / R4_REQUIRED |
| استقلال العشوائية والمخرجات | rng.py يشتق المفتاح من master_seed وscenario_id وtrial_id وbike_id وdate وevent_type. لكل سيناريو فرع حالة stage7-state/<scenario> ومجلد نتائج results_stage7/<scenario>/blocks. | التوازي بين السيناريوهات لا يحتاج تعديل سياسة RNG أو seed؛ يجب فقط إبقاء العزل والتحقق من الهوية والتسلسل والبصمات كما هي. | SOURCE REVIEWED؛ لم يُنفذ تشغيل |
| إعلان النجاح | final-report يحسب stable_count وtimeout_count وerror_count ويطبع الملخص، لكنه لا يحتوي بعد الملخص على شرط واضح يفشل المهمة إذا لم تكن جميع السيناريوهات مستوفية للقبول. وبعض حالات الحجب/المهلة تنهي الموجّه بخروج صفري. | أضف تحققًا fail-closed: لا ينجح Stage 7 ولا يُعلن اكتمالها إلا إذا كانت الحالات الـ25 مقبولة جميعًا وبأدلة هوية/نتائج مكتملة؛ أي timeout أو blocked أو failed أو error أو Artifact ناقص يمنع النجاح. هذا لا يغيّر قواعد الاستقرار الإحصائي؛ بل يمنع اعتبار عدم الاكتمال نجاحًا. | WORKFLOW_DEFECT / R4_REQUIRED |
| مهلات الوظائف المساعدة | preflight-gates وfinal-report لكل منهما timeout-minutes=15، ويوجد انتظار محدود لإلغاء تشغيل قديم. | الاقتراح هو إبقاء مهلات وظائف المساعدة القصيرة ما دامت لا توقف حساب السيناريو، لأنها تمنع تعليق الإعداد/التقرير إلى ما لا نهاية؛ تعديلها لا يلزم لتحقيق الغرض الحالي. | KEEP |
| سلوك طابور Workflow | المجموعة المشتركة الافتراضية تحتفظ بتشغيل نشط واحد وتشغيل معلّق واحد؛ التشغيل الأحدث قد يستبدل الأقدم المعلّق. | هذا خاص بتشغيل نسخ Workflow؛ لا يمنع تشغيل السيناريوهات الـ25 بالتوازي داخل نفس التشغيل. إن كان المطلوب حفظ كل نسخة من كل push في طابور، فذلك اختيار منفصل لم يُفترض هنا. | PENDING_POLICY_IF_NEEDED |

## حدود المنصة المتحقق منها

توثيق GitHub الحالي يذكر حدًا يصل إلى 6 ساعات للمهمة على GitHub-hosted runners، و35 يومًا للتشغيل، كما أن سقف التزامن يعتمد على الخطة (الجدول المنشور: Free=20، Pro=40، Team=60، Enterprise=500 مهمة متزامنة لعوامل standard hosted). خطة الحساب الحالية غير معروفة في هذا الفحص؛ لذلك max-parallel=25 يتيح 25 مهمة لكنه لا يضمن أن 25 عاملًا ستبدأ فعليًا في اللحظة نفسها.

- https://docs.github.com/en/actions/reference/limits
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#concurrency

## نطاق التنفيذ المقترح بعد الإذن المحدد

**CP-R4-TIMEOUT-PARALLELISM-FAIL-CLOSED** على فرع مرشح منفصل فقط:

1. وضع تصميم حفظ/استئناف متين لدفعات Parquet المنجزة مع تحقق الهوية (SOURCE_SHA/master_seed/RNG/sampling/stability policy/schema/scenario/Trial IDs/fingerprint) قبل اعتبارها تقدمًا محفوظًا.
2. إضافة سجلات تقدم واضحة بعد كل دفعة محفوظة: السيناريو، نطاق Trial IDs، العدد المكتمل، الهدف الإحصائي التالي، البصمة وحالة Gate؛ وتسجيل stdout/stderr والأخطاء دون إخفائها.
3. بعد إثبات حدود الحفظ، استبدال حد 40 دقيقة الذي ينهي العمل باكرًا بآلية تجزئة/استئناف آمنة، مع ضبط حد المهمة الطويلة عند سقف المنصة المعتمد (360 دقيقة على hosted runner) لا الادعاء بأنها بلا سقف منصة.
4. جعل max-parallel=25 مع الحفاظ على قائمة السيناريوهات الـ25 وfail-fast=false.
5. تعديل الاختبارات المتأثرة لتثبت: لا حد داخلي يوقف المحاكاة قبل إتمام دفعة آمنة؛ حد المنصة مضبوط بوضوح؛ التوازي 25؛ عزل البيانات وRNG ثابت؛ نتائج timeout/blocked/failed/error أو نقص Artifact لا يمكن أن تمر كنجاح.
6. اختبارات ساكنة/وحدات على المرشح فقط. لا Workflow تشغيل كامل، ولا Monte Carlo إنتاجي، ولا Trial/Checkpoint جديد ضمن CP التعديل. تبقى حدود GitHub الفعلية نافذة.

**يتطلب هذا النطاق R4 وموافقة منفصلة قبل تعديل الملفات المحمية مرة أخرى.** لا ينبغي الموافقة على حذف JOB_TIMEOUT_MINUTES وحده أو تغيير max-parallel وحده دون مسار الحفظ/الاستئناف وfail-closed أعلاه.

## البوابات وما لم يتغير

- GATEA_PROVIDER_MISSING، SOURCE_SHA_DRIFT، UNDEFINED_BUSINESS_RULE، غياب scripts/stage13_assemble.py، عدم اكتمال ملفات التسليم، فجوة الحوكمة، وG2_RISK لم تُحل بهذا الإصلاح.
- لا إثبات تشغيل: tested_sha=NOT_RUN، run_id=NONE، artifact_id=NONE.
- لا تغيير main أو state.json أو المرجع أو seed/RNG أو sampling/cohort/Trial IDs أو البيانات التاريخية/Parquet. لا PR جديد أو merge أو Release.

## الخطوة التالية

طلب إذن محدد لنطاق CP-R4-TIMEOUT-PARALLELISM-FAIL-CLOSED قبل أي تعديل إضافي للـWorkflow أو الاختبارات. يظل فرع التزامن المرشح منفصلًا ولا يُدمج تلقائيًا.
