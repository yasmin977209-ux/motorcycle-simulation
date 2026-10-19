# CP-R4-TIMEOUT-PARALLELISM-FAIL-CLOSED — تنفيذ المرشح ومتبقي الحفظ الدائم — 2026-10-19

## الحالة التنفيذية

**PARTIAL / NOT READY TO MERGE.** نُفذت تغييرات Workflow والاختبارات على فرع مرشح مستقل، لكن شرط الحفظ الدائم لدفعات Parquet لم يكتمل؛ لذلك لا يصح وصف الحزمة بأنها مكتملة أو آمنة للاستئناف بعد حد المنصة. لا تُدمج.

## التفويض والنطاق

وافق المستخدم صراحة على تنفيذ CP-R4-TIMEOUT-PARALLELISM-FAIL-CLOSED على فرع مرشح فقط، مع عدم تغيير main أو SOURCE_SHA أو master_seed أو RNG أو البيانات/Trial IDs أو القواعد الإحصائية، وعدم تشغيل Monte Carlo أو Trial أو Checkpoint أو Workflow إنتاجي، وعدم دمج PR أو إنشاء Release.

## الهوية

- Repository: yasmin977209-ux/motorcycle-simulation
- Base main HEAD: 647c19826b90d8224ce73ef9b90c306a45e03fb0
- Main state.json blob: 2178260bb18efeb81437486f13b6d10cf5e85936
- source_sha: f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b
- state stage/status: 12-CLOSED / FINAL_DELIVERY_BLOCKERS_OPEN
- Candidate branch: tmp/cp-stage7-timeout-parallelism-20261019
- Candidate HEAD after final read-back: ac8abcb3ae4bba7b5bb33d88026917881d0e704a2
- Workflow blob: f673adca6d4a6db240a1b08ce3cb84ddc7881821
- Test blob: b73f0cce6d543014b1391f86111dc775dd747cae
- GitHub compare: ahead_by=5, behind_by=0; only .github/workflows/stage7-full-run.yml and tests/test_stage7_authoring.py changed.

## تغييرات المرشح التي تمت قراءتها مجددًا

1. إزالة JOB_TIMEOUT_MINUTES=40 وتمريره إلى orchestrator، وإزالة فرع الإنهاء المبكر الذي كان يكتب final_status=timeout بعد 40 دقيقة.
2. ضبط matrix-simulation.timeout-minutes إلى 360، أي سقف منصة فعلي وليس تشغيلًا بلا حد.
3. ضبط max-parallel إلى 25 مع الإبقاء على قائمة السيناريوهات الـ25 وfail-fast=false.
4. استخدام مفتاح concurrency مشترك بحسب github.ref مع cancel-in-progress=false.
5. إضافة شرط fail-closed بعد كتابة summary.json: النجاح لا يحدث إلا إذا كانت هناك 25 حالة بالضبط، وكل حالة final_status=stable وfinal_stats_included=true ولها trial count وبصمة، وstable_count=25 وtimeout_count=error_count=0. خلاف ذلك يطبع STAGE7_FAIL_CLOSED ويرجع exit code 1.
6. تحديث tests/test_stage7_authoring.py لتختبر غياب الحد الداخلي، وسقف 360، وmax-parallel=25، ومجموعة التزامن المشتركة، وفشل الملخص عند عدم اكتمال الحالات.

## R4: فجوة الحفظ الدائم — مانع صريح

المراجعة تؤكد أن scripts/stage7_run_trial_block.py يكتب Parquet وmetadata محليًا. أما scripts/stage7_state.py فيحفظ حالة JSON على فرع stage7-state/<scenario> ولا يحفظ ملفات Parquet. يرفع Workflow مجلد blocks كـArtifact في خطوة لاحقة بعد انتهاء orchestrator.

عند بلوغ سقف 360 دقيقة أو إلغاء المهمة من المنصة، قد لا تكون ملفات Parquet قد رُفعت. عند الاستئناف، validate_trial_sequence يقارن Trial IDs المحلية مع completed_trials المخزنة؛ ومن المفترض أن يفشل عند غياب البيانات بدل إعادة حسابها بصمت، لكن هذا ليس مسار استئناف مكتملًا. لذلك:

- إزالة الحد الداخلي والتوازي 25 مطبقان في المرشح، لكن الحفظ الدائم لكل دفعة قبل اعتمادها لم يُنفذ.
- لا ندعي أن التقدم يمكن استعادته تلقائيًا بعد انقطاع عامل التشغيل.
- لا ندعي نجاح الاختبارات؛ لم يتمكن الفحص المحلي من clone المستودع بسبب تعذر DNS إلى github.com. لم يُشغّل Pytest أو YAML parser أو Workflow.
- هذه الفجوة مانع K_CODE / MISSING_EVIDENCE. أقل إصلاح تالٍ: تصميم وتطبيق نقل/استرجاع دائم للدفعات مع تحقق SHA-256 وmetadata وهوية source/scenario/Trial IDs/fingerprint، ثم اختبارات تستعيد دفعة محفوظة وتثبت الفشل المغلق عند فقدها أو عدم تطابقها. لا تشغيل إنتاجي ضمن هذا النطاق.

## الثوابت وعدم التنفيذ

- لم تتغير main أو state.json أو المرجع أو SOURCE_SHA أو master_seed أو RNG أو sampling/cohort/Trial IDs أو القواعد الإحصائية أو البيانات التاريخية/Parquet.
- لم يُشغّل Monte Carlo أو Trial أو Checkpoint أو CLI أو Workflow.
- tested_sha=NOT_RUN؛ run_id=NONE؛ artifact_id=NONE.
- لم يُفتح PR جديد ولم يُدمج أو يُغلق أي PR ولم يُنشأ Release.
- لا تزال بوابات المشروع السابقة مفتوحة، ومنها GATEA_PROVIDER_MISSING وSOURCE_SHA_DRIFT وUNDEFINED_BUSINESS_RULE وغياب scripts/stage13_assemble.py وفجوات التسليم والحوكمة.

## الحكم والخطوة التالية

**PARTIAL — DO NOT MERGE.** استكمال مسار الحفظ الدائم واختباراته على الفرع المرشح هو الخطوة التالية. لا تُعد هذه الحزمة جاهزة للدمج أو للتشغيل الإنتاجي قبل ذلك، حتى مع بقاء فشل الاستئناف مغلقًا عند غياب الملفات.
