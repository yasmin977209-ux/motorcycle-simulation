# CP-P8 — جرد CLI والبيئة (قراءة فقط)

**التاريخ:** 2026-10-18 (Asia/Aden)
**المستودع:** yasmin977209-ux/motorcycle-simulation
**النمط:** جرد مصدر/عقد CLI فقط؛ لم يُشغّل CLI أو pytest أو Workflow أو Trial أو Checkpoint أو Monte Carlo.
**الحكم:** جرد المصدر مكتمل ضمن النطاق المقروء؛ قابلية إعادة إنتاج البيئة غير مثبتة من ملفات الجذر وحدها.

## 1. الهوية الحية وخط الأساس

- رأس main المقروء مباشرة من GitHub: 647c19826b90d8224ce73ef9b90c306a45e03fb0.
- main/state.json blob: 2178260bb18efeb81437486f13b6d10cf5e85936؛ stage = 12-CLOSED؛ repository_status = FINAL_DELIVERY_BLOCKERS_OPEN؛ source_sha = f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b؛ state.sha_semantics = parent_state_commit_pointer.
- docs/STATE_SHA_SEMANTICS.md blob: 134363f0f2834f8087760b3148910a1a3d3af38b.
- فرع الاستمرارية tmp/cp-session-continuity-20261017 وصل إلى e4279d2a75c89be073a8b9eacc090fe812c3449e عند الفحص؛ PR #46 ما زال Open / Draft / unmerged، وقاعدته main عند 647c19826b90d8224ce73ef9b90c306a45e03fb0.
- استُخدم الرأس الحي والملفات الحالية؛ لا تُنقل نتائج فروع المرشحين إلى main.

## 2. عقد CLI في run_batch.py

الملف على main هو blob 0418ddea818c194a5b582df94778fa5f13a3ecc4.

الوسائط المعروفة من تعريف build_parser:
- --scenario: مطلوب.
- --trials: مطلوب؛ موصوف بأنه عدد التجارب الإضافية، مع تحقق أن القيمة موجبة.
- --output-dir: مطلوب.
- --start-trial-id: افتراضي 1، ويتحقق أن القيمة لا تقل عن 1.
- --resume-from-checkpoint: علم صريح لاستئناف حالة Stage 7 من stage7-state/<scenario>.
- --master-seed: افتراضي constants.MASTER_SEED.
- يطبق parser سياسة C100 التي تتطلب تجربة واحدة.

في main يُمرر SOURCE_SHA من متغير البيئة إلى run_batch. ويشترط run_batch وجود SOURCE_SHA؛ إذا لم يصل من الوسيط، يُقرأ من البيئة، وإذا بقي فارغًا يحدث ValueError برسالة SOURCE_SHA must be supplied by environment. مسار الاستئناف يتطلب GITHUB_REPOSITORY وGH_TOKEN ويُفشل برسالة resume requires GITHUB_REPOSITORY and GH_TOKEN إذا غاب أحدهما.

تنبيه تشغيلي: تشغيل CLI بوسائط فعلية يستدعي run_batch ويمكن أن ينفذ Trials ويكتب مخرجات/حالة. لذلك اقتصر هذا CP على قراءة المصدر؛ لم تُجرّب حتى --help أو أي استدعاء تنفيذي.

## 3. التبعيات وإعادة الإنتاج

requirements.txt على main هو blob 81131ac1437fc652ceff21831570ce19de314b78، ومحتواه:

- pytest>=9,<10
- numpy>=2.3,<3
- pyarrow (بدون حد إصدار)
- python-dateutil>=2.9,<3
- scipy>=1.17,<2
- pyyaml (بدون حد إصدار)
- openpyxl>=3.1,<4

المخزون الجذري الحالي لا يتضمن pyproject.toml أو setup.cfg أو ملف قفل للتبعيات أو ملف .python-version؛ وقد أعاد فحص pyproject.toml وsetup.cfg نتيجة 404. لم يُثبت هذا الجرد إعداد Python الفعلي المستخدم في CI؛ ذلك يحتاج مراجعة مستقلة لملفات Workflows في CP-P9. تبعيات pyarrow وpyyaml غير مثبتة برقم إصدار محدد هنا، وبقية القيود نطاقات، لذلك requirements.txt وحده لا يكفي لإعادة بناء بيئة حرفية قابلة للتكرار.

## 4. فروق وموانع ظاهرة ذات صلة

- SOURCE_SHA_DRIFT مؤكد من المصدر: daily_engine.py على main blob 0d17d1923fbf95ba7f3e4b6ae695bfbf80f85964، أما الملف عند المرجع المربوط إلى SOURCE_SHA = f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b فblob 6c4496c3e9a9b41668c3d93063ad31d96df5f878. المحتويان مختلفان؛ أول اختلاف سطري في القراءة الحالية عند السطر 137، ولا يجوز تحديث SOURCE_SHA أو خلط البيانات دون قرار/تحقق الهوية المطلوب.
- scripts/stage13_assemble.py غير موجود على main (فحص الملف رجع 404)، ويتوافق ذلك مع مانع MISSING_ARTIFACT في main/state.json. هذا لا يثبت عدم وجود نسخة مرشحة على فرع آخر.
- PR #45 ما زال Open / Draft / unmerged من الرأس 23a99404ee000c14e2d24de42ccb053076833dfd إلى main. ملفه الوحيد tests/test_monte_carlo_round2.py بإضافة PYTHONPATH إلى subprocess. هذه مراجعة اختبارات، ولا تُدمج أو تُعدّل دون R4 وموافقة صريحة محددة لتغيير الاختبارات.
- README.md على main يذكر .github/workflows/stage7-gates.yml، لكن هذا الملف غير موجود ضمن قائمة Workflows الحالية المقروءة؛ يجب حسم هذا الانحراف في CP-P9، لا بتعديل وصف أو Workflow في هذا CP.
- يوجد Artifact مرتبط بتشغيل مرشح Stage 13 رقم 39044148534، اسمه stage13-production-integration-evidence-39044148534، وحجمه 34,628 بايت. لم يُحمّل محتواه أو يُفحص في CP-P8؛ لا يُعتبر اسم Artifact أو نجاح Run برهانًا على قبول إنتاجي.

## 5. R4 وحدود التنفيذ

| العنصر | الحالة الحالية | المرجع/الدليل | الحكم |
|---|---|---|---|
| عقد CLI | run_batch.py blob 0418ddea… | قراءة تعريف parser وmain/run_batch | VERIFIED من المصدر؛ لم يُشغّل |
| SOURCE_SHA | main يمرر متغير بيئة مطلوبًا؛ main daily_engine يختلف عن الملف عند SOURCE_SHA | state.json وblob المصدرين أعلاه | K_CODE/K_SPEC identity blocker قائم؛ لا تحديث تلقائي |
| تبعيات البيئة | requirements.txt بنطاقات/تبعيات غير مثبتة تمامًا | blob 81131ac… وغياب ملفات القفل من الجذر | قابلية الإعادة الكاملة PENDING حتى يكتمل فحص CI/التبعيات |
| استئناف checkpoint | يتطلب GITHUB_REPOSITORY وGH_TOKEN ويقرأ حالة Stage 7 | run_batch.py | عقد المصدر VERIFIED؛ لا توجد محاولة استئناف |
| إصلاح PR #45 | تغيير tests فقط في Draft غير مدمج | PR #45 ومحتوى patch المقروء | APPROVAL_PENDING؛ لا تعديل/دمج |
| Stage 13 assembler | غير موجود على main | 404 لملف scripts/stage13_assemble.py | BLOCKED على main |
| README مقابل Workflows | README يشير إلى stage7-gates.yml غير موجود في قائمة main الحالية | README blob 08d666… وقائمة Workflows الحالية | ملاحظة للمراجعة في CP-P9 |

## 6. ما لم يحدث

- لم يُشغّل CLI أو pytest.
- لم يُشغّل Workflow أو Run جديد، ولم يُنشأ Trial أو Checkpoint أو Monte Carlo.
- لم تُنزّل Artifacts في هذا CP؛ محتوى Artifact 12104968606 غير مفحوص هنا.
- لم تتغير الملفات أو البيانات أو seed/RNG/SOURCE_SHA أو الاختبارات أو Workflows أو state.json أو main.
- لا يوجد ادعاء بأن البيئة قابلة للإعادة بالكامل، أو بأن أي بوابة أصبحت PASS.

## 7. الخطوة التالية

CP-P9: جرد مستقل قراءة فقط لملفات Workflows الحالية على main، بما يشمل إصدار Python، تثبيت التبعيات، أوامر pytest، إعداد fixtures، مهلات الوظائف، permissions، متغيرات البيئة، branch/ref pins، رفع Artifact، ومقارنة تعريفات README بالملفات الموجودة. لا تُجرى تعديلات على Workflows أو الاختبارات إلا بعد R4 وموافقة مالك محددة. بعد P9، استمر في فحوص CP-SOURCE/Gate A والهوية، ثم أصلح فقط العيوب التقنية المستقلة المصرح بها مع إبقاء البوابات المحجوبة منفصلة.
