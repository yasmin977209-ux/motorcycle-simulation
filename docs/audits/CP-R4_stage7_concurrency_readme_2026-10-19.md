# CP-R4 — تحليل مخاطر Stage 7 وتصحيح مرجع README — 2026-10-19

## الحكم التنفيذي

**R4_READY_FOR_SCOPED_OWNER_APPROVAL; NO WORKFLOW/TEST CHANGE PERFORMED.** هذا تقرير مراجعة وتحديد أقل إصلاح، وليس موافقة تنفيذ أو نتيجة اختبار. لا تعديل للكود أو الاختبارات أو Workflows أو README في هذه الـCP.

## الهوية الحية والنطاق

- المستودع: yasmin977209-ux/motorcycle-simulation.
- `main` HEAD: 647c19826b90d8224ce73ef9b90c306a45e03fb0؛ لم يتغير.
- `main/state.json` blob: 2178260bb18efeb81437486f13b6d10cf5e85936؛ `stage=12-CLOSED)، `repository_status=FINAL_DELIVERY_BLOCKERS_OPEN)، `source_sha=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`، ودلالة `state.sha=parent_state_commit_pointer`.
- فرع الاستمرارية: `tmp/cp-session-continuity-20261017` عند 63f497dda1b0d1a12191d49baea87a596c8ff73a قبل الكتابة.
- PR #46: OPEN / DRAFT / UNMERGED؛ base `main` عند 647c19826b90d8224ce73ef9b90c306a45e03fb0؛ الرأس قبل الكتابة 63f497dda1b0d1a12191d49baea87a596c8ff73a.
- أدلة هذا R4: README blob `08d666bff504609fc26acb4523c25812c61fac6e`; `.github/workflows/stage7-full-run.yml` blob `4bb3b8df6742f51087b45eed1b9200468f12ac60`; `tests/test_stage7_authoring.py` blob `6a4e11399e2c6b85e9dc240a0c669f395a639e66`; الملف المؤرشف `docs/legacy-workflows/stage7-gates.yml.disabled` blob `1ce89868fe844397ff1c5b00c7b189cf5650b81a`.
- لم تُشغّل أي Workflow أو pytest أو CLI أو Monte Carlo أو Trial أو Checkpoint؛ `tested_sha=NOT_RUN`.

## R4 — الأدلة، النص الحاكم، الحكم، وأقل إصلاح مقترح

| العنصر | الحالي والدليل المباشر | المرجع/النص الحاكم | الحكم وأقل إصلاح مقترح |
|---|---|---|---|
| مفتاح GitHub concurrency | `stage7-full-run.yml`: `group: stage7-full-run-${{ github.run_id }}`; `cancel-in-progress: false`. كل Run جديد يحمل `run_id` مختلفًا. | [GitHub Actions concurrency docs](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#concurrency): التقييد يطبق على التشغيلات التي تشترك في المجموعة نفسها؛ افتراضيًا يوجد تشغيل معلّق واحد فقط، ويستبدل الأحدث المعلّق السابق ما لم تهيّأ قائمة انتظار مختلفة. | `WORKFLOW_DEFECT / RISK` على مستوى التصميم: إعداد concurrency نفسه لا يحقق التنافي المتبادل بين Runs مختلفة لأن مفتاح المجموعة فريد لكل Run. أقل تعديل مرشح: جعل المجموعة ثابتة لكل فرع/Workflow، مثل `stage7-full-run-${{ github.ref }}`، مع إبقاء `cancel-in-progress: false`. هذا يمنع التشغيلين المتوازيين على الفرع؛ لكن الافتراضي يسمح بانتظار واحد فقط وقد يستبدل Run معلّقًا أقدم بآخر أحدث. تغيير هذا السلوك يحتاج اختيارًا صريحًا إذا كان المطلوب حفظ كل push في queue. |
| حارس preflight اليدوي | ضمن `preflight-gates` يستعلم عن Runs غير المكتملة لفرع `tmp/stage7-full-run-20261004`، ويلغي أي Run غير الحالي، ثم ينتظر حتى 90 محاولة × ثانيتين قبل الفشل. | النص في Workflow: `select(.conclusion == null)`, طلب `actions/runs/${run_id}/cancel`, سجلات `CANCELLED_STALE_RUN` و`STALE_RUN_STOPPED`، ثم حد `STALE_RUN_CANCELLATION_TIMEOUT`. | توجد محاولة حماية فعلية ولا يصح وصف Workflow بأنه بلا حراسة إطلاقًا. لكنها ليست قفلًا ذريًا: يمكن لتشغيلين يبدأان معًا أن يريا بعضهما في قائمة Runs ويحاولا إلغاء بعضهما. المفتاح الثابت يكمّل هذه الحماية. لا يوجد Run جديد لإثبات وقوع race فعلي، لذا الحالة RISK وليست ادعاءً بإخفاق تشغيلي مشاهد. |
| اختبار عقد concurrency | `tests/test_stage7_authoring.py::test_stage7_workflow_has_concurrency_guard` يطلب حرفيًا `stage7-full-run-${{ github.run_id }}`؛ فلا يختبر سلوك منع التزامن، بل يثبت النص الحالي نفسه. | سياسة المشروع تتطلب R4 ثم موافقة صريحة مستقلة قبل تغيير tests/Workflows. | `K_TEST / WEAK_ASSERTION` مرشح: عند إصلاح المفتاح سيحتاج الاختبار إلى تعديل صريح يقبل المفتاح المشترك الصحيح ويرفض المفتاح الفريد لكل Run، من دون تشغيل workflow. لا تعديل للاختبار ضمن هذا R4. |
| مهلة Stage 7 | الثوابت: `JOB_TIMEOUT_MINUTES: "40"`; `matrix-simulation.timeout-minutes: 45`، مع تعليق يذكر خمس دقائق لحفظ الحالة ورفع Artifact. | `main/state.json` blocker `G2_RISK`: المخاطرة المسجلة هي وظائف تتجاوز 35 دقيقة، والجدول المصحح لم يُقَس بمحاكاة Monte Carlo إنتاجية. اختبارات authoring تثبت القيم 40/45 حاليًا. | `G2_RISK / PENDING`: توجد مخاطرة معروفة، لكن لا يوجد دليل مدة يبرر تغيير الأرقام. **التوصية: لا تغيير لحدّي 40/45 في هذه الـCP**. يلزم لاحقًا قياس مخول ومرتبط برأس وRun ومخرجات، مع موافقة تشغيل منفصلة؛ لا تُستخدم تجربة جديدة لتقدير المدة دون تصريح محدد. |
| مرجع README للبوابات الأربع | `README.md` يقول إن `.github/workflows/stage7-gates.yml` يحتوي أربع بوابات. هذا المسار غير موجود في قائمة ملفات `.github/workflows` النشطة (24 ملفًا). لكن نسخة قديمة موجودة باسم `docs/legacy-workflows/stage7-gates.yml.disabled`. | الاسم `.disabled` وموقع `legacy-workflows` يدلان على أرشفة لا تشغيل؛ وتظل القائمة الحية هي المرجع في تحديد الملف النشط. | `DOC_DEFECT / VERIFIED`: الصحيح ليس أن الملف غير موجود في أي مكان، بل إنه **غير موجود كـWorkflow نشط في المسار المشار إليه**؛ توجد نسخة مؤرشفة/معطّلة. أقل إصلاح مستقل: توضيح أن الأربع بوابات وصف تاريخي للـWorkflow المؤرشف، وإدراج أسماء ومسارات الملفات الحالية من دون الادعاء بأنها تنفذ الأربع بوابات القديمة. يمكن إصلاح README على فرع مرشح دون تعديل main. |
| حدود المحفز | `stage7-full-run.yml` يحفَّز بـpush إلى `tmp/stage7-full-run-20261004` فقط. | إعداد المحفز الفعلي في أول الملف. | عند أي تعديل مصرح للـWorkflow يجب العمل من فرع مرشح لا يطابق اسم فرع التشغيل هذا، كيلا يؤدي دفع تغييرات المراجعة إلى تشغيل محاكاة طويلة تلقائيًا. لا تُستخدم الفرع المطابق لرفع patch أو توثيق. |

## أدلة خارجية حول دلالة concurrency

يوضح توثيق GitHub الحالي أن المجموعة المشتركة تمنع أكثر من Run واحد من العمل في الوقت نفسه؛ وبشكل افتراضي يوجد Run معلّق واحد، ويلغي Run جديد المعلّق السابق ويحل محله. المصدر: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#concurrency. أما الاستنتاج أن مفتاحًا يحتوي `github.run_id` فريد لكل Run فهو استنتاج مباشر من صيغة الإعداد وهوية كل Run، وليس نتيجة تشغيل.

## أقل نطاق تنفيذ لاحق مقترح — ينتظر الموافقة الصريحة

1. **README فقط** (مستقل ومنخفض المخاطر): تصحيح الإحالة القديمة مع حفظ وصفها التاريخي وتوثيق مسارات Stage 7 الحالية. معيار القبول: لا يدّعي README وجود Workflow نشط بالمسار القديم، ولا يوحي أن authoring workflow ينفذ بوابات المحاكاة الأربع.
2. **Workflow + test** (يتطلبان إذنًا صريحًا): استبدال مفتاح concurrency الفريد لكل Run بمفتاح مشترك للفرع/الـWorkflow، وتحديث اختبار العقد ليختبر خاصية التنافي لا حرفية الإعداد الخاطئ. معيار القبول الساكن: YAML صالح؛ الاختبار يرفض مفتاحًا مبنيًا على `github.run_id` ويقبل مفتاح المجموعة المشترك؛ لا Run طويل ولا Trial في تحقق CP التعديل المحدود. يُنفذ على فرع مؤقت لا يطابق trigger التشغيل.
3. **المدة** (لا يُغيّر الآن): إبقاء 40/45، وتظل `G2_RISK` مفتوحة حتى تتوفر أدلة أداء مصرح بها. لا أخلط إصلاح concurrency بإذن تشغيل Monte Carlo.

### نقطة القرار المطلوبة للعمل المحمي

هل توافق صراحةً على تعديل `.github/workflows/stage7-full-run.yml` و`tests/test_stage7_authoring.py` على فرع مرشح غير مشغّل، بالنطاق المحدد في البند (2) فقط؟ لا يشمل الإذن تعديل `main` أو تغيير SOURCE_SHA أو البذرة/RNG أو بيانات/Trial/Golden أو تشغيل محاكاة طويلة أو دمج PR.

## حالة المشروع بعد R4

لم يتغير `main` أو `state.json` أو README أو test أو Workflow أو مصدر المحاكاة أو البيانات؛ لم يتغير SOURCE_SHA أو master_seed/RNG أو sampling أو cohort أو trial IDs؛ ولم تُنشأ Run/Job/Artifact/Release. Gate A وGate B و§2.5/IUT والتسليم النهائي تبقى بالحالة المسجلة في `main/state.json`، ولا يوجد PASS جديد.
