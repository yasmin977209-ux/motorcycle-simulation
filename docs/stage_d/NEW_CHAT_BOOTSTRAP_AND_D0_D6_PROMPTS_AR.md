# دليل استئناف محادثة جديدة وبرومبتات D0–D6
**تاريخ التثبيت:** 2026-10-31  
**المستودع:** `yasmin977209-ux/motorcycle-simulation`  
**فرع العمل الوحيد المصرح:** `tmp/cp-v240-stage-d-s6-deliverables-20261030`  
**HEAD عند إنشاء هذا الدليل:** `85875ea9f2595176052a9c3032e8f51ae432bcdf`  
**main عند الفحص:** `c6e54349a5e94f65d5aa9f83141f225d777bb474` — يجب إعادة التحقق دائماً.

هذا الدليل هو نقطة استئناف عملية. لا يثبت وحده نجاح أي بوابة، ولا ينسخ ملفات البيانات الثنائية. اقرأ ملفات الحالة الحية المشار إليها وأعد التحقق من GitHub قبل كل إجراء.

## 1. أول رسالة للمحادثة الجديدة (انسخها كما هي)

أنت تعمل على مشروع Motorcycle Simulation. اتصل بمستودع GitHub مباشرةً، ولا تطلب مني إعادة رفع ZIP أو ملفات سبق حفظها في المستودع.

المستودع: `yasmin977209-ux/motorcycle-simulation`  
فرع Stage D المصرح: `tmp/cp-v240-stage-d-s6-deliverables-20261030`  
الفرع `main` للقراءة فقط وممنوع تعديله. لا تنشئ PR أو Merge أو Release.

ابدأ بقراءة هذه الملفات من الفرع الحي، بهذا الترتيب:
1. `docs/stage_d/NEW_CHAT_BOOTSTRAP_AND_D0_D6_PROMPTS_AR.md` (هذا الدليل).
2. `docs/stage_d/STAGE_D_SESSION_STATUS_2026-10-31.md`.
3. `docs/stage_d/STAGE_D_CONTINUITY_HANDOFF_2026-10-31.md`.
4. `docs/stage_d/D0_REPOSITORY_CLOSURE.md` و`D0_REMOTE_EVIDENCE_LEDGER_2026-10-31.md` و`D0_INPUT_AUDIT.md` و`D0_INPUT_AUDIT.json`.
5. `docs/stage_d/D1_REPOSITORY_CLOSURE.md` و`D1_BUILDER_DESIGN.md` و`D1_BUILDER_AUDIT.json`.
6. `docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.md` و`D2_NUMBER_REGISTRY_AUDIT.json`.
7. `scripts/import_stage_d_sources.py` و`.github/workflows/stage-d-d1-d2-validation.yml`.
8. `docs/governance/D-2026-10-30-REFERENCE-V2.4.0.md` وملف المرجع المعياري الكامل إذا كان قد استورد.

ثم افحص GitHub API مباشرةً: رؤوس main وفرع العمل، شجرة الملفات، أحدث commits، كل Workflow runs على فرع Stage D، Artifacts، PRs، Releases. لا تعتمد على HEAD أو hashes مكتوبة في تقرير قديم دون إعادة القراءة.

الحالة الموثقة عند آخر فحص في 2026-10-31:
- D0: `COMPLETE / PASS_SCOPED_WITH_LIMITATIONS`، وليس قبولاً إنتاجياً شاملاً.
- D1: `BLOCKED / REPORTED_ONLY` حتى تُنشر ملفات المصدر والاختبارات منفردة ويعمل تحقق exact-head على GitHub.
- D2: `BLOCKED / REPORTED_ONLY` حتى يُنشر `results/number_registry.json` ويُعاد قراءته من GitHub.
- D3–D6: لم تبدأ.
- الفرع كان عند `85875ea9f2595176052a9c3032e8f51ae432bcdf`، وmain عند `c6e54349a5e94f65d5aa9f83141f225d777bb474`، وStage D runs = 0. أعد التحقق؛ هذه لقطة زمنية وليست ثوابت دائمة.

**قانون الإثبات الإلزامي:** لا تكتب PASS لأي ملف أو دليل إلا بعد وجود الثلاثية التالية لكل ملف:
(1) رابط GitHub للملف، (2) SHA-256 محسوبة من بايتات الملف التي أُعيد جلبها من GitHub بعد الإيداع، (3) commit SHA الذي يحتوي تلك البايتات. أضف Git blob SHA-1 وحجم الملف كحقول مساعدة. إذا غاب أي عنصر فالحالة `REPORTED_ONLY` ولا تفتح البوابة. لا تحسب SHA من نسخة محلية ثم تسميها remote SHA. لا تستخدم SHA قديمة بعد تعديل الملف.

**قاعدة الملفات المحلية:** لا تنشئ مخرجات محلية ثم تتركها خارج GitHub. الأفضل أن يتم البناء داخل GitHub Actions على الفرع المصرح، ثم commit/push، ثم remote readback، ثم exact-head tests. إذا تطلبت أداة التنفيذ ملفاً محلياً مؤقتاً، فيجب أن يكون ذلك ضمن job مؤقت وينتهي بإيداع الملف في نفس سير التنفيذ؛ وإلا سجّل المانع ولا تدّعِ الإيداع.

**قيد نقل المصدر لمرة واحدة:** توجد أداة استيراد منشورة `scripts/import_stage_d_sources.py`، لكنها لم تُشغّل حتى آخر حالة موثقة. وهي تحتاج إلى أربعة ZIPs موجودة محلياً لدى صاحب العمل لتستخرج ملفات النصوص والشفرة وتودع الملفات الفردية. موصل GitHub في جلسة ChatGPT لا يستطيع قراءة `/mnt/data` وتشغيل المستورد في clone محلي من تلقاء نفسه. لا تطلب مني إعادة إرفاق الأرشيفات إلى المحادثة. إذا لم تتوفر لك بيئة Work/Computer Use محلية موثوقة، أعطني خطوة واحدة فقط لتشغيل المستورد مرة واحدة من clone موثق، ثم استكمل تلقائياً من GitHub. بعد ذلك لا ينبغي تكرار رفع ZIPs في المحادثات المستقبلية.

لا تنفذ D1 أو D2 أو أي بناء قبل فحص الحالة الحالية والاعتماديات. لا تنتقل عبر بوابة لم تجتز. بعد فحص التأسيس، أعطني ملخصاً موجزاً لما قرأته فعلياً وما الذي يمنع التقدم، ثم انتظر برومبت المرحلة التالية مني.

## 2. ثوابت المشروع والهوية

- المرجع الحاكم الحالي بقرار المالك: v2.4.0، SHA-256 `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`؛ القرار `D-2026-10-30-REFERENCE-V2.4.0`، `APPROVED_BY_OWNER`، نافذ 2026-10-30. يجب استيراد نص المرجع الكامل ومطابقة بصمته قبل استخدامه كملف معياري.
- مرجع تنفيذ S6 التاريخي يبقى v2.3، SHA-256 `e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f`. لا تخلط historical execution reference مع current governing reference.
- v2.3.1 مغلق `CLOSED_UNAPPROVED_CANDIDATE` ولا يعاد تفعيله.
- S6: source `da1a9ea9b5cd789c944de3f07b08395bb67c49e7`، cohort `s6-v23-da1a9ea9`، seed `20270101`.
- C100: source `965281d52441cd0d4b744e211c9f68ee4cdc3753`، cohort `c100-v23-s4-20261026-965281d5`، تصنيف `CROSS_COHORT_DETERMINISTIC_REUSE`، ولا يعامل كتكرارات مستقلة لـS6.
- Stage 12/13 lineage منفصل: source `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`. لا تستخدم Stage 13 builder لإنتاج S6 ولا تغير lineage.
- Artifacts الثابتة الوحيدة لـD0/D1/D2:
  - Aggregate: Artifact `12852969854`, Run `40773412377`, SHA-256 `ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54`, 9,357,996 bytes.
  - Full Logging: Artifact `12998778418`, Run `41098699740`, SHA-256 `403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb`, 310,827,203 bytes.
  - C100: Artifact `12630457193`, Run `40263424595`, SHA-256 `c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79`, 361,733 bytes.
- نتائج التشغيل السابقة لا تتغير: Gate A المالي `PASS_SCOPED` فقط (80/80 pairs، 90,000 مقارنة، صفر اختلاف)؛ Gate A الإنتاجي `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`؛ Gate B عند N=2400 `FAIL_SCOPED` (10 PASS / 10 FAIL)؛ Stability `NOT_CONVERGED` (0/60)؛ N=4800 `NOT_EXECUTED`.
- الحقول المحاسبية الخمسة المفقودة تاريخياً: `Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Total_Assets`. لا backfill ولا افتراض صفر.
- Full Logging يخص 105 مفاتيح تمثيلية فقط: 125 role assignments، 105 unique keys (100 S6 + 5 C100)، 216,253 daily rows، 24,545,842 events، 1,297,518 roll-forward checks. لا تعممها على 48,000 Trial.
- كل النتائج تبقى `T2_INTERIM / NOT_FINAL_BLOCKED` حتى لو اكتملت D0–D6. لا تعلن FINAL_ACCEPTED أو P17_FINAL_ACCEPTED أو CONVERGED.

## 3. قواعد عمل لا يجوز خرقها

1. اقرأ المصدر الحي قبل أي تعديل؛ لا تستخدم ملفات مرفقة أو summaries بديلاً عن GitHub عندما يكون المصدر موجوداً.
2. لا تغيّر `main`، لا PR، لا Merge، لا Release.
3. لا Trial ولا Simulation ولا Monte Carlo ولا N=4800، ولا إعادة تشغيل C100 أو تجارب مكتملة.
4. لا تغير seed أو SOURCE_SHA أو cohort أو trial identity.
5. لا تعدل artifacts أو manifests التاريخية؛ أنشئ normalized/derived views منفصلة فقط.
6. لا تستخدم float في الحسابات المالية؛ استخدم int وFraction، ثم Decimal مع ROUND_HALF_EVEN للعرض.
7. لا تخترع بيانات أو أرقاماً أو صفوفاً لتعويض غياب مصدر. ميّز `MISSING_EVIDENCE` عن FAIL.
8. لا تعتمد على Stage 12/13 لتغطية فجوات S6.
9. لا تبدأ مرحلة لاحقة إذا كانت سابقتها BLOCKED أو REPORTED_ONLY.
10. بعد كل كتابة: commit على فرع العمل، fetch/readback من GitHub، احسب remote SHA-256 من البايتات المسترجعة، سجل URL + SHA-256 + commit SHA، ثم اختبر exact head. لا تعتبر push وحده كافياً.
11. إذا تعذر إيداع ملف أو تشغيل أداة، توقف وسجل السبب المحدد؛ لا تقل "تم" أو "PASS".
12. لا تحذف أو تستبدل تاريخاً سابقاً؛ صحح بإضافة سجل جديد مع الاحتفاظ بالقيم القديمة الموسومة superseded.

---

## 4. برومبت D0 — إعادة تثبيت المدخلات وإغلاق D0 فقط

ابدأ D0 فقط. افحص الفرع الحي وmain وHEADs وPRs وRuns وArtifacts وشجرة الملفات وقرارات الحوكمة. اقرأ سجل D0 وملفات الأدلة. أعد تنزيل Artifacts الثلاثة المثبتة من GitHub Actions، وتحقق من run metadata وtested SHA والحجم والـSHA-256 من ZIP bytes الفعلية، ثم ZIP CRC والعضويات والمسارات الآمنة والروابط الرمزية والتكرار. استخدم Parquet reader حقيقياً لفحص schema والصفوف والمفاتيح والحقول والأعداد والتعارضات إن كان ذلك متاحاً داخل GitHub Actions؛ لا تدّعِ فحص Parquet من مجرد ZIP CRC.

تحقق من:
- فصل S6 وC100 وStage 12/13.
- 125 role assignments و105 unique keys، منها 100 S6 و5 C100.
- عدم تحويل Full Logging للـ105 إلى دليل 48K.
- حقول الميزانية الخمسة المفقودة كما هي.
- حالة Gate A وGate B وStability وN=4800 دون ترقية.
- المرجع الحاكم v2.4.0 ومرجع تنفيذ S6 التاريخي v2.3 منفصلين.

المخرجات/التحديثات: `docs/stage_d/D0_INPUT_AUDIT.md`, `D0_INPUT_AUDIT.json`, `D0_REMOTE_EVIDENCE_LEDGER_2026-10-31.md`, `D0_REPOSITORY_CLOSURE.md`، وتحديث handoff/status عند الحاجة. لا تعِد كتابة أدلة قديمة دون سجل تصحيح.

إذا كانت ثلاثية URL + remote SHA-256 + containing commit غير موجودة لأي ملف، صنفه REPORTED_ONLY. أغلق D0 فقط ضمن نطاق سلامة الـ3 artifacts والـpreflight الموثق؛ لا تدّعِ قبول Gate A الإنتاجي أو اكتمال البيانات التاريخية. لا تبدأ D1 في هذا البرومبت.

## 5. برومبت D1 — S6 Builder مستقل ونشر المصدر

لا تبدأ D1 إلا بعد التحقق من D0 live.

الهدف: بناء S6 Builder/Adapter مستقل تماماً عن Stage 13، مع Shared Data Model واحد. اقرأ المصدر المحلي/الموجود بالفرع وقارن البايتات؛ توجد ثلاثة ملفات قديمة متعارضة مع المصدر المحلي:
- `scripts/s6_artifact_reader.py`
- `scripts/s6_deliverables_model.py`
- `scripts/s6_manifest_resolver.py`

لا تستبدلها دون حفظ نسخها القديمة في `docs/stage_d/archive/pre_import_conflicts/` وتوثيق SHA-256 لكل نسخة. استخدم المستورد المنشور إذا أمكن تشغيله بأمان من clone نظيف بعد التحقق من بصمات ZIP الأربعة. لا ترفع ZIP الحاوية نفسها؛ استخرج ملفات النص/الكود الفردية واحتفظ بأصلها ومكانها داخل الأرشيف في manifest الاستيراد.

تأكد من وجود ونشر الملفات الفردية المطلوبة:
- `scripts/s6_deliverables_builder.py`
- `scripts/s6_deliverables_model.py`
- `scripts/s6_artifact_reader.py`
- `scripts/s6_manifest_resolver.py`
- `scripts/s6_number_registry.py`
- `scripts/s6_validate_representatives.py`
- `tests/test_s6_deliverables_builder.py`
- `tests/test_s6_number_registry.py`
- `docs/stage_d/D1_BUILDER_DESIGN.md`
- `docs/stage_d/D1_BUILDER_AUDIT.json`
- `.github/workflows/stage-d-d1-d2-validation.yml`

احفظ أيضاً مرجع v2.4.0 المعياري كاملاً في `docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md` وتحقق من SHA-256 المطابقة تماماً. احفظ v2.3 تاريخياً وv2.3.1 في quarantine ولا تجعلهما مرجعين نافذين.

المنطق:
- LossCase = argmin(Final_Net_Project_Equity).
- MaxCase = argmax(Final_Net_Project_Equity)، دون اشتراط الإيجابية.
- لا تعِد اختيار الممثلين ولا تشغل Trials.
- Resolver يقرأ trial_manifest وpost_write_audit وrepresentative_full_logging_manifest، ويحفظ original status ويضيف normalized_audit_status منفصلاً.
- لا يمنح PASS_SCOPED إلا عند تطابق SHA والحجم وهوية source/cohort/trial وexpected/actual fingerprint ونجاح sidecar/root manifest.
- لا يعدل ملفات المصدر.
- Shared model يحمل provenance لكل قيمة، ويفصل S6 عن C100.

اختبر ZIP safety وidentity وmanifest resolver وcohort separation وexact arithmetic ورفض float. شغّل compileall وpytest على فرع Stage D فقط. أودع كل ملف نصي منفرداً ثم أعد قراءته من GitHub واحسب ثلاثيته. لا تكتف بحزمة ZIP محلية. D1 لا يغلق إلا بعد أن تكون كل الملفات المصدرية موجودة في GitHub، وتنجح اختبارات exact-head على commit محدد، ويكون تقرير الإغلاق نفسه ذا ثلاثية كاملة.

## 6. برومبت D2 — Number Registry والحسابات الدقيقة

لا تبدأ D2 إلا بعد D1 PASS مستند إلى ثلاثية GitHub وexact-head CI.

ابنِ `results/number_registry.json` من artifacts الثلاثة الثابتة وShared Data Model فقط. كل رقم يظهر في أي Excel أو DOCX لاحق يجب أن يكون له number_id واحد فريد وسجل provenance قابل للتتبع. لا تكتب أرقاماً يدوياً في القوالب.

لكل سجل، حسب الانطباق:
- number_id, metric_name, scenario_id
- source_artifact_id, source_run_id, source_member
- source_sha256, source_file_path, source_sha
- cohort_id, trial_id أو unique key
- numerator, denominator, exact_value, display_value
- unit, calculation_method, rounding_method
- N_total, N_closed, N_censored, N_unique_paths
- gate_status, evidence_status
- locator دقيق (member + row/key/column أو JSON pointer)

استخدم int للقيم الصحيحة، Fraction للنسب/المتوسطات/المئينات والفواصل، Decimal للعرض وquantize(Decimal("0.01"), ROUND_HALF_EVEN). امنع float في كل مسار مالي وفي JSON الناتج. إذا لم يوجد مقام، اذكر ذلك صراحة ولا تخترع مقاماً.

أثبت:
- Gate A المالي PASS_SCOPED فقط: 80/80 pairs و90,000 comparisons و0 mismatch.
- Gate A الإنتاجي NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS.
- Gate B N=2400 FAIL_SCOPED: 10 PASS / 10 FAIL.
- Stability NOT_CONVERGED: 0/60.
- N=4800 NOT_EXECUTED.
- Full Logging PASS_SCOPED للممثلين الـ105 فقط.

اختبر عدم تسرب float، numerator/denominator، rounding، deterministic recomputation، unique number IDs، complete provenance، cohort separation، no unregistered report numbers. وثّق الأرقام غير القابلة للاشتقاق والمصادر المفقودة دون zero-fill أو التخمين.

المخرجات: `results/number_registry.json`, `tests/test_s6_number_registry.py`, `docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.md` وJSON audit. commit ثم remote readback لكل ملف وثلاثيته. لا تفتح D3 حتى تنجح D2.

## 7. برومبت D3 — مصنفا Excel

لا تبدأ إلا بعد D2 PASS الموثق.

أنشئ من Shared Data Model وNumber Registry فقط:
- `deliverables/النتائج_الكاملة_AR.xlsx`
- `deliverables/Full_Results_EN.xlsx`

185 ورقة بالضبط في كل مصنف: 10 عالمية + 175 ورقة (25 سيناريو × 7 أوراق: STATS, DAILY, ASSETS, ACCTG, PARTNER, GUARANTEE, CONTRACTS). يجب أن تشمل الأوراق العالمية المطلوبة في المرجع، ومنها README وSCENARIO_MATRIX وVALIDATION_SUMMARY وREPRESENTATIVE_CASES وDAILY_DISTRIBUTION، واستكمل الأسماء العالمية العشرة من المرجع الكامل نفسه ولا تخمّن أسماء الخمس المتبقية.

املأ بيانات كل ورقة من مصادرها الفعلية فقط. سجلات Full Logging تغطي 105 unique keys و125 role assignments فقط؛ لا تستنتج سجلات تفصيلية للـ48K. أظهر missing evidence بوضوح. لا تستخدم Stage 13. افصل C100 وأظهر CROSS_COHORT_DETERMINISTIC_REUSE. العربية RTL والإنجليزية LTR، وأسماء الأوراق ASCII متطابقة ولا تتجاوز 31 حرفاً.

اعرض حالات المشروع بدقة: T2_INTERIM / NOT_FINAL_BLOCKED؛ Gate A المالي PASS_SCOPED؛ Gate A الإنتاجي NOT_DECLARED؛ Gate B FAIL_SCOPED؛ NOT_CONVERGED؛ N=4800 NOT_EXECUTED؛ C100 cross-cohort؛ فجوة الحقول المحاسبية الخمسة.

استخدم int/Fraction/Decimal فقط ولا float مالي. افحص القيم الرقمية في XML الداخلي للمصنف باستخدام Decimal لا float. افتح المصنفين من القرص بعد الحفظ، اختبر 185 ورقة لكل منهما، تطابق أسماء الأوراق، تطابق القيم الرقمية خلية بخلية، RTL/LTR، عدم float، السيناريوهات والصفوف والمجاميع ومصادر الأرقام. أضف اختبارات Stage D ولا تستخدم نتائج Stage C كبديل.

أودع المصنفين والاختبارات والتقارير على فرع Stage D في نفس سير التنفيذ. إذا تعذر إثبات محتوى ورقة، أظهرها ناقصة ولا تملأها تخميناً؛ لا تعلن D3 PASS. لا تبدأ D4 قبل بوابة D3.

## 8. برومبت D4 — خمسة تقارير DOCX

لا تبدأ إلا بعد D3 PASS.

أنشئ باستخدام python-docx:
1. `deliverables/التقرير_الكامل_AR.docx` (RTL)
2. `deliverables/Full_Report_EN.docx`
3. `deliverables/الملخص_AR.docx` (RTL، 2–3 صفحات)
4. `deliverables/Summary_EN.docx` (2–3 صفحات)
5. `deliverables/دراسة_الجدوى_AR.docx` (RTL)

كل رقم في المستندات يجب أن يأتي من `results/number_registry.json` عبر number_id. لا تكتب أرقاماً يدوياً. التقرير الكامل يتناول: ملخص المشروع، المنهجية، هوية المرجع، هوية S6 وC100، نتائج N=2400، الأدوار التمثيلية، Full Logging، المحاسبة، النتائج الإحصائية، Gate A/B، Stability، القيود، فجوات الأدلة، المخاطر والاستنتاج المرحلي.

الملخصان 2–3 صفحات ويعرضان الحالة التنفيذية وأهم النتائج والقيود وحالة القبول والخطوات التالية دون إيحاء بقبول نهائي.

دراسة الجدوى مبنية حصراً على REFERENCE_COMPLIANT_BASELINE. لا تضف تضخماً أو طلباً سوقياً أو أسعاراً أو تكاليف أو توقعات مبيعات أو بيانات اقتصادية من خارج النموذج. أدرج إفصاح §17.3 حرفياً/بالمعنى المعياري الدقيق كما في المرجع الكامل، ووضح أن النتائج مشروطة بافتراضات النموذج وليست توقعاً سوقياً مثبتاً. ضع T2_INTERIM / NOT_FINAL_BLOCKED على الغلاف وفي الخاتمة.

كل التقارير تظهر بوضوح حالات Gate A المالي/الإنتاجي، Gate B، Stability، N=4800، C100، وفجوة 48K. أنشئ مدققاً لاستخراج كل رقم من DOCX ومطابقته مع registry. افتح الملفات بعد حفظها وتحقق من RTL والصفحات والحقول والأرقام. commit ثم remote readback والثلاثية لكل DOCX. لا تبدأ D5 حتى D4 PASS.

## 9. برومبت D5 — Manifest وحزمة ZIP

لا تبدأ إلا بعد D3 وD4 PASS.

أنشئ `deliverables/manifest.json` مستقلاً، شاملاً:
- اسم الحزمة وإصدارها وتاريخ البناء.
- tested commit SHA والفرع.
- governing reference SHA-256 وhistorical execution reference SHA-256 منفصلين.
- S6 SOURCE_SHA/cohort/seed، C100 SOURCE_SHA/cohort وتصنيفه.
- Artifact IDs وRun IDs وبصمات المدخلات.
- بصمات وأحجام الأعضاء الثمانية.
- بصمة وحجم Number Registry الخارجي.
- نتائج الاختبارات وحالات البوابات والموانع والتعارضات المفتوحة.
- classification = T2_INTERIM / NOT_FINAL_BLOCKED.

أنشئ ZIP باسم `deliverables/delivery_bundle_v2.3.zip` ويحتوي 8 أعضاء بالضبط: ملفات التسليم السبعة (مصنفا Excel + خمسة DOCX) و`manifest.json`. لا تضع Number Registry أو SHA256SUMS داخل ZIP إلا إذا عدّل المرجع المعتمد ذلك صراحة؛ السجل يبقى خارجياً.

أنشئ `deliverables/SHA256SUMS.txt` خارج ZIP ويغطي ZIP وmanifest وكل ملفات التسليم الفردية و`results/number_registry.json`. احسب البصمات من الملفات الفعلية بعد الكتابة، لا من القوالب أو بيانات قديمة.

استخدم staging/atomic publication. اختبر العدد 8 بالضبط، عدم التكرار، عدم وجود مسارات غير آمنة، CRC، الأحجام، hashes، مطابقة manifest وSHA256SUMS. أعد فتح ZIP من القرص بعد إنشائه. لا تدّعِ Post-Write Audit المستقل في D5؛ هذا D6.

أودع الملفات وmanifest وZIP وSHA256SUMS على فرع Stage D. الملفات الثنائية يجب أن تُدفع عبر Git CLI داخل GitHub Actions أو آلية رفع موثقة، لا أن تُترك محلياً. احسب remote SHA-256 لكل ملف بعد readback وسجل commit. لا تبدأ D6 حتى D5 pass scoped.

## 10. برومبت D6 — التدقيق المستقل وإغلاق Stage D

لا تبدأ إلا بعد D5.

أنشئ `scripts/audit_s6_deliverables_bundle.py` كمدقق مستقل لا يستورد دوال التحقق الداخلية من Builder أو report_builder. افتح ZIP والمصنفات وDOCX من القرص/Artifact بعد البناء، وأعد قراءة كل عضو.

افحص:
- ZIP فيه 8 أعضاء بالضبط، CRC سليم، لا duplicate names ولا unsafe paths، الأعضاء المطلوبة كاملة.
- أحجام وSHA-256 لكل عضو مطابقة manifest وSHA256SUMS.
- المصنفان: 185 ورقة، أسماء وترتيب متطابقان، القيم الرقمية خلية بخلية، RTL/LTR، عدم float مالي، اكتمال بيانات السيناريوهات وإفصاح النقص.
- DOCX الخمسة: سلامة الملفات، RTL، الملخصان 2–3 صفحات، إفصاح §17.3، T2_INTERIM / NOT_FINAL_BLOCKED، عدم القبول النهائي، وكل رقم مطابق لـnumber_registry.
- source/cohort identity وفصل S6/C100 وlineage.
- Gate statuses لا تُرقّى.

نفّذ اختبارات Stage D: 175 (185 sheets + numeric equivalence)، 176 (report-number registry traceability)، 179 (manifest/hash/identity)، 180 (DAILY round-trip)، 181 (partner daily balances)، 182 (no float/exact arithmetic)، 183 (cohort separation)، 186 (8-member ZIP/readback). قبل التنفيذ اربط كل Test ID بالعقد الصحيح وسجل أي تعارض ترقيم مع Stage C دون تعديل سجل Stage C التاريخي. سجل PASS/FAIL/SKIPPED/NOT_RUN لكل اختبار، مع Run ID وJob ID وexact tested SHA.

شغّل workflow على فرع Stage D فقط. احفظ `docs/FINAL_AUDIT.md` وJSON audit و`docs/PROJECT_CONTINUITY.md` (إضافة زمنية لا محو تاريخي)، وارفع GitHub Actions Artifact نهائياً مع Run/Artifact IDs. أعد قراءة الملفات النهائية من GitHub واحسب SHA-256 من remote bytes وسجل URL + SHA-256 + commit SHA لكل ملف. اختبر exact final head بعد آخر commit، ولا تعتبر اختبار commit سابق اختباراً للرأس النهائي.

حتى لو نجح D6، الحكم هو `T2_INTERIM / NOT_FINAL_BLOCKED` أو `PASS_SCOPED_WITH_LIMITATIONS` للتسليم المرحلي فقط. لا FINAL_ACCEPTED ولا P17/P18 ولا CONVERGED ولا PR/Merge/Release.

## 11. بروتوكول التنفيذ بين البرومبتات

أرسل البرومبت الأول وحده، وانتظر فحص التأسيس. ثم أرسل D0، وبعد تقريره ومراجعته D1، ثم D2، ثم D3، ثم D4، ثم D5، ثم D6. لا ترسلها دفعة واحدة ولا تسمح للوكيل بتجاوز بوابة. إذا كانت المرحلة BLOCKED، أرسل طلب إصلاح للمانع المحدد فقط، ولا تنتقل للمرحلة التالية.
