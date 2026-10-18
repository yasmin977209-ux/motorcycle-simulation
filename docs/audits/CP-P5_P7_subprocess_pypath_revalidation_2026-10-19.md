# CP-P5/P7 — مراجعة دليل إصلاح subprocess وPYTHONPATH — 2026-10-19

## الحكم

**CANDIDATE_FIX_HAS_SUCCESSFUL_EVIDENCE; MAIN_NOT_VERIFIED; PR_NOT_MERGED.** الدليل الحي يوضح أن PR #45 يحتوي إصلاحًا موجّهًا لمسار استيراد العملية الفرعية، وقد اجتاز Run مرشحًا ناجحًا. لا يُنقل الحكم إلى main ولا تُغلق الحاجة إلى قبول منفصل على الرأس الحالي.

## الهوية الحية والروابط

- `main` HEAD: `647c19826b90d8224ce73ef9b90c306a45e03fb0`.
- PR #45: مفتوح / Draft / غير مدمج، base `main` عند الرأس المذكور، head الفرعي الحالي `23a99404ee000c14e2d24de42ccb053076833dfd`.
- الفرع: `tmp/p7-subprocess-pypath-20261016-clean`.
- المسار الوحيد في PR #45: `tests/test_monte_carlo_round2.py`.
- Blob ملف الاختبار على رأس PR الحالي: `640ca1bedca5dbd04aa6e1177e63ddf0fde7297e`.
- Run التاريخي الناجح: [38950047414](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/38950047414), tested SHA `57dec56428779452979b4f7d22b29e07fceeebae`, Job `117138844807`, Artifact `12067742973` (`p7-subprocess-verification-evidence`, 2,613 bytes).
- فرع الاستمرارية قبل هذا التقرير: `tmp/cp-session-continuity-20261017` عند `cef28e498ed8233447a720a3a4e422428949d2ea`. PR #46 مفتوح Draft وغير مدمج.

## الفرق بين رأس التشغيل ورأس PR الحالي

رأس PR الحالي `23a99404ee000c14e2d24de42ccb053076833dfd` هو commit واحد بعد SHA المختبر `57dec56428779452979b4f7d22b29e07fceeebae`. مقارنة GitHub تثبت أن الفرق الوحيد هو حذف `.github/workflows/p7-subprocess-verification-360.yml` من الفرع النهائي. ملف الاختبار المعدل له Blob SHA نفسه على الرأسين، لذلك إصلاحه نفسه موجود في النسختين. مع ذلك، تشغيل الاختبارات كان مربوطًا بـSHA الأقدم، ولا يجوز وصفه بأنه Run على رأس PR الحالي حرفيًا.

الـWorkflow المؤقت المستخدم في التشغيل التاريخي كان يضبط `timeout-minutes: 360`. لقد حُذف من رأس PR الحالي، ولم يُعد تشغيله في هذه المراجعة. لا يُعد هذا الـWorkflow جزءًا من المقترح النهائي الحالي ولا يجوز إعادته أو اعتماده دون R4 وموافقة مستقلة.

## التغيير محل التحقق

في `_run_hashseed` أضاف المرشح جذر المشروع إلى `PYTHONPATH` للعملية الفرعية، مع الاحتفاظ بالقيمة الموجودة إن وجدت. هذا يعالج سببًا محتملًا قويًا لفشل استيراد `monte_carlo` في سكربت فرعي مخزن تحت `/tmp`.

النتائج الحرفية من سجل Job التاريخي:

- الاختبارات المركزة: `5 passed in 22.84s`.
- المجموعة الكاملة: `379 passed, 1 skipped, 1 warning in 426.33s (0:07:06)`.
- نتيجة الـRun: `success`.
- قبل pytest بنى الـWorkflow fixtures مؤقتة لـStage 5، وتحقق من هويتها؛ كما سجل صراحة أنها fixtures لا checkpoint إحصائي ولا cohort إنتاجي.
- الاختباران المركّز والكامل شُغّلا في هذا الـRun مع `PYTHONPATH` الموروث غير مضبوط؛ ومع ذلك احتوى اختبار subprocess إصلاحًا يحدد مسار المشروع للابن.

## علاقته بإخفاق P5 التاريخي

Run P5 الأقدم `38656654259` كان على candidate SHA مختلف، ونتيجته الحرفية `5 failed, 416 passed, 1 skipped, 1 warning`. أربع حالات من الفشل كانت بسبب عدم إنشاء `results_stage5/` قبل pytest؛ والخامسة subprocess. Run P7 اللاحق يختلف في إعداده: بنى fixtures أولًا واحتوى إصلاح PYTHONPATH؛ ولذلك يوفر دليلًا إيجابيًا مرشحًا لكلا المسارين، لكنه لا يمحو الإخفاق التاريخي ولا يثبت أن main الحالي اجتاز الاختبارات.

## R4 / الحكم والقيود

| العنصر | الحكم |
|---|---|
| إصلاح subprocess / PYTHONPATH | `K_CODE/K_TEST` candidate fix مع دليل Run ناجح على tested SHA معلوم؛ قبول PR الحالي لم يتم. |
| fixtures | المسار fixture-first اجتاز المجموعة في Run P7؛ لا يستبدل ذلك قبول head الحالي أو بيانات حقيقية عندما يتطلب معيار القبول دليلًا إنتاجيًا. |
| صلاحية الدليل | strong candidate evidence, not main evidence. فرق SHA محصور في حذف Workflow مؤقت، وBlob ملف الاختبار متطابق؛ سجّلت ذلك بدل إخفاء فرق tested SHA. |
| صلاحيات التغيير | PR يعدل tests؛ وفق تعليمات المشروع، لا تُدمج أو يُعتمد تغيير الاختبار تلقائيًا دون الموافقة الصريحة المطلوبة. |
| حدود التشغيل | هذا التقرير لا يشغّل أو يعيد Run؛ لم يحدث pytest/CLI/Monte Carlo/Trial/Checkpoint جديد. لا تغييرات على main أو state.json أو SOURCE_SHA أو seed/RNG أو البيانات أو Golden coverage. |

## الخطوة التالية

الحصول على موافقة مالك صريحة بشأن قبول تغيير `tests/test_monte_carlo_round2.py` في PR #45. بعد الإذن فقط، تُراجع R4 النهائية وملفات الاختبارات المتغيرة وسلامة عدم إدراج Workflow الـ360 دقيقة؛ لا دمج/إغلاق PR تلقائيًا. تبقى كل نتائج الـRun مقيدة بـtested SHA `57dec56428779452979b4f7d22b29e07fceeebae` ولا تُنسب إلى main.
