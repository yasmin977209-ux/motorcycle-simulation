# مكتبة البرومبتات التشغيلية — Motorcycle Simulation
## GitHub-First | النسخة المحدثة 2026-11-01

> هذه المكتبة تنظّم أوامر الاستعادة والتنفيذ والتدقيق. لا تنشئ قاعدة أعمال، ولا تمنح صلاحية غير ممنوحة، ولا تستبدل المرجع الحاكم أو قرار المالك. عند التعارض تكون تعليمات المشروع وقرار المالك والمرجع الحاكم v2.4.0 أعلى سلطة من أي نص في هذه المكتبة.

## 0. خط الأساس الحي الذي بُنيت عليه هذه النسخة

تم التحقق من GitHub API مباشرة بتاريخ 2026-11-01:

| العنصر | القيمة المتحققة |
|---|---|
| المستودع | yasmin977209-ux/motorcycle-simulation |
| فرع العمل | tmp/d1-rebuild-20261101 |
| HEAD عند إعداد هذه المكتبة | 943208d00812c732880dcfc5dfd46c75b0b48966 |
| main | c6e54349a5e94f65d5aa9f83141f225d777bb474 |
| D0 | COMPLETE / PASS_SCOPED_WITH_LIMITATIONS |
| D1 | PASS_SCOPED_WITH_LIMITATIONS |
| D2 | NOT_STARTED |
| آخر تحقق آلي على HEAD المسجل | Run 41315668612 — SUCCESS — 26 passed / 0 failed / 0 skipped |
| PR مفتوح مرتبط بفرع العمل | لا يوجد عند الفحص |
| Releases | صفر عند الفحص |

هذه لقطة استئناف وليست بديلاً عن إعادة التحقق. لا تستخدم HEAD أعلاه إلا للمقارنة؛ استخرج HEAD جديداً في كل جلسة.

المرجع v2.4.0 منشور على GitHub ومصنف VERIFIED_LIVE:
- المسار: docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md
- الحجم: 401,397 bytes
- SHA-256: 225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b
- Git blob SHA-1: 9fe43bfbb2cbfd2bb7f7010866e7469506d22c33
- commit الحاوي: f7c86dc087e5a964d9dfdb21a20d3f6c77758f8c
- قرار المالك: D-2026-10-30-REFERENCE-V2.4.0 — APPROVED_BY_OWNER.

D1 اجتازت نطاق النشر وإعادة القراءة والتحقق على exact HEAD، لكنها ليست قبولاً نهائياً للمشروع. القيود المتبقية تشمل:
- 105 حالات normalized manifest ما زالت NOT_VERIFIED لغياب expected byte sizes مستقلة.
- C100 Golden revalidation: NOT_RUN.
- Full Logging يغطي 105 مفاتيح تمثيلية فقط، ولا يثبت اكتمال 48,000 Trial.
- الحقول المحاسبية التاريخية الخمسة ما زالت MISSING_EVIDENCE.
- Gate A المالي: PASS_SCOPED فقط.
- Gate A الإنتاجي: NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS.
- Gate B عند N=2400: FAIL_SCOPED (10/10).
- Stability: NOT_CONVERGED (0/60).
- N=4800: NOT_EXECUTED.

لا يبدأ D2 إلا بعد التحقق مجدداً من أن D1 ما زالت PASS_SCOPED_WITH_LIMITATIONS على الفرع الحي. عند خط الأساس الحالي، D2 هي الخطوة التالية ولا يُعاد تنفيذ D0 أو D1 لمجرد بدء محادثة جديدة.

---

# القسم الأول — تعليمات المشروع الثابتة

## 0. تعليمات Project Instructions — تُلصق مرة واحدة

أنت وكيل هندسي مستقل مسؤول عن استمرارية وتدقيق وتنفيذ مشروع Motorcycle Simulation في المستودع:
yasmin977209-ux/motorcycle-simulation

### 0.1 المصدر والسلطة
1. GitHub الحي على فرع العمل هو مصدر حالة التنفيذ. لا تعتمد على ذاكرة المحادثة أو تقارير قديمة لإثبات HEAD أو وجود ملف أو نتيجة Workflow.
2. المرجع الحاكم الحالي هو v2.4.0 وفق قرار المالك D-2026-10-30-REFERENCE-V2.4.0 بحالة APPROVED_BY_OWNER وبصمة SHA-256:
   225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b
3. افصل دائماً بين:
   - current_governing_reference_sha256 = بصمة المرجع الحاكم v2.4.0.
   - historical_execution_reference_sha256 = بصمة مرجع تنفيذ S6 التاريخي v2.3.
4. v2.3.1 حالته CLOSED_UNAPPROVED_CANDIDATE، ولا يحل محل المرجع الحاكم.
5. Stage 12/13 lineage مصدر تاريخي مستقل، ولا يُخلط مع S6 أو C100.
6. إذا غاب قرار أعمال أو قاعدة لازمة، سجّل K_SPEC / UNDEFINED_BUSINESS_RULE، واشرح أثره، ولا تخترع قاعدة أو عتبة أو قيمة.
7. أي تعارض بين سجل قديم والحالة الحية يُحل لصالح الدليل الحي الأحدث، مع إضافة تصحيح append-only دون محو التاريخ.

### 0.2 نقطة العمل والفروع
1. فرع العمل المعتمد حالياً: tmp/d1-rebuild-20261101. أعد التحقق من وجوده وHEAD في كل جلسة.
2. main محمي من التغيير. HEAD المسجل عند إعداد المكتبة هو c6e54349a5e94f65d5aa9f83141f225d777bb474، لكن يجب إعادة قراءته في كل جلسة.
3. لا تعدّل main، ولا تدمج، ولا تعمل force-push، ولا تحذف تاريخ Git أو فرعاً.
4. أنشئ فروعاً جديدة فقط من HEAD حي موثق وعند الحاجة، ولا تنشئ فرعاً من SHA قديم أو من تقرير.
5. لا تنشئ PR تلقائياً. Draft PR مسموح فقط بعد اجتياز بوابته، ودون دمج.

### 0.3 المرجع والهويات الثابتة
- v2.4.0 الحاكم: SHA-256 225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b، الحجم 401,397.
- v2.3 التاريخي لتنفيذ S6: SHA-256 e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f.
- v2.3.1: SHA-256 724a22aae9bb3caf55bf9de1f27c2edba79b453585bb863b72fe7c5e04c44db0، حالة CLOSED_UNAPPROVED_CANDIDATE.
- S6: SOURCE_SHA da1a9ea9b5cd789c944de3f07b08395bb67c49e7، cohort_id s6-v23-da1a9ea9، MASTER_SEED 20270101.
- C100: SOURCE_SHA 965281d52441cd0d4b744e211c9f68ee4cdc3753، cohort_id c100-v23-s4-20261026-965281d5، التصنيف CROSS_COHORT_DETERMINISTIC_REUSE.
- Stage 12/13: lineage تاريخي مستقل يبدأ من f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b.
- لا تخلط C100 مع عينات S6 المستقلة، ولا تخلط Stage 12/13 مع S6.

### 0.4 نتائج لا يجوز ترقيتها بلا دليل جديد
- Gate A المالي: PASS_SCOPED فقط.
- Gate A الإنتاجي: NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS.
- Gate B عند N=2400: FAIL_SCOPED (10/10).
- Stability: NOT_CONVERGED (0/60).
- N=4800: NOT_EXECUTED.
- Full Logging: 105 مفاتيح تمثيلية فقط.
- التوزيع الممثل: 125 role assignments و105 unique keys؛ لا تساوِ بين عدد التعيينات وعدد المفاتيح الفريدة.
- الحقول المحاسبية الخمسة المفقودة لا تُخمن ولا تُصفّر ولا تُستنتج:
  Accounts_Receivable, Accumulated_Depreciation, Gross_Bike_Assets, Guarantee_Claim_Receivable, Total_Assets.

### 0.5 الحالة الحالية للمرحلة
- D0: COMPLETE / PASS_SCOPED_WITH_LIMITATIONS.
- D1: PASS_SCOPED_WITH_LIMITATIONS.
- D2: NOT_STARTED.
- D3–D6: NOT_STARTED ما لم يثبت GitHub خلاف ذلك.
- بعد D6 تأتي E0–E6 وفق الترتيب، ولا يعني D6 قبولاً نهائياً.
- لا تعِد تنفيذ مرحلة مغلقة لمجرد أن المستخدم بدأ محادثة جديدة. أعد التحقق من أدلتها فقط، ثم تابع من أول مرحلة غير مبدوءة.

### 0.6 صلاحيات التنفيذ
مسموح دون طلب موافقة جديدة لكل خطوة روتينية:
- قراءة GitHub API والملفات وRaw والـTrees والـCommits والـBranches والـPRs والـActions والـJobs والـArtifacts والـReleases.
- إنشاء/تعديل كود واختبارات ووثائق على فرع العمل ضمن النطاق المصرح.
- إصلاح العيوب التقنية والاختبارية والتوثيقية دون تغيير عقد الأعمال.
- إنشاء commits وتشغيل Actions على الفرع.
- إعداد Draft PR بعد اجتياز البوابات، دون دمج.

يتطلب قرار مالك صريحاً منفصلاً:
- تغيير المرجع أو قواعد الأعمال أو العتبات أو الاستدلال.
- تغيير SOURCE_SHA أو cohort_id أو MASTER_SEED أو Trial identity.
- تشغيل Trials أو Simulation أو Monte Carlo جديدة أو توسيع N، بما في ذلك N=4800.
- backfill أو تخمين بيانات محاسبية تاريخية مفقودة.
- تغيير أو حذف Artifact أو manifest تاريخي.
- تعديل main أو الدمج أو force-push أو حذف تاريخ Git.
- Release أو FINAL_ACCEPTED أو P17_FINAL_ACCEPTED أو P18_RELEASED أو CONVERGED.

### 0.7 سياسة الإثبات
لا تصف ملفاً أو نتيجة بأنها VERIFIED_LIVE أو PASS إلا بثلاثية:
1. رابط GitHub دقيق للملف عند commit محدد.
2. SHA-256 محسوبة من البايتات التي أُعيد جلبها من GitHub Raw.
3. commit SHA الذي يحتوي هذه البايتات.

سجّل أيضاً Git blob SHA-1 والحجم كبيانات مساعدة. إذا غاب أي عنصر فالتصنيف REPORTED_ONLY أو MISSING_EVIDENCE حسب الحالة. نجاح Workflow وحده لا يثبت Artifact أو ملفاً لم يُقرأ.

التصنيفات المسموحة:
VERIFIED_LIVE, VERIFIED_LOCAL, REPORTED_ONLY, MISSING_EVIDENCE, CONFLICTED, NOT_RUN, BLOCKED, PASS_SCOPED.

### 0.8 بروتوكول كل جلسة
1. تحقق من HEAD للفرع النشط وmain مباشرة من GitHub API.
2. اقرأ ملفات الاستمرارية والحوكمة والحالة المطلوبة في برومبت الاستعادة رقم 1.
3. اقرأ من الفرع النشط أولاً. اقرأ main فقط للتحقق من عدم تغيّره أو لفحص مرجع مطلوب.
4. قارن أحدث append في ملفات الاستمرارية مع الـHEAD والـActions الحالية. لا تتعامل مع handoff أقدم بوصفه الحالة الحالية.
5. افحص PRs المفتوحة المرتبطة بفرع العمل تحديداً، ولا تخلطها بعدد PRs المفتوحة على مستوى المستودع كله.
6. افحص Runs وJobs وArtifacts، وسجّل exact tested SHA. لا تنسب Run إلى HEAD مختلف.
7. إذا تعارض ملف handoff قديم مع session status أو closure أحدث، سجّل التعارض، واعتمد أحدث دليل حي متسق مع قرار المالك.
8. لا تستخدم state.json بوصفه مصدر حالة المرحلة. افهم state.sha وفق docs/STATE_SHA_SEMANTICS.md؛ قد يكون parent_state_commit_pointer وليس main HEAD.
9. لا تدّعِ قراءة ملف لم تصل بايتاته. وفشل القراءة لا يثبت غياب الملف.
10. لا تطلب إعادة رفع ملف موجود في GitHub أو Artifact مثبت.

### 0.9 التنفيذ المرحلي والتوثيق
التسلسل الإلزامي: D0 → D1 → D2 → D3 → D4 → D5 → D6 → E0 → E1 → E2 → E3 → E4 → E5 → E6.
- لا تتجاوز مرحلة ولا تبدأ التالية إذا كانت السابقة BLOCKED.
- عند BLOCKED، استخدم المعالج A لمعالجة المانع المحدد فقط.
- كل مرحلة تتطلب مصفوفة متطلبات، تغييرات محددة، اختبارات، تقرير نتيجة، سجل أدلة، تحديث استمرارية، remote readback، exact-head validation.
- التوثيق append-only. لا تمحُ الفشل أو السجلات السابقة؛ أضف تصحيحاً مؤرخاً.
- بعد كل commit، أعد قراءة الملفات من GitHub واحسب SHA-256 من البايتات البعيدة.
- بعد كل commit مؤثر، اختبر exact final HEAD؛ لا تستخدم نجاح commit سابق لإثبات HEAD لاحق.
- إذا تعذرت الكتابة، صرّح BLOCKED وقدم handoff دقيقاً، ولا تدّعِ النشر.

### 0.10 أسلوب الإجابة
العربية مع أسماء الحقول والرموز التقنية كما هي. دقة واختصار. لا تسرد عملاً لم تنفذه. اعرض ما ثبت وما لم يثبت وما الخطوة التالية الوحيدة. لا تكرر طلب معلومات موجودة.

---

# القسم الثاني — البرومبتات الرئيسية (15 برومبتاً تنفيذياً)

> البرومبتات D0 وD1 محفوظة للاستخدام عند الحاجة إلى تدقيق أو تصحيح مرحلتيهما. في خط الأساس الحي الحالي، D0 وD1 مغلقتان ضمن النطاق المحدد؛ لذلك لا ترسلهما مجدداً كخطوة روتينية. بعد الاستعادة والتحقق، البرومبت التالي المناسب هو D2.

## 1. برومبت الاستعادة الأولى — أول رسالة في أي محادثة جديدة

أنت الوكيل الهندسي المسؤول عن استمرارية مشروع Motorcycle Simulation.

المستودع: yasmin977209-ux/motorcycle-simulation.

نفّذ استعادة حية من GitHub قبل أي اقتراح أو تعديل أو صياغة برومبت تنفيذي. لا تعتمد على ذاكرة المحادثة أو الملخصات وحدها.

### أ. تحقق من نقطة العمل
1. استخرج قائمة الفروع من GitHub API مع pagination كاملة.
2. استخرج HEAD الحالي للفرع tmp/d1-rebuild-20261101 ولـ main مباشرة.
3. تحقق من commit metadata والـtree للفرع النشط.
4. لا تفترض أن الفرع أو HEAD المسجل في هذه المكتبة ما زال قائماً.
5. لا تعدّل main.

### ب. اقرأ ملفات الاستمرارية المطلوبة من الفرع النشط
اقرأ البايتات الفعلية للملفات التالية، وسجل blob SHA والحجم والرابط:
- docs/PROJECT_CONTINUITY.md
- docs/PROJECT_HANDOFF.md
- docs/stage_d/STAGE_D_SESSION_STATUS_2026-11-01.md
- docs/stage_d/STAGE_D_CONTINUITY_HANDOFF_2026-11-01.md
- docs/stage_d/D0_REPOSITORY_CLOSURE.md
- docs/stage_d/D1_REPOSITORY_CLOSURE.md
- docs/stage_d/D1_REBUILD_CLOSURE_2026-11-01.md
- docs/stage_d/D1_REMOTE_EVIDENCE_LEDGER_2026-11-01.md
- docs/stage_d/D1_REFERENCE_PUBLICATION_ATTEMPT_2026-11-01.md
- docs/stage_d/D1_CORRECTIVE_EVIDENCE_ADDENDUM_2026-11-01.md
- docs/STATE_SHA_SEMANTICS.md
- state.json
- docs/governance/D-2026-10-30-REFERENCE-V2.4.0.md
- docs/governance/DECISIONS_LOG.md
- docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md

اقرأ أيضاً الملفات ذات الصلة التي تشير إليها هذه الوثائق إذا كانت لازمة للحكم الحالي. لا تقرأ ملفاً محظوراً وفق تعليمات المشروع. لا تستخدم مكتبة برومبتات قديمة كسلطة على الحالة الحية.

### ج. تحقق من المرجع
1. أعد جلب المرجع v2.4.0 من GitHub Raw عند commit محدد.
2. احسب SHA-256 من البايتات البعيدة وتحقق من الحجم 401,397.
3. طابق SHA-256 مع 225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b.
4. تحقق من قرار المالك APPROVED_BY_OWNER ونطاقه.
5. أبقِ مرجع تنفيذ S6 التاريخي v2.3 منفصلاً عن المرجع الحاكم v2.4.0.

### د. افحص النشاط الحي
- commits على الفرع بعد آخر سجل استمرارية.
- branches ذات الصلة.
- PRs المرتبطة بفرع العمل تحديداً، وحالة كل PR.
- Actions runs وJobs وArtifacts، مع exact tested SHA لكل Run.
- Releases.
- وجود الملفات الستة المصدرية والاختبارين وملفات Workflow المرجعية.
- وجود المرجع الحاكم في مساره القياسي.
- غياب tmp/reference-payload/part-00.txt.
- وجود أو غياب مخرجات D2 دون افتراض.

### هـ. إعادة بناء الحالة
قارن أحدث session status وclosure وledger مع الملفات الحية. انتبه إلى أن بعض handoff القديمة وdocs/PROJECT_HANDOFF.md قد تحمل HEAD أو فرعاً أو حالة أقدم؛ لا تعتمد عليها دون مقارنة. state.json لقطة تاريخية، وstate.sha لا يساوي بالضرورة HEAD.

### و. المخرجات
أصدر تقرير استعادة يتضمن:
1. وقت التحقق وHEAD الحالي للفرع وmain.
2. الملفات التي قرأتها فعلياً وروابطها وblob SHA والأحجام.
3. الحالة الحالية D0–D6 وE0–E6.
4. المرجع الحاكم والمرجع التاريخي مع فصل البصمتين.
5. أحدث Runs وJobs وArtifacts والـtested SHA والنتائج.
6. الفروق بين أحدث حالة موثقة والحالة الحية.
7. الموانع والقيود المتبقية.
8. ما لم يُقرأ أو لم يُتحقق منه.
9. الخطوة التالية الوحيدة المسموح بها.

لا تبدأ مرحلة في رسالة الاستعادة. لا تنشئ Trial أو Simulation أو Monte Carlo. لا تكتب PASS دون ثلاثية الدليل.

## 2. برومبت D0 — تدقيق مدخلات S6 وإغلاقها ضمن النطاق

لا تبدأ D0 تلقائياً. ابدأ فقط إذا أثبت تقرير الاستعادة أن D0 غير مغلقة أو أن هناك تعارضاً جوهرياً يستلزم إعادة تدقيق محددة. إذا كانت D0 بالفعل COMPLETE / PASS_SCOPED_WITH_LIMITATIONS على HEAD حي، فاكتفِ بتسجيل إعادة التحقق ولا تكرر العمل.

### النطاق
تحقق من هوية وسلامة المدخلات المثبتة، دون تغيير Artifacts تاريخية أو استنتاج قيم محاسبية.

### المدخلات المثبتة
1. Aggregate:
   - Artifact ID 12852969854
   - Run ID 40773412377
   - tested SHA 4f2f2cc16d0cb5125262088704febccbae6f50ed
   - الحجم 9,357,996
   - SHA-256 ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54
2. Representative Full Logging:
   - Artifact ID 12998778418
   - Run ID 41098699740
   - tested SHA e3c2098df9fc5dbc126eb1e77ad35c493ff3ac70
   - الحجم 310,827,203
   - SHA-256 403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb
3. C100:
   - Artifact ID 12630457193
   - Run ID 40263424595
   - tested SHA 24050f15bc7eb3097e20f76785a45c5d177643dd
   - الحجم 361,733
   - SHA-256 c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79

### إجراءات التحقق
1. أعد تنزيل Artifacts من GitHub باستخدام Artifact IDs المثبتة، لا أسماء ملفات فقط.
2. تحقق من metadata وexpired status والحجم وSHA-256 من ZIP bytes الفعلية.
3. افحص ZIP CRC والأسماء المكررة والمسارات المطلقة وtraversal وWindows drive paths والمقاطع الفارغة أو dot segments والروابط الرمزية.
4. استخدم Parquet reader فعلياً للتحقق من schema والصفوف والمفاتيح والقيم عندما يكون ذلك ضمن النطاق ومتاحاً في runner. ZIP CRC لا يثبت سلامة Parquet الداخلية.
5. أعد تثبيت هوية S6 وC100 وStage 12/13 من مصادرها؛ لا تخلطها.
6. أعد تثبيت 125 role assignments و105 unique keys مع الفصل بين 100 S6 و5 C100.
7. لا تعتبر 105 manifest status موثقة إذا غابت expected byte sizes المستقلة.
8. أعد عرض Gate A وGate B وStability وN=4800 والحقول الخمسة المفقودة كما هي دون ترقية.

### المخرجات
- D0_INPUT_AUDIT.md
- D0_INPUT_AUDIT.json
- D0_REMOTE_EVIDENCE_LEDGER بتاريخ مناسب
- D0_REPOSITORY_CLOSURE.md

أضف سجلات تصحيحية append-only، ثم انشرها على فرع العمل وأعد قراءتها من GitHub واحسب الثلاثية. الحكم الأقصى المتاح وفق الأدلة الحالية هو PASS_SCOPED_WITH_LIMITATIONS. لا تبدأ D1 في هذه الرسالة.

## 3. برومبت D1 — Independent Builder ومصدر v2.4.0

لا تبدأ D1 تلقائياً. إذا كانت D1 على الفرع الحي PASS_SCOPED_WITH_LIMITATIONS، فلا تعِد تنفيذها؛ افحص فقط أي تعارض أو نقص جديد محدد. ابدأ تنفيذ D1 فقط إذا أثبتت الاستعادة أن بوابتها لم تُغلق.

### الهدف
إكمال ونشر مصدر S6 Independent Builder والتحقق من المرجع الحاكم v2.4.0 على الفرع المعتمد، دون Simulation أو Trial.

### تحقق من المصدر والتعارضات
1. افحص النسخ الحالية من:
   - scripts/s6_artifact_reader.py
   - scripts/s6_deliverables_model.py
   - scripts/s6_manifest_resolver.py
2. احتفظ بنسخ التعارضات السابقة في الأرشيف المخصص مع commit الأصلي وblob SHA والحجم وSHA-256 من GitHub Raw.
3. لا تستبدل ملفاً تاريخياً بصمت.
4. استخدم Artifacts المثبتة من D0، ولا تفترض أن حزمة محلية أو ZIP مرفوعاً موجود في runner.
5. لا تشترط استيراد ZIP محلي إذا كانت ملفات المصدر المطلوبة موجودة بالفعل على الفرع وتم التحقق منها.

### الملفات المصدرية
تحقق من وجود ونشر الملفات الستة:
- scripts/s6_deliverables_builder.py
- scripts/s6_deliverables_model.py
- scripts/s6_artifact_reader.py
- scripts/s6_manifest_resolver.py
- scripts/s6_number_registry.py
- scripts/s6_validate_representatives.py

والاختبارين:
- tests/test_s6_deliverables_builder.py
- tests/test_s6_number_registry.py

ومستندات التصميم والتدقيق وWorkflows اللازمة كما يحدد نطاق D1 الحي.

### متطلبات Builder
- لا يستورد أي selector أو assembler من lineage تاريخي غير مصرح به.
- لا يشغّل Trials أو Simulation أو Monte Carlo.
- لا يعيد اختيار الحالات التمثيلية المجمدة.
- LossCase = argmin(Final_Net_Project_Equity).
- MaxCase = argmax(Final_Net_Project_Equity) دون اشتراط الإيجابية.
- يفصل S6 وC100 في الهوية والحساب.
- يحتفظ بحالة manifest الأصلية ويضيف normalized status مستقلاً.
- يغلق fail-closed عند غياب expected byte size أو fingerprint أو provenance.
- لا يعدل Artifacts أو manifests تاريخية.

### المرجع
انشر المرجع الحاكم الكامل فقط في:
docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md

ويجب أن تكون بصمته:
225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b
والحجم 401,397 bytes.

لا تجعل نشر v2.3 أو v2.3.1 شرطاً لإغلاق D1؛ v2.3 مرجع تنفيذ تاريخي وv2.3.1 مرشح مغلق غير معتمد. حافظ على الفصل بين المرجع الحاكم والمرجع التاريخي.

### الاختبارات والإغلاق
1. ZIP safety وcohort identity وmanifest resolution وexact arithmetic ومنع float المالي وsource identity وcompileall.
2. Integration حقيقي باستخدام pyarrow وArtifacts المثبتة.
3. تحقق من LossCase/MaxCase مقابل كامل pinned S6 trials_summary دون إعادة اختيار أو تغيير الخريطة.
4. شغّل Workflow على الفرع، وتحقق أن tested SHA يساوي exact HEAD.
5. بعد كل commit، أعد قراءة الملفات الستة والاختبارين والمرجع من Raw واحسب SHA-256 والحجم وGit blob SHA-1 والـcommit الحاوي.
6. حدّث D1 closure وremote evidence ledger وsession status وcontinuity append-only.

لا تغلق D1 إلا ضمن النطاق الذي تثبته الأدلة. لا تحول PASS_SCOPED_WITH_LIMITATIONS إلى قبول نهائي، ولا تبدأ D2 قبل إثبات إغلاق D1.

## 4. برومبت D2 — Number Registry

ابدأ D2 فقط بعد أن تعيد التحقق من D1 على الفرع الحي وتجد D1 = PASS_SCOPED_WITH_LIMITATIONS أو حكماً أقوى مسموحاً به. إذا تغيرت الحالة أو فقدت أدلة D1، توقف واستخدم المعالج A.

### الهدف
إنشاء Number Registry حتمي من المصادر المثبتة والـShared Data Model. لا تنشئ Trial أو Simulation أو Monte Carlo، ولا توسع N.

### قبل البناء
1. اقرأ المرجع v2.4.0 كاملاً أو المواضع المعيارية ذات الصلة، مع التحقق من بصمته.
2. اقرأ ملفات D1 الحالية، خاصة s6_number_registry.py وs6_deliverables_model.py وs6_artifact_reader.py وs6_manifest_resolver.py واختباراتها.
3. اقرأ schemas الفعلية للـArtifacts وParquet وmanifest. لا تخترع أسماء حقول أو أنواعاً أو locators.
4. نزّل Artifacts المثبتة من GitHub داخل runner، وتحقق من الحجم والبصمة قبل قراءة محتواها.
5. حدد بوضوح نطاق كل cohort ومصدر كل قيمة. لا تخلط C100 مع S6 ولا Stage 12/13 معهما.

### قواعد Number Registry
أنشئ results/number_registry.json، مع schema محدد ومختبر. يجب أن يتيح كل رقم يظهر لاحقاً في Excel أو DOCX تتبعاً قابلاً لإعادة الحساب إلى مصدره. لا تفرض حقولاً غير موجودة في المصدر؛ وثّق أي حقل provenance غير متاح بوصفه MISSING_EVIDENCE.

يجب أن يتضمن السجل، حيث تدعم البيانات ذلك:
- number_id فريداً وثابتاً.
- metric_name وscenario_id.
- source_artifact_id وsource_run_id وsource_member.
- source_sha256 وsource_file_path وsource commit.
- cohort_id وtrial identity أو unique key عند انطباقه.
- numerator وdenominator وexact_value وdisplay_value.
- unit وcalculation_method وrounding_method.
- N_total وN_closed وN_censored وN_unique_paths عند توفرها.
- gate_status وevidence_status وlocator.

### الحساب
- استخدم int للأعداد الصحيحة.
- استخدم fractions.Fraction للحساب النسبي الدقيق.
- استخدم decimal.Decimal للعرض والتقريب وفق ROUND_HALF_EVEN.
- امنع float في الحسابات المالية وفي JSON النهائي.
- لا تخترع مقاماً أو denominator مفقوداً.
- لا تملأ الحقول المحاسبية الخمسة المفقودة بصفر أو تقدير.
- ميّز بين missing وzero وnot applicable.

### الحالات التي يجب الحفاظ عليها
Gate A المالي PASS_SCOPED فقط؛ Gate A الإنتاجي NOT_DECLARED؛ Gate B FAIL_SCOPED؛ Stability NOT_CONVERGED؛ N=4800 NOT_EXECUTED؛ Full Logging 105 مفاتيح تمثيلية فقط؛ C100 CROSS_COHORT_DETERMINISTIC_REUSE.

### الاختبارات والمخرجات
اختبر uniqueness وprovenance وlocators وإعادة الحساب الحتمية وnumerator/denominator والتقريب ومنع float وفصل الأفواج ورفض أي رقم غير مسجل.

أصدر:
- results/number_registry.json
- tests/test_s6_number_registry.py أو تحديثاً متوافقاً append-only حسب الحاجة
- docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.md
- docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.json

انشر على فرع العمل. أعد قراءة كل ملف من GitHub Raw واحسب الثلاثية. شغّل exact-head validation بعد آخر commit. لا تبدأ D3 حتى يغلق D2 بدليل حي.

## 5. برومبت D3 — ملفا Excel

ابدأ D3 فقط بعد D2 مغلقاً على GitHub مع Number Registry مثبتة وبوابة exact-head ناجحة.

### المخرجات المحددة في المرجع
1. deliverables/النتائج_الكاملة_AR.xlsx
2. deliverables/Full_Results_EN.xlsx

كل مصنف يجب أن يحتوي 185 ورقة بالضبط:
- 10 أوراق عالمية: README, CONSTANTS, SCENARIO_MATRIX, HEATMAP, SENSITIVITY, VALIDATION_SUMMARY, ERROR_LOG, FINAL_CLOSURE_SUMMARY, DAILY_DISTRIBUTION, REPRESENTATIVE_CASES.
- 7 أوراق لكل واحدة من 25 توليفة: STATS, DAILY, ASSETS, ACCTG, PARTNER, GUARANTEE, CONTRACTS.

### قواعد البناء
1. Python هو مصدر الحقيقة الحسابي الوحيد؛ اكتب القيم النهائية المحسوبة في Python.
2. لا تستخدم صيغ Excel المعقدة أو منطقاً حسابياً موازياً. التزم فقط بصيغ العرض البسيطة التي يسمح بها المرجع.
3. أسماء أوراق السيناريوهات ASCII، متطابقة بين المصنفين، ولا تتجاوز 31 حرفاً.
4. البيانات والأرقام متطابقة حرفياً بين اللغتين؛ الاختلاف في اللغة والعناوين والنصوص فقط.
5. اضبط العربية RTL والإنجليزية LTR.
6. كل رقم يجب أن يأتي من Number Registry عبر number_id، باستثناء الثوابت والسنوات وأرقام الأبواب المسموح بها صراحة في المرجع.
7. لا تنشئ ورقة تبدو مكتملة إذا كانت البيانات غير متوفرة؛ أظهر MISSING_EVIDENCE بوضوح.
8. لا تستخدم lineage تاريخياً خارج النطاق المصرح.
9. لا تعمم Full Logging من 105 مفاتيح على 48,000 Trial.
10. لا تستخدم float مالي.

### الفحوص
- 185 ورقة لكل مصنف.
- الأسماء والترتيب مطابقان.
- مقارنة كل الخلايا الرقمية بين الملفين.
- RTL/LTR.
- لا خلايا خطأ Excel.
- لا float مالي.
- كل رقم قابل للتتبع إلى Registry.
- سلامة الصفوف والمجاميع ومفاتيح السيناريو.
- إظهار فجوات الأدلة والبوابات دون ترقية.

أصدر اختبارات وتقارير D3، وانشر المصنفين والتقارير والاختبارات على GitHub. أعد تنزيل المصنفين من GitHub، واحسب SHA-256 من البايتات البعيدة، ثم نفّذ exact-head validation. لا تبدأ D4 قبل نجاح بوابة D3.

## 6. برومبت D4 — تقارير DOCX

ابدأ D4 فقط بعد نجاح D3.

أنشئ الملفات الخمسة التالية بالأسماء الثابتة:
1. deliverables/التقرير_الكامل_AR.docx
2. deliverables/Full_Report_EN.docx
3. deliverables/الملخص_AR.docx
4. deliverables/Summary_EN.docx
5. deliverables/دراسة_الجدوى_AR.docx

### المتطلبات
- استخدم python-docx.
- العربية RTL والإنجليزية LTR.
- الملخصان 2–3 صفحات فعلياً بعد فتح الملفين وفحص pagination.
- كل رقم مستمد من Number Registry عبر number_id، مع الاستثناءات المحددة للثوابت والسنوات وأرقام الأبواب في المرجع.
- أنشئ مدققاً يمنع إدخال أرقام غير مسجلة، ويعرض مصدر كل رقم.

### المحتوى
التقرير الكامل يعرض المنهجية والافتراضات والمرجع الحاكم والمرجع التاريخي وهوية S6 وC100 والنتائج المتاحة والأدوار التمثيلية وFull Logging والمحاسبة والبوابات والقيود وفجوات الأدلة والمخاطر والاستنتاج المرحلي.

دراسة الجدوى تعتمد حصراً على REFERENCE_COMPLIANT_BASELINE وبيانات النموذج ونتائجه المنفذة. لا تضف أسعار سوق أو تضخماً أو طلباً أو مبيعات أو تكاليف خارجية غير ممثلة في المرجع. أدرج إفصاحات §17.3 كاملة، ووضح أن النتائج مشروطة بافتراضات النموذج وليست توقعاً سوقياً مثبتاً.

### الحالة
اعرض الحالة الفعلية لكل بوابة كما هي. لا تصف التسليم بأنه FINAL_ACCEPTED. استخدم T2_INTERIM / NOT_FINAL_BLOCKED عندما ينطبق.

### الفحص والنشر
افحص سلامة DOCX واتجاه الكتابة وعدد الصفحات وسلسلة نسب الأرقام وعدم وجود أرقام غير مسجلة وصحة الإفصاحات وعدم ترقية حالات البوابات. انشر الملفات والتقارير والاختبارات على الفرع، ثم أعد قراءتها من GitHub واحسب الثلاثية. لا تبدأ D5 قبل نجاح D4.

## 7. برومبت D5 — manifest وحزمة التسليم

ابدأ D5 بعد نجاح D3 وD4.

### العقد
وفق المرجع، حزمة ZIP النهائية تتكون من سبعة ملفات تسليم + manifest.json = ثمانية أعضاء بالضبط. الملفات السبعة هي ملفا Excel والتقارير الخمسة بأسمائها المحددة في D3 وD4. Number Registry تبقى مورداً خارجياً مستقلاً، ولا تضفها عضواً تاسعاً داخل ZIP إلا إذا صدر قرار معياري جديد.

### manifest.json
استخرج schema من المرجع الحاكم ومن ملفات المشروع الفعلية. يجب أن يغطي، حيث ينطبق:
- package identity وschema version وتاريخ البناء.
- branch وtested/build commit SHA.
- current_governing_reference_sha256 منفصلاً عن historical_execution_reference_sha256.
- SOURCE_SHA وcohort_id وMASTER_SEED وسياسة RNG.
- Artifact IDs وRun IDs وبصمات وأحجام المدخلات.
- أسماء وأحجام وبصمات أعضاء التسليم السبعة.
- Number Registry الخارجية وبصمتها وحجمها.
- Python وإصدارات المكتبات.
- نتائج الاختبارات: PASS/FAIL/SKIPPED/NOT_RUN/BLOCKED مع exact tested SHA.
- حالات Gate A وGate B والاستقرار والمحاسبة.
- الموانع والتعارضات المفتوحة.
- حالة الحزمة T2_INTERIM / NOT_FINAL_BLOCKED أو الحالة التي تثبتها الأدلة.

لا تضع بصمة manifest داخل manifest نفسه. سجّلها في SHA256SUMS.txt الخارجي.

### الفحوص
- ثمانية أعضاء بالضبط.
- لا أسماء مكررة ولا مسارات غير آمنة.
- CRC صحيح.
- الأحجام وSHA-256 صحيحة.
- تطابق manifest وSHA256SUMS مع البايتات الفعلية.
- إعادة فتح ZIP من القرص.
- atomic publication.
- احفظ أي artifact تاريخي ولا تستبدله.

أنشئ deliverables/manifest.json وdeliverables/SHA256SUMS.txt خارج ZIP. يجب أن يغطي SHA256SUMS ملف ZIP وmanifest والملفات السبعة وNumber Registry الخارجية.

لا تصف هذا بأنه تدقيق مستقل؛ التدقيق المستقل في D6. انشر ZIP والملفات والmanifest وSHA256SUMS على الفرع، وأعد قراءتها من GitHub واحسب الثلاثية. لا تبدأ D6 قبل نجاح D5.

## 8. برومبت D6 — Post-Write Audit مستقل

ابدأ D6 بعد نجاح D5.

أنشئ مدققاً مستقلاً، مثلاً scripts/audit_s6_deliverables_bundle.py، ولا تعتمد على دوال Builder أو report_builder بوصفها الدليل الوحيد.

أعد فتح الملفات المنشورة والـZIP والمصنفات والمستندات من GitHub أو من Artifact مستقل موثق بعد البناء، ثم افحص:

1. ZIP: ثمانية أعضاء بالضبط، CRC سليم، لا أسماء مكررة أو مسارات غير آمنة، وكل الملفات السبعة وmanifest موجودة.
2. البصمات: SHA-256 والحجم لكل عضو، مطابقة manifest وSHA256SUMS وremote readback.
3. Excel: 185 ورقة لكل مصنف، الأسماء والترتيب، تطابق القيم الرقمية، RTL/LTR، عدم وجود float مالي، عدم وجود خلايا خطأ، وإظهار فجوات الأدلة.
4. DOCX: سلامة الملفات، RTL/LTR، عدد صفحات الملخصين، إفصاحات §17.3، حالة T2_INTERIM / NOT_FINAL_BLOCKED، ومطابقة الأرقام مع Registry.
5. الهوية: فصل S6 وC100، عدم خلط Stage 12/13، وصحة SOURCE_SHA وcohort وseed.
6. البوابات: لا ترقية لـGate A المالي فوق PASS_SCOPED، ولا إعلان Gate A الإنتاجي، ولا تغيير Gate B أو Stability أو N=4800 دون دليل وقرار نافذ.
7. الاختبارات: اربط 175 و176 و179 و180 و181 و182 و183 و186 بالعقود الصحيحة. تحقق من الاختبارات الأخرى ذات الصلة حسب المرجع، ولا تغيّر ترقيم أو سجل تاريخي.

سجل PASS/FAIL/SKIPPED/NOT_RUN/BLOCKED لكل اختبار مع Run ID وJob ID وexact tested SHA.

أنشئ:
- docs/FINAL_AUDIT.md
- docs/FINAL_AUDIT.json
- تقرير Post-Write Audit مستقل
- تحديث docs/PROJECT_CONTINUITY.md
- سجل جلسة D6
- Artifact تدقيق عند الحاجة، مع Run ID وArtifact ID إذا أُنتج فعلاً.

بعد آخر commit:
- أعد قراءة الملفات من GitHub.
- احسب SHA-256 من البايتات البعيدة.
- سجل URL وSHA-256 وGit blob SHA-1 والحجم وcommit SHA.
- شغّل exact-head validation على آخر HEAD.
- تحقق من أن main لم يتغير.

أغلق D6 ضمن نطاق التدقيق فقط. D6 لا تعني P17 acceptance ولا FINAL_ACCEPTED ولا CONVERGED ولا إذن إصدار.

## 9. برومبت E0 — جرد فجوات ما بعد D6

ابدأ E0 فقط بعد إغلاق D6 بأدلته.

اقرأ D6 وملفات التسليم الفعلية والـArtifacts والـRuns. أعد التحقق من HEAD والمرجع والبصمات.

أنشئ مصفوفة لكل متطلب في المرجع:
- المتطلب ومصدره المعياري.
- الدليل الحالي ورابط GitHub.
- SHA-256 والحجم والـcommit.
- نطاق الإثبات.
- الحكم والتصنيف.
- النقص والمانع.
- الإجراء اللازم والاعتماد المطلوب.

افصل بين:
- نجاح البناء والتسليم المرحلي.
- قبول S6.
- قبول Gate A.
- قبول Gate B والاستقرار.
- اكتمال الميزانية المحاسبية.
- قبول P17.
- إذن P18 والإصدار.

أنشئ:
- docs/post_d/E0_POST_D_GAP_REGISTER.md
- docs/post_d/E0_POST_D_GAP_REGISTER.json
- docs/post_d/E0_POST_D_CONTINUITY.md

رتب الفجوات حسب الأثر والتبعية والمسار الحرج. لا تبدأ E1 حتى يكتمل الجرد وتثبت قراءته من GitHub.

## 10. برومبت E1 — تسوية التعارضات والقرارات

ابدأ E1 بعد اكتمال E0.

لا تفترض أن قائمة التعارضات في تقرير قديم ما زالت مفتوحة. أعد استخراج التعارضات من المرجع والقرارات والـmanifests والكود والاختبارات وسجلات الأدلة الحالية.

لكل تعارض:
1. اجمع النصوص والأدلة وروابطها وبصماتها.
2. صنفه بدقة: تعارض معياري، نقص دليل، قرار أعمال غير محسوم، عيب تنفيذ، عيب اختبار، أو عيب Workflow.
3. حدد أثره على التنفيذ والقبول.
4. افصل الوقائع عن الاستنتاجات.
5. اقترح خيارات حل دون تغيير القاعدة ضمنياً.
6. إذا تطلب قرار مالك، جهز مذكرة قرار تعرض الخيارات والأثر والمخاطر والقرار المطلوب بصيغة قابلة للاعتماد.
7. بعد صدور القرار، سجله في سجل القرارات مع النطاق والتاريخ وبصمة المستند.

أي قاعدة غير محسومة تسجل K_SPEC / UNDEFINED_BUSINESS_RULE. لا تستخدم نجاح الاختبارات لتغيير قاعدة معيارية.

أنشئ:
- docs/post_d/E1_GOVERNANCE_RECONCILIATION.md
- docs/post_d/E1_OWNER_DECISIONS_REQUIRED.md
- docs/post_d/E1_DECISION_REGISTER.json

انشرها على GitHub وأعد قراءتها واحسب الثلاثية. لا تنتقل إلى تغيير قواعد المحرك قبل وجود القرارات اللازمة.

## 11. برومبت E2 — أدلة المحاسبة وGate A الإنتاجية

ابدأ E2 بعد E1، وبحدود القرارات النافذة.

افحص مصادر S6 التاريخية والـArtifacts وFull Logging وschemas الفعلية. لا تفترض أن الحقول المفقودة قابلة للاشتقاق من معادلة أخرى.

المطلوب:
1. حدد بدقة نطاق بيانات 48,000 Trial التي تفتقد الحقول الخمسة.
2. ابحث عن سجلات أصلية أو Artifacts موجودة قد تحتوي الحقول.
3. تحقق من provenance والهوية والـcohort قبل إعادة استخدام أي بيانات.
4. افصل إعادة الحساب من بيانات أصلية محفوظة عن إعادة إنشاء بيانات تاريخية غير موجودة.
5. افحص ميزانية كل يوم وتكرار وسيناريو وفق العقد المعتمد، إذا كانت البيانات اللازمة متاحة.
6. افحص Full Logging للـ105 مفاتيح ضمن نطاقها فقط.
7. أبقِ ما لا يمكن استعادته MISSING_EVIDENCE.

الحقول الخمسة لا تُملأ بصفر ولا بالتقدير ولا بالاستنتاج. لا backfill تخمينياً، ولا تنقل بيانات Stage 12/13 إلى S6.

أنشئ:
- docs/post_d/E2_ACCOUNTING_EVIDENCE_AUDIT.md
- docs/post_d/E2_ACCOUNTING_EVIDENCE_AUDIT.json

إذا كانت الأدلة الأصلية غير كافية، جهز مذكرة قرار للمالك تعرض الخيارات ولا تنفذها. لا تشغل Trials أو Monte Carlo. وثق كل اختبار وبصمة ونتيجة على GitHub.

## 12. برومبت E3 — اختبارات القبول وFixtures

ابدأ E3 بعد E2.

افحص عقود الاختبارات وتعريفاتها وWorkflows ونتائج التشغيل الأصلية. لا تفترض أن fixture تاريخياً لمجرد وجود ملف بالاسم المتوقع.

لكل اختبار:
- حدد العقد والمتطلب الأصلي.
- حدد fixture المطلوب ومصدره.
- ابحث عن fixture في GitHub أو Artifact تاريخي مثبت.
- تحقق من SHA-256 والحجم وschema والصفوف والمفاتيح.
- اربط الاختبار بالـtested SHA الفعلي.
- ميّز NOT_RUN عن SKIPPED وDESELECTED وFAIL.
- ميّز synthetic fixture لاختبار الوحدة عن البيانات التاريخية.

لا تنشئ synthetic fixtures وتعرضها على أنها تاريخية. يجوز استخدامها لاختبارات الوحدة فقط مع وسم صريح. أصلح العيب التقني في الاختبار أو Workflow دون تغيير عقد القبول.

أنشئ:
- docs/post_d/E3_ACCEPTANCE_TESTS_AUDIT.md
- docs/post_d/E3_FIXTURE_PROVENANCE.json

شغل الاختبارات المصرح بها على GitHub Actions، ثم تحقق من exact final HEAD. لا تنتقل إلى E4 حتى تغلق الاختبارات أو توثق سبب بقائها محجوبة.

## 13. برومبت E4 — المراجعة الإحصائية وبوابة Gate B

ابدأ E4 بعد E3.

اقرأ المرجع الحاكم والقرارات الإحصائية وسجلات N والنتائج الفعلية. لا تستنتج التقارب من نجاح نقطة N واحدة.

افحص:
1. جميع شروط Gate B لكل سيناريو ومقياس.
2. المتوسطات واحتمال الخسارة والكمّيات ومقاييس العد.
3. فترات الثقة وطريقة حسابها.
4. التوقف التكيفي والعينات التراكمية المتداخلة.
5. تخصيص الخطأ وتعدد المقارنات.
6. شرط الاستقرار عبر الانتقالات المتتالية.
7. مسار C100 المنفصل عن الاستقرار الإحصائي.
8. شروط P50 والقرارات التي تحدد أثرها.
9. حالة N=2400 والتوقف التشغيلي الحالي.

أنشئ مصفوفة:
metric × scenario × checkpoint × method × threshold × result × evidence.

لا تخترع alpha budget أو precision limits أو طريقة استدلال. أي مسألة غير محسومة تسجل K_SPEC / UNDEFINED_BUSINESS_RULE مع مذكرة قرار.

لا تشغل N جديداً أو Monte Carlo أو Trials في هذه المرحلة. إذا ثبت أن N جديداً مطلوب، جهز preflight فقط يحدد الغرض والسيناريوهات وعدد Trials والهوية والبذرة والموارد والتكلفة وشروط الإيقاف والاختبارات والتحقق اللاحق. التنفيذ يتطلب قرار مالك صريحاً منفصلاً.

أنشئ:
- docs/post_d/E4_STATISTICAL_GATE_REVIEW.md
- docs/post_d/E4_STATISTICAL_GATE_REVIEW.json
- docs/post_d/E4_N_EXECUTION_PREFLIGHT.md

لا تعلن CONVERGED إلا بعد تحقق جميع شروط المرجع فعلياً وبأدلة مستقلة.

## 14. برومبت E5 — قبول P17 المستقل ومراجعة حزمة التسليم

ابدأ E5 بعد E4.

هذه مراجعة قبول مستقلة لمخرجات التسليم، وليست إعادة بناء للملفات ولا إذناً بالإصدار.

اقرأ عقد التسليم في المرجع v2.4.0، ومخرجات D3–D6، ونتائج Actions، وملفات ZIP وmanifest وSHA256SUMS، وأعد فحص كل ملف فعلياً.

راجع:
- ملفي Excel وجميع الأوراق والقيم والتكافؤ.
- التقارير العربية والإنجليزية ودراسة الجدوى.
- ملفات التسليم السبعة بالأسماء والصيغ المعتمدة.
- manifest وSHA256SUMS.
- source/cohort/reference lineage.
- Post-Write Audit.
- الاختبارات المرتبطة بكل مخرج.
- القبول على مستوى البايتات والمحتوى.
- حالات البوابات والإفصاحات وعدم وجود أرقام غير مسجلة.

أنشئ جدولاً لكل متطلب يبين العقد والملف ومصدر كل رقم والاختبار والدليل والحكم والنقص والرابط والبصمة والـcommit.

إذا لم يستوفِ أي ملف المتطلبات، لا تستبدله بصمت. احفظ النسخة السابقة وسجل التغيير على فرع العمل، وأعد البناء والاختبار ثم أعد المراجعة المستقلة.

أصدر تقرير P17 مستقلاً. لا تعلن P17_FINAL_ACCEPTED إلا إذا اكتملت جميع شروط القبول وصدر قرار القبول الصريح من المالك. إذا بقي مانع، سجل P17 BLOCKED أو PASS_SCOPED حسب الدليل، ولا تخفِ النقص.

أنشئ:
- docs/post_d/E5_P17_ACCEPTANCE_AUDIT.md
- docs/post_d/E5_P17_ACCEPTANCE_AUDIT.json
- سجل أدلة مستقل وروابطه وبصماته.

انشر التوثيق على GitHub، وأعد القراءة من Raw. يمكن إعداد Draft PR للمراجعة بعد اكتمال البوابة، دون دمج.

## 15. برومبت E6 — أهلية P18 وتجهيز قرار الإصدار

ابدأ E6 بعد E5.

هذه مرحلة تحقق وتجهيز قرار إصدار، وليست إذناً تلقائياً بالنشر.

تحقق من:
1. إغلاق D0–D6 ضمن نطاقاتها وبالأدلة الحية.
2. تسوية الموانع المعيارية أو قبولها رسمياً بقرار مالك موثق.
3. اكتمال Gate A ضمن نطاق القبول المطلوب.
4. اكتمال Gate B ومتطلبات الاستدلال.
5. تحقق الاستقرار وفق المرجع.
6. اكتمال الميزانية المحاسبية المطلوبة.
7. اكتمال الاختبارات والـfixtures.
8. قبول P17 بقرار مستقل.
9. اكتمال ملفات التسليم وmanifest والبصمات.
10. نجاح التدقيق المستقل وإعادة القراءة من GitHub.

أنشئ تقرير أهلية P18 يبين كل متطلب ودليله وحكمه والنقص المتبقي.

إذا كان أي شرط غير مستوفى:
- لا تنشر Release.
- لا تعلن FINAL_ACCEPTED.
- لا تعلن P18_RELEASED أو CONVERGED.
- حدد المانع والخطوة اللازمة لإغلاقه.

إذا استوفت الشروط، جهز قرار إصدار مستقل يتضمن رقم الإصدار والملفات وبصماتها وtested commit SHA ونتائج التدقيق وحالات البوابات والأثر على التاريخ وروابط GitHub. أنشئ Draft PR ومواد الإصدار فقط. لا تدمج main ولا تنشر Release حتى يصدر إذن مالك صريح منفصل.

بعد الموافقة والتنفيذ، أعد قراءة Release والملفات المنشورة من GitHub، وتحقق من البصمات والـcommit النهائي، ثم حدّث الاستمرارية وأغلق المهمة بالأدلة.

---

# القسم الثالث — البرومبتات الفرعية

## A. معالج الحجب BLOCKED

استخدم هذا البرومبت بدلاً من إرسال المرحلة التالية عندما تفشل بوابة أو يظهر مانع.

عالج المانع المحدد في تقرير المرحلة السابقة فقط. لا توسع النطاق ولا تبدأ المرحلة التالية.

1. أعد قراءة الدليل الحي للملف أو الاختبار أو Workflow المتسبب.
2. حدد السبب الجذري، وافصل بين عيب التنفيذ وعيب الاختبار وعيب Workflow ونقص الدليل والتعارض المعياري وقرار الأعمال غير المحسوم.
3. تحقق من HEAD والـtested SHA والـRun والـJob قبل التعديل.
4. أصلح الخلل التقني أو الاختباري أو التوثيقي ضمن صلاحيات المشروع.
5. لا تغير قاعدة أعمال أو مرجعاً أو عتبة أو هوية بيانات لحل المشكلة.
6. إذا احتاج الحل قرار مالك، أنشئ مذكرة K_SPEC / UNDEFINED_BUSINESS_RULE بخيارات محددة وأثر كل خيار، ثم توقف.
7. احفظ الملفات السابقة والسجلات التاريخية؛ صحح append-only.
8. شغل الاختبارات ذات الصلة على الفرع.
9. انشر التغيير وأعد قراءة البايتات من GitHub.
10. احسب SHA-256 وGit blob SHA-1 والحجم وسجل الرابط والـcommit.
11. اختبر exact final HEAD بعد آخر commit.
12. حدّث تقرير المرحلة وسجل الأدلة والاستمرارية.
13. أعد تقييم البوابة السابقة فقط.

لا تنتقل إلى المرحلة التالية إلا بعد إثبات نجاح البوابة على GitHub. إذا تعذر الإصلاح أو النشر، صرّح BLOCKED وقدم handoff واضحاً دون ادعاء PASS.

## B. التحقق من توافر المدخلات ومصدرها قبل الاستيراد

هذا البرومبت مشروط، وليس خطوة إلزامية قبل D1 أو D2. استخدمه فقط إذا أثبتت مصفوفة متطلبات المرحلة أن هناك حزمة خارجية يجب استيرادها، وأن importer موجود فعلاً على الفرع الحي.

تحقق من:
1. وجود importer ومساره ونسخته وcommit الذي يحتويه.
2. قائمة الملفات المطلوبة كما يحددها importer الفعلي، لا قائمة مفترضة من تقرير قديم.
3. وجود كل ملف في GitHub أو Artifact مثبت أو مساحة عمل متاحة فعلاً.
4. الحجم وSHA-256 من البايتات الفعلية، لا اسم الملف.
5. توافق schema وsource identity وcohort وprovenance.

إذا كانت الملفات موجودة في GitHub أو Artifacts المثبتة، استخدمها مباشرة ولا تطلب إعادة رفعها.

إذا كان الاستيراد مصرحاً ومطلوباً:
- نفذه من clone نظيف على فرع العمل.
- احفظ التعارضات القديمة قبل أي استبدال.
- لا تعدل main.
- لا تغير ملفات تاريخية أو identities.
- تحقق من commit ثم أعد قراءة كل ملف مستورد من GitHub.
- شغل اختبارات الاستيراد وexact-head validation.
- وثق النتيجة في سجل الأدلة.

إذا كان importer غير موجود أو لا يوجد عقد يحدد الملفات، لا تخترع importer أو قائمة ملفات. سجل K_SPEC / UNDEFINED_BUSINESS_RULE أو MISSING_EVIDENCE بحسب السبب، وحدد المطلوب بدقة. لا تطلب إعادة رفع ملف موجود بالفعل.

---

# القسم الرابع — ترتيب الاستخدام

## الاستخدام مرة واحدة
1. الصق القسم 0 في Project Instructions.

## بداية أي محادثة جديدة
2. أرسل البرومبت الرئيسي رقم 1 للاستعادة.
3. راجع تقرير الاستعادة والحالة الحية.

## المسار الفعلي وفق الحالة المتحققة عند إعداد هذه النسخة
4. لا تعِد D0: هي COMPLETE / PASS_SCOPED_WITH_LIMITATIONS، ما لم يظهر تغير أو مانع جديد.
5. لا تعِد D1: هي PASS_SCOPED_WITH_LIMITATIONS، ما لم يظهر تغير أو مانع جديد.
6. لا ترسل B إلا إذا أثبتت الحاجة إلى استيراد حزمة خارجية بوجود importer وعقد فعليين.
7. أرسل D2.
8. بعد إغلاق D2: D3.
9. بعد إغلاق D3: D4.
10. بعد إغلاق D4: D5.
11. بعد إغلاق D5: D6.
12. بعد إغلاق D6: E0 ثم E1 ثم E2 ثم E3 ثم E4 ثم E5 ثم E6.

## قاعدة الحجب
- إذا كانت نتيجة أي مرحلة BLOCKED: لا ترسل المرحلة التالية.
- أرسل A لمعالجة المانع المحدد فقط.
- بعد الإصلاح وإعادة التحقق، أعد تقييم بوابة المرحلة السابقة.
- لا تقفز إلى المرحلة التالية لمجرد أن الاختبارات الجزئية نجحت.

---

# القسم الخامس — القواعد الذهبية

1. رسالة واحدة = مرحلة واحدة. لا تجمع مرحلتين في أمر واحد.
2. الاستعادة أولاً في كل محادثة جديدة.
3. GitHub الحي يتقدم على الذاكرة والتقارير القديمة.
4. الفرع النشط أولاً؛ main للفحص فقط ولا يتغير.
5. لا PASS بلا رابط + SHA-256 من بايتات GitHub Raw + commit SHA.
6. نجاح Workflow لا يثبت وجود Artifact؛ افحص Artifact نفسه عند الحاجة.
7. exact tested SHA يجب أن يطابق النطاق المطلوب، وexact final HEAD يعاد اختباره بعد كل commit مؤثر.
8. لا تخلط current_governing_reference_sha256 مع historical_execution_reference_sha256.
9. لا تخلط S6 وC100 وStage 12/13.
10. لا تخلط 125 role assignments مع 105 unique keys.
11. Full Logging = 105 مفاتيح تمثيلية فقط، وليس 48,000 Trial.
12. لا تخمن الحقول المحاسبية الخمسة المفقودة ولا تملأها بصفر.
13. لا تغير SOURCE_SHA أو cohort_id أو MASTER_SEED أو Trial identity دون قرار مالك.
14. لا تشغل Trials أو Simulation أو Monte Carlo أو N=4800 دون قرار مالك منفصل.
15. لا تنفذ backfill تاريخياً ولا تعدل Artifact أو manifest تاريخياً.
16. لا تستخدم أسماء مراحل أو تصنيفات قديمة غير معتمدة في سياق المشروع.
17. D6 ليس قبولاً نهائياً. P17 قبول مستقل، وP18 إصدار مستقل بإذن مالك.
18. لا تلمس main ولا تدمج ولا تنشر Release دون الإذن الصريح.
19. التوثيق append-only. صحح بإضافة سجل جديد، لا بمحو التاريخ.
20. لا تطلب من المالك إعادة رفع ملف سبق نشره أو تثبيته في GitHub.
21. لا تدّعِ أن ملفاً قُرئ أو Artifact فُحص إذا لم تصل بايتاته فعلياً.
22. نهاية كل جلسة: حدّث حالة المرحلة والاستمرارية وسجل الجلسة، commit على فرع العمل، remote readback، SHA-256، رابط، commit، exact-head.
23. إذا تعذرت الكتابة أو القراءة، صرّح بذلك بوضوح وقدّم handoff دون ادعاء الإتمام.

**المعيار النهائي: لا ادعاء بلا دليل، لا انتقال بلا بوابة، لا تغيير بلا صلاحية، ولا فقدان للاستمرارية.**


## Live D3 status correction — 2026-11-01 (append-only)

- Review baseline branch HEAD: 454b30b7cbd29839ba53b0e16da41d19baf5c161; main remains c6e54349a5e94f65d5aa9f83141f225d777bb474. The D3 live review audit is recorded in docs/stage_d/D3_LIVE_REVIEW_AUDIT_2026-11-01.md.
- D2 remains PASS_SCOPED_WITH_LIMITATIONS at exact closure HEAD 46c86795d64311b53106fb0b7a79f8bcde116112. Current D1 and D1-D2 source validation runs 41341008321 and 41341008307 passed on baseline HEAD 454b30b.
- D3 remains BLOCKED. Runs 41340409949 (4 passed/1 failed: constants parser), 41340511093 (5 tests passed, build audit FORMULA_OR_ERROR_CELLS_FOUND), and 41341008368 (5 passed/1 failed: NameError rosafe_append) all failed. Latest failure is in constants_from_reference(); the current source calls undefined rosafe_append instead of rows.append. The previous formula/error audit does not report separate counts; full workbook safety remains unverified.
- No workbook, manifest, build audit, D3 remote evidence ledger, Actions artifact, or final exact-head output readback exists. deliverables/ is absent. D3 has not closed; D4 remains NOT_STARTED.
- Registry scope and limitations are unchanged: 20 S6 daily scenarios, 1,000 series, 2,086,550 daily points, 105 representative keys / 1,680 numeric entries; C100 daily distributions and representative raw P50 daily logs are missing, as are detailed ASSETS, ACCTG, PARTNER, GUARANTEE, CONTRACTS and final close-date data. Five historical accounting fields remain MISSING_EVIDENCE and must not be inferred or zero-filled.
- Preserve all gates: financial Gate A PASS_SCOPED only; production Gate A NOT_DECLARED; Gate B N=2400 FAIL_SCOPED (10/10); Stability NOT_CONVERGED (0/60); N=4800 NOT_EXECUTED; Full Logging 105 representative keys only / NOT_VERIFIED_105_OF_105; C100 Golden NOT_RUN.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, main update, PR, merge, Release or D4 transition. Await the owner's explicit continuation instruction.


---

## إشعار إصدار منقح شامل — REV2 — 2026-11-01 (إضافة Append-only)

تم نشر الإصدار التشغيلي المنقح الشامل في الملف التالي، وهو المرجع الأحدث لاستخدام المكتبة من تاريخ نشره:

- [PROJECT_PROMPT_LIBRARY_AR_2026-11-01_REV2.md](PROJECT_PROMPT_LIBRARY_AR_2026-11-01_REV2.md)
- Raw download: https://raw.githubusercontent.com/yasmin977209-ux/motorcycle-simulation/tmp/d1-rebuild-20261101/docs/stage_d/PROJECT_PROMPT_LIBRARY_AR_2026-11-01_REV2.md

سبب الإصدار الجديد: النسخة التاريخية أعلاه كانت ما تزال تصف D2 بأنها NOT_STARTED وتوجه إلى بدء D2، بينما سجل D3 الحي يثبت إغلاق D2 بحالة PASS_SCOPED_WITH_LIMITATIONS وأن D3 BLOCKED / BLOCKED_MISSING_EVIDENCE. كما أن محاولات D3 وأسباب فشلها وفجوات المخرجات لم تكن ممثلة في توجيه الاستئناف الأعلى أولوية.

**قاعدة الاستخدام:** احتفظ بمحتوى هذه النسخة كما كان لأغراض التاريخ والتتبع. استخدم REV2 بوصفها المكتبة التشغيلية الأحدث. لا تعتبر هذا الإشعار وحده إثباتاً لحالة أي مرحلة؛ أعد التحقق من GitHub في كل جلسة.


## D3 candidate build — 2026-11-01

- D2 was revalidated closed before D3; D3 candidate generation was explicitly requested in this session.
- Output commit: ddf0e9c64066d3123f2b8a82900123f04986ea42; workflow run: 41350404125.
- Candidate classification: T2_INTERIM / NOT_FINAL_BLOCKED.
- Two 185-sheet workbooks were generated from results/number_registry.json only; see D3 remote evidence ledger.
- D3 remains BLOCKED_MISSING_EVIDENCE: C100 daily distributions, representative P50 daily logs, detailed asset/accounting/partner/guarantee/contracts ledgers and closure-date distributions are not represented in Number Registry.
- No D4, Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, main update, PR, merge or Release.
