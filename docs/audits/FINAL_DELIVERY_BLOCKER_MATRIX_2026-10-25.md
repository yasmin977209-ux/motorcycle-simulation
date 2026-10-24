# مصفوفة إغلاق موانع التسليم — 2026-10-25

**الحالة:** BLOCKED_FOR_FINAL_ACCEPTANCE
**main:** c6e54349a5e94f65d5aa9f83141f225d777bb474 — لم يُعدّل.
**فرع العمل:** owner-approved-delivery-preparation-20261025 — مرشح غير مدمج.
**بوابة التنفيذ على main:** docs/stage7/statistical_execution_gate.json = BLOCKED_FOR_IMPLEMENTATION.
**قاعدة:** لا تُرفع حالة أي مانع لأن توثيقه اكتمل؛ يلزم الدليل المحدد أدناه.

## مصفوفة الموانع والاعتماديات

| الترتيب | المانع | الحالة المثبتة | العمل المطلوب | دليل الإغلاق المقبول | ما لا يجوز فعله قبل الإغلاق |
|---|---|---|---|---|---|
| P0 | سلطة المرجع وهوية المرجع | SHA-256 للمرفق 297fb4c445bcce20fdd66a02d65aea00c74007d2f3d7c68ead416a5822fd5582 يختلف عن SHA-256 في بوابة الإنتاج ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479. | قرار حوكمة صريح يحدد المرجع الحاكم ويربط التعديلات المعتمدة دون استبدال صامت. | سجل قرار معتمد، وبصمة مرجع قابلة لإعادة الحساب، وربط واضح لكل تعديل نافذ. | لا تشغيل إنتاجي أو اعتماد قواعد متعارضة قبل الحسم. |
| P0 | تغيير RNG وهوية المصدر الجديد | تصحيح نطاق البذرة مرشح على هذا الفرع واجتاز اختبارات RNG؛ السلوك مختلف عن المصدر التاريخي وGolden التاريخي مربوط بالمصدر السابق. | مراجعة مستقلة للفرق، وتسمية مصدر مرشح جديد، وخطة Golden متوافقة مع المصدر الجديد وفصل cohort القديم عن الجديد. | Source SHA جديد مثبت، اختبارات الهوية/المطابقة، وقرار صريح لإعادة استخدام البيانات. | لا دمج، ولا إعادة وسم النتائج التاريخية، ولا استخدام Golden القديم لإثبات صحة RNG الجديد. |
| P0 | صلاحية الاستدلال المالي تحت التوقف المتكيف (K_SPEC) | بوابة المتوسط تستخدم Student-t نقطياً؛ لا توجد طريقة مقبولة صالحة لكل الأوقات، ولا برهان دعم محدود أو افتراض كمي معتمد للذيل/العزوم. | إما إثبات حد دعم/أفق نهائي من الثوابت والمسارات القانونية، أو طلب افتراض ذيل/عزوم كمي مبرر ومراجع؛ ثم دمج طريقة صالحة للتوقف المتتابع واختبارها مستقلاً. | مذكرة رياضية موقعة، واختبارات تغطية/توقف، وتنفيذ متصل بالمسار الفعلي، ومراجعة مستقلة. | لا إعلان استقرار، ولا اعتبار نجاح اختبار وحدة بديلاً عن برهان الاستدلال. |
| P0 | عدم إثبات انتهاء المسار في حالة PREP ناقصة التمويل | run_deterministic_trial يعمل حتى simulation_stopped دون حارس تاريخي؛ الإغلاق يمنع وجود أي دراجة PREP. المسار الخصومي الاصطناعي لم يثبت أنه reachable أو unreachable من التهيئة القانونية. | برهان reachability/عدم الوصول من create_initial_project، أو قرار تجاري منفصل يحدد معالجة العجز/التصفية عند تعذر التمويل، ثم اختبار exact-source. | برهان أو قرار مالك محدد، واختبارات انتقال/عدم تقدم، وأدلة ضمن النطاق المصرح به. | لا إضافة تاريخ إغلاق أو timeout اعتباطي؛ لا تغيير دلالات الإغلاق لمجرد إنهاء المحاكاة. |
| P0 | تغطية Gate A الذهبية غير مكتملة | الخريطة تغطي 25 سيناريو و25,205 بصمة؛ التوليفات غير C100 حتى N=1200، والتوسعة إلى N=2400 متاحة فقط لـC030_G030. | بعد حسم هوية المصدر/البذرة/RNG والحوكمة، اعتماد خطة تغطية دقيقة لكل نقاط التوقف المطلوبة. | Golden موثّق لكل مصدر/سيناريو/Trial ID، تحقق provenance، واختبارات fail-closed على exact HEAD. | لا Trial/checkpoint عند نقطة غير مغطاة، ولا توليد مرجع ذهبي من البيانات التي يجري تقييمها. |
| P0 | الانتقال التاريخي الفاشل | C030_G030 / P90_Final_Cash عند N=300→600 سجّل تغيراً نسبياً 1.5715059335%، متجاوزاً شرط أقل من 1%؛ الحالة FAILED_NOT_REQUALIFIED. | إبقاء الفشل مسجلاً، ثم إعادة تأهيله باستخدام الطريقة الإحصائية المعتمدة وتوافق المصدر والبيانات. | تقرير انتقال قابل لإعادة الإنتاج يحقق جميع شروط Gate A/B وقاعدة التوقف، أو حكم صريح باستمرار الفشل. | لا يمحو نجاح انتقال لاحق الفشل السابق ولا يتجاوزه مجرد رفع N. |
| P1 | مكونات المقاييس الاحتمالية والمئينات | طرق quantile وBernoulli المرشحة غير موصولة بالمسار الإنتاجي؛ مصدر/اكتمال P90_Held_Assets واختباره المتكامل ناقصان. | ربط كل مقياس بمصدر بيانات وهوية cohort، ودمج طريقة استدلال/حدود دقة صالحة للفحص المتكرر، مع شروط رفض مغلقة. | اختبارات fail-closed للمقاييس المطلوبة، ومطابقة استخراج مستقلة، واكتمال Trial IDs. | لا قبول صامت لمقياس مفقود أو استخدام صفر/قيمة بديلة. |
| P1 | Stage 10: المصدر وfidelity والوقت التشغيلي | source_identity=PARTIAL وfidelity=PARTIAL وtopology_status=NOT_DEFINED_IN_CURRENT_REPOSITORY؛ 470 ثانية كأبطأ benchmark تاريخي لا يثبت زمن المحاكاة التكيفية الكاملة. | تحديد حدود ما قيس فعلاً، استكمال مطابقة المصدر، وقياس عبء التشغيل الكامل بعد إذن إنتاجي صالح. | Benchmark مكرر على workload معتمد، وتوثيق بيئة/حزم/ذاكرة، وحدود زمن آمنة مع حفظ checkpoint. | لا اعتبار Stage 10 PASS دليلاً على اكتمال المصدر أو runtime الحالي. |
| P1 | مصدر الأرقام التفصيلية في Excel/Stage 13 | المصنف التشخيصي بـ185 ورقة يطابق 11,005 TrialResults و22,546,465 صفاً يومياً، لكنه NOT_FINAL_BLOCKED وتوجد أقسام تفصيلية غير متاحة في cohort التشخيصي. | بناء ملفات التسليم من cohort مقبول يتضمن مصادر الأصول والعقود والمحاسبة والشركاء والكفالة، ثم إعادة فتح كل ملف وفحصه مستقلاً. | سبعة ملفات AR/EN مع manifest.json، وبصمات وفهرس أرقام موحد، وصفر خلايا خطأ، واختبارات محاسبية وتوافق لغتين. | لا تسمية المصنف التشخيصي كتسليم نهائي لأن عدد أوراقه صحيح فقط. |
| P1 | نطاق الاختبار مقابل القبول الإنتاجي | على candidate HEAD `37e2a7f8fa4b622c9ddd65ccbb1bcfa7878cfe91` نجحت pytest للمستودع كله: 517 passed, 1 skipped؛ مجموعة القبول 162 passed, 1 skipped؛ ومجموعة الارتدادات 164 passed, 1 warning. أُنشئت fixtures اختبارية مؤقتة لـ127 و159–161 في runner فقط. | بعد أي تعديل جديد، أعِد تشغيل كامل الاختبارات على exact final HEAD؛ ثم افصل نتيجة الاختبارات عن قرار الإنتاج والإحصاء والقبول. | CI كامل على SHA التسليم، سجل K_TEST/skip مصرح به، وحزمة مخرجات خضعت لمراجعة مستقلة. | لا تعتبر fixtures الاختبارية cohort رسمياً، ولا تعتبر pytest PASS بمفرده Gate A/B أو P17/P18 PASS. |
| P1 | الواقعية التجارية | لا توجد بيانات تشغيلية موثقة عن التحصيل الفعلي، فراغ الأسطول، الصيانة، التأمين، الكفالة، التمويل، أو إعادة البيع. | جمع بيانات محلية قانونية ومجهّلة، ثم إنشاء إصدار منفصل معاير زمنياً واختباره خارج العينة. | مصدر/تغطية بيانات، معايرة موثقة، فحص معايرة، اختبار فترة مستقلة، وموافقة مالك. | لا اختلاق معاملات أو إدخال التضخم/أسعار عامة مباشرة كثوابت محلية. |
| P0 | P17/P18 والإصدار | P17=NOT_ACCEPTED وP18=BLOCKED — no Release؛ عدد Releases الحية صفر. | إعادة تدقيق مستقلة على الحزمة الكاملة بعد إغلاق الموانع السابقة. | P17 جديد يقبل الحزمة وP18 يتغير إلى قابل للإصدار بناءً على الأدلة، ثم موافقة إصدار مستقلة. | لا دمج ولا tag ولا Release أو نشر. |

## الترتيب التنفيذي الصحيح

1. حسم المرجع الحاكم وقرار هوية RNG الجديد؛ لا يمكن إثبات Golden/نتيجة جديدة ضد مواصفة غير محسومة.
2. حسم فرضيات انتهاء المسار/العزوم واعتماد طريقة الاستدلال المتكيف؛ لا تبدأ cohort إنتاجياً قبل قبول Gate B.
3. اعتماد خطة Golden تغطي مصادر/Trial IDs المطلوبة وإعادة تأهيل الانتقال الفاشل وفق المنهج المقبول.
4. استكمال اختبارات المجموعة كاملة ومصادر الحقول المالية وقياس زمن التشغيل المعتمد.
5. بناء حزمة AR/EN من cohort مقبول واحد مع manifest.json، ثم مراجعة مستقلة P17/P18.
6. دراسة الواقعية ببيانات محلية فعلية كنسخة منفصلة؛ لا تخلطها بالنسخة المرجعية المطابقة.

## حالة التنفيذ الراهنة

- إصلاح RNG candidate-only: منفذ واختباراته المحددة ناجحة.
- Preflight حتمي للقبول والبوابات وExcel/Stage13: ناجح ضمن النطاق الموضح في تقرير Owner-approved delivery preparation.
- بيانات المعايرة الواقعية: لم تُقدّم سجلات تشغيلية محلية؛ تمت كتابة نموذج الحقول وقواعد المعايرة فقط.
- إنتاج Monte Carlo/Trial/checkpoint/Golden جديد: لم يتم، لأن بوابة main لا تسمح به.
- main: دون تغيير. PR #77: مسودة غير مدمجة.
- الحكم: CANDIDATE_PROGRESS_CONFIRMED / FINAL_DELIVERY_BLOCKED.

## تحديث نتائج الاختبارات — 2026-10-25

تم سد فجوة fixtures الاختبارية دون استخدام بيانات إنتاج: منشئ `tests/build_stage5_acceptance_fixtures.py` يعمل في runner مؤقت فقط. على HEAD `37e2a7f8fa4b622c9ddd65ccbb1bcfa7878cfe91`، GitHub Actions أظهر `517 passed, 1 skipped` للمستودع كله، `162 passed, 1 skipped` لمجموعة القبول، `164 passed, 1 warning` للارتدادات الحتمية، و`114 passed` لاختبارات Stage 7 candidate methods. هذه النتائج لا تغير حالة `K_SPEC`, Gate A, Golden coverage, P17/P18 أو صلاحيات الإنتاج.


## تصحيح إضافي بعد مراجعة المرجع — حساب رمية التحصيل

أظهر التدقيق في §14.3 من المرجع المرفق أن فرع المرشح كان يستعمل مقارنة `float` (`rng_draw(seed) < collection_probability`) في قرار التحصيل، في حين ينص المرجع على المقارنة الصحيحة الدقيقة `u * 100 < pct * 2**64`. أُصلح ذلك في المرشح بإضافة `draw_success` على أعداد صحيحة وإبقاء `rng_draw` لأغراض التشخيص فقط، مع اختبار حدّ 50% واختبارات 0%/100% ورفض النسبة غير الصحيحة. هذا يُعد تغييراً إضافياً في سلوك المصدر المرشح؛ لذلك يعزّز ضرورة source identity وGolden جديدين متوافقين، ولا يسمح بإعادة تسمية النتائج التاريخية.

كما عُدلت دوال فحص دقة فواصل §2.5 لتقبل المساواة مع حد الدقة (`<=`) وفق حد القرار المعتمد، مع الإبقاء على شرط التغير الاحتمالي المتتابع strict (`< 0.005`). النتائج تظل candidate-only إلى أن يجتاز CI على الرأس الجديد ومراجعة مستقلة؛ حالة Gate A/B وP17/P18 لا تتغير.


## تدقيق هوية العشوائية لكل تكرار — تنفيذ مرشح

أُضيف إلى المرشح سجل مستقل لكل تكرار: `rng_checksum` يساوي مجموع القيم ذات 53 بتاً (من أعلى 53 بتاً للكتلة ذات 64 بتاً المستخدمة في الرمية) بترديد `2**64`، مع عداد سحوبات. لا تُسجَّل رمية عند الاحتمالين المحسومين 0% و100%. تظل بصمة النتائج المالية مستقلة عن حقول التدقيق، وتُنشأ بصمة منفصلة تربط تدقيق RNG بالمصدر والبذرة الرئيسية والسيناريو ومعرّف التكرار. فحص المرشح يرفض الحقول غير الصحيحة أو عدم وجود رميات في السيناريو العشوائي أو تكرار checksum غير صفري (`DUPLICATE_SEED_DETECTED`). تُشترط بصمة تدقيق متطابقة عند استئناف checkpoint.

هذه الإضافة لا تغيّر `main` ولا البيانات التاريخية أو بصمات Golden؛ كما أنها تجعل أي checkpoint قديم بلا هوية تدقيق صريحة غير قابل للاستئناف بصمت. لم يُعلن القبول الإنتاجي؛ يلزم أن يجتاز التغيير اختبار CI كامل على رأسه الجديد، وأن تُعتمد هوية المصدر الجديدة وخطة Golden/البيانات المتوافقة.


## RNG audit end-to-end contracts — candidate code path only

The current candidate now separates the financial `fingerprint_sha256` from the RNG audit identity across these paths:

- `run_batch.py` binds `rng_checksum_fingerprint_sha256`, the master seed, and the explicit audit schema in checkpoint identity; resume validation rejects missing/mismatched audit identities and duplicate nonzero checksums.
- Stage 7's `scripts/stage7_run_trial_block.py` captures the checksum per logical trial, persists it to Parquet, and stores a separate checksum-map fingerprint and seed/schema in block metadata. The Stage 7 workflow validates restored blocks and binds the audit fingerprint into its state artifact identity.
- Stage 10 benchmark trials capture the same checksum while preserving financial per-trial hashes, and write a source/seed-bound checksum fingerprint for canonical new blocks.
- Stage 13 adaptive summaries now require the exact finance-plus-audit row schema and verify a separate ordered `rng_audit_map_sha256`. The financial `result_sha256` deliberately excludes audit columns; a checksum-map mismatch or repeated nonzero checksum fails closed. Synthetic-only regression tests cover map tampering and duplicate checksums.

This is a code/schema integration change, not proof that the historical 11,005-trial cohort possesses valid checksums. Historical TrialResult blocks produced before this change cannot be backfilled with zero checksums or relabeled as audited. Any stochastic trial lacking the new audit fields remains blocked until independently generated under a newly reconciled source identity. No production trials, Golden extensions, or canonical dataset writes were run.

The v2.1 reference hash reconciliation, K_SPEC/time-uniform inference, Gate A coverage, source/data provenance, realism calibration, PREP reachability, Stage 10 workload/fidelity, and P17/P18 acceptance blockers remain unchanged.
