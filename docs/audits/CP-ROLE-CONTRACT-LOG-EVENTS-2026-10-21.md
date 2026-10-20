# CP — عقد الأدوار و `log_events` — 2026-10-21

**الحالة الحالية:** `PHASE_1_PARTIAL / MAXCASE_PAYLOAD_BLOCKED`؛ هذا تقرير واحد يجري استكماله بعد تحليل المرحلة 2.
**النطاق:** قراءة الأدلة الموجودة فقط. لا تعديل كود/اختبارات/Workflows/بيانات/Parquet، ولا تشغيل Trial أو Monte Carlo أو CS، ولا إنتاج ملفات التسليم.
**مرجع السلطة:** البايتات المحلية للمرجع الأصلي SHA-256 `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479` (271,496 bytes، HASH VERIFIED).
**المصدر المراجع:** `docs/governance/DECISIONS_LOG.md` blob `df4910e6a86bcce84f6b71d6d260913800474f95`; `docs/governance/REFERENCE_AMENDMENTS.md` blob `b4eab80bf657d72e9e49d14db81d2baf0a462d77`.

## المرحلة 1 — عقد الأدوار

### الأدلة وهويتها

- D-2026-10-10-03 موجود في سجل القرارات وحالته `APPROVED — NORMATIVE`; Amendment-03 موجود. المعيار: P50 أقرب وسيط `Final_Net_Project_Equity`؛ P10/P90 الأقرب إلى quantile 0.10/0.90؛ LossCase أقل `abs(Final_Net_Project_Equity)`؛ MaxCase أعلى قيمة **موجبة**؛ كسر التعادل لجميع الأدوار بأقل `trial_id`. إذا لم توجد قيمة موجبة لـMaxCase تكون `UNDEFINED_BUSINESS_RULE` ويُحجب اعتماد السيناريو.
- V3 artifact: ID `11503510055`, Run `37662891608`, producer SHA `6128b22864bb171ba49ec15dbb42439a6513c30c`, ZIP 17,787,110 bytes, SHA-256 `111eb7a2abd7b85625a02c55ee6f3140a14644ef253141bfdc3f8fc5ae4c287d`. Metadata: scenario `C050_G000`, official source run `37225915321`, source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, 450 trials, fingerprint reconciliation `450/450`, date range `2027-01-01` to `2033-02-12`, 2,235 aggregate `DAILY_DISTRIBUTION` dates.
- V3 `trial_fingerprints.json`: 450 unique contiguous IDs 1..450, SHA-256 `82cb7a2725944edc3b749bcc722d22040459baac2db6c68f3c0ddde98b0db8f6`. `trial_results.parquet` 28,825 bytes, SHA-256 `09c223d8348f93a5c5e9246a409614d6345a76b224ff65f865c6bdbaea5fbbe8`; `daily_distribution.parquet` 137,290 bytes, SHA-256 `caf8de98e7e907b01cb87ee2cfc879293a3acb740290f0d2a8ab6867ebb13cd3`.
- The local host has no PyArrow/fastparquet; installing PyArrow was blocked by DNS. Therefore the V3 TrialResult Parquet bytes were hash-verified but not independently decoded row-by-row here. Existing official Stage 12 read-only verifier Run `39309810806`, tested SHA `23162f417dba32192f1ec2a8d34b1d5bc461bc9a`, Artifact `12215292742` reports row-level fingerprint binding and daily continuity across the 25-scenario 11,005-trial canonical cohort; this is cross-evidence, not a claim that this session parsed the V3 Parquet directly.
- The selected-role register `docs/stage9a/representative_trial_ids.json` blob `caf392ac015f9ba9f5e4bdac6e7fef7062bcf6d9` records `method=numpy.quantile(method=linear)`, `criterion=Final_Net_Project_Equity`, `tie_break=min_trial_id`, generated `2026-10-07T15:49:18.186Z`, with IDs and final-equity values shown below.
- Each existing V3 representative JSON was read and checked: summary scenario and trial ID, non-empty daily array, exact same trial ID throughout, contiguous daily dates beginning 2027-01-01 and ending at the summary `final_close_date`, and last-day Cash/Net_Equity/Cumulative_Project_Profit matching the summary. The four files are byte-identical between V2 and V3.

### جدول الأدوار

| الدور المعياري | الحالة | ملف/مصدر V3 | قاعدة الاختيار | الدليل المتحقق |
|---|---|---|---|---|
| P50 | `PASS_SCOPED` للوجود والربط | `representatives/P50.json`; `trial_id=29` | أقرب `Final_Net_Project_Equity` إلى quantile 0.50 (linear)، tie → أصغر ID | القيمة النهائية 276,669,500؛ 2,235 صفًا يوميًا؛ 2027-01-01 → 2033-02-12؛ كل صفوف DAILY تحمل ID 29؛ الحقول النهائية تطابق الملخص. payload SHA-256 `5b377dbd4868cbb165a6925916051c375ad0c031636224e3b08560196656b3e8`. |
| P10 | `PASS_SCOPED` للوجود والربط | `representatives/P10.json`; `trial_id=131` | أقرب إلى quantile 0.10 (linear)، tie → أصغر ID | القيمة 265,600,350؛ 2,226 صفًا يوميًا؛ الإغلاق 2033-02-03؛ كل الصفوف تحمل ID 131؛ نهاية DAILY تطابق الملخص. SHA-256 `3191b3def023762e42e23d9a8a73235e5e78b94757d17b691f19f4e37ab477d5`. |
| P90 | `PASS_SCOPED` للوجود والربط | `representatives/P90.json`; `trial_id=18` | أقرب إلى quantile 0.90 (linear)، tie → أصغر ID | القيمة 288,621,050؛ 2,228 صفًا يوميًا؛ الإغلاق 2033-02-05؛ كل الصفوف تحمل ID 18؛ نهاية DAILY تطابق الملخص. SHA-256 `7742dccd6ac8433542cb577e583310891b07104fb2af895a663705d70c2886c4`. |
| LossCase | `PASS_SCOPED` كربط للملف القديم؛ إعادة حساب الترتيب الخام ليست مستقلة في هذا المضيف | الملف القديم `representatives/Loss.json`; `trial_id=304` | أقل `abs(Final_Net_Project_Equity)`، بغض النظر عن الإشارة؛ tie → أصغر ID | السجل الرسمي يسجل `Loss=304` و`Loss_value=249,030,500`؛ payload summary مطابق؛ 2,233 صفًا يوميًا؛ الإغلاق 2033-02-10؛ كل الصفوف تحمل ID 304. SHA-256 `34be00c541604e6bb13e80b3e10ae6f95109bdc3ce76d64661f58f81f484164c`. لا تعارض نصيًا مع §14.6 الأصلي أو Amendment-03؛ يلزم mapping صريح من الدور LossCase إلى اسم الملف القديم Loss.json. |
| MaxCase | `MISSING_EVIDENCE / PENDING_DATA_SOURCE` — لا يوجد payload خام خامس داخل V3 | لا يوجد `representatives/MaxCase.json` في V3؛ `daily_distribution.parquet` تجميعي وليس دفترًا يوميًا لتكرار واحد | أعلى `Final_Net_Project_Equity` موجبة؛ tie → أصغر ID؛ لا قيمة موجبة → `UNDEFINED_BUSINESS_RULE` | تحقق مستقل سابق من Run Stage 12 `37964656154` وArtifact `11634501915` أثبت لـC050_G000: `trial_id=60`, `Final_Net_Project_Equity=308,412,450`, 2,235 صفًا يوميًا (2027-01-01 → 2033-02-12)؛ بصمة عضو DAILY `6beecb837a3c6b71f34aedbeb958e8dd176cce3d60b2dfa1b95ee9bd57e6a380`، ودليل الاختيار/ربط النتيجة موجود في Artifact `12215292742`. لكنه ليس payload من V3، وملف V3 لا يحمل اليوميات الكاملة لـID 60. |

### فحص DAILY ونتيجة المرحلة الأولى

- V3 يحتوي أربعة payloads فقط؛ أحجامها: Loss 314,218,180 bytes، P10 332,102,108، P50 342,536,957، P90 356,570,015. لم يُعثر على ملف خامس.
- سجلات DAILY الأربعة الحالية كاملة زمنيًا، ومربوطة بوضوح بالـtrial IDs أعلاه. لا يُعد `daily_distribution.parquet` بدلًا عن سجل يومي خام لكل TrialResult.
- سجل Stage 12 لـMaxCase يفتقد أعمدة يومية مطلوبة في payload الحالي: `Partner1_Reinvestment_Balance`, `Partner2_Reinvestment_Balance`, و`Cumulative_Project_Profit`. يوجد `Retained_Earnings` لكن لا يوجد قرار نافذ يقرر تكافؤه مع `Cumulative_Project_Profit`. لذلك لا يمكن تكوين خامس payload مطابق للعقد من هذه الأعمدة دون توجيه مالك؛ لا تخمين أو أصفار أو إعادة تشغيل.
- **الاستنتاج:** عُرف ID/قاعدة MaxCase بواسطة دليل مصدر موجود، لكن شرط «الدور موجود في V3 مع payload كامل» غير متحقق. عقد الأدوار العام ليس مغلقًا؛ `Stage 13 production = BLOCKED`. المطلوب من المالك اختيار سياسة نقص بيانات MaxCase قبل أي تغيير تنفيذي.
- لا تغييرات كود/اختبارات/Workflows/بيانات/Parquet تمت. لم أشغّل Test أو Trial أو Checkpoint أو Monte Carlo أو CS.

### القرارات الذاتية وحدودها

1. اعتمدت mapping للـP10/P50/P90 وفق الملف الرسمي وقاعدة quantile المسجلة، مع التحقق من daily binding.
2. اعتبرت `Loss.json` مرشح الملف القديم لدور LossCase لأن القاعدة في المرجع الأصلي وAmendment-03 متوافقتان؛ لن أغيّر اسم الملف داخل المصدر ولا أنفّذ أي كتابة بيانات.
3. لم أعتبر MaxCase مقبولًا من مجرد وجود صف Stage 12؛ غياب payload من V3 والحقول اليومية غير المتاحة يبقيانه معلقًا.
4. لا تنتقل حالة `PASS_SCOPED` للربط اليومي إلى قبول Stage 13 أو التسليم النهائي.

### أسئلة قرار المالك — مرحلة 1

- **MaxCase:** (A) إبقاء Stage 13 محجوبًا حتى يتوفر payload يومي كامل مطابق من مصدر معتمد ومطابق الهوية؛ أو (B) السماح صراحةً بتمثيل جزئي يستند إلى سجل Stage 12، مع ترك حقول الشريك و`Cumulative_Project_Profit` فارغة وموسومة `PENDING_DATA_SOURCE` وقبول ذلك في عقد المخرجات. لن تُجرى إعادة تشغيل Trial ضمن هذا النطاق.
- **LossCase:** لا أطلب تغيير قاعدة الأعمال؛ أطلب فقط إقرارًا بأن الاسم القديم `Loss.json` يُربط صراحةً إلى الدور المعياري `LossCase` في loader/mapping المستقبلي. حتى ذلك الحين يبقى هذا mapping موثقًا كمرشح لا تعديل للمصدر.

### اختبارات الحراسة المقترحة (لم تُشغّل)

1. اختيار P10/P50/P90 باستخدام quantile الخطي المحدد؛ كسر التعادل بأصغر integer `trial_id`.
2. اختيار LossCase كأقل قيمة مطلقة، لا أقل قيمة موقعة؛ واختبار حالة التعادل وعلامتي القيمة الموجبة/السالبة.
3. اختيار MaxCase كأعلى قيمة موجبة؛ tie → أصغر ID؛ لا قيمة موجبة → `UNDEFINED_BUSINESS_RULE` وفشل قبول السيناريو.
4. التحقق من mapping صريح للأسماء الخمسة، ومنع استنتاج اسم ملف من الدور دون mapping معتمد؛ اختبار `LossCase -> Loss.json` صراحةً.
5. رفض payload إذا اختلف `scenario_id` أو `trial_id` بين assignment وTrialResult/summary/أي صف DAILY.
6. رفض صف DAILY مفقود/مكرر/غير متصل، أو تاريخ نهائي/رصيد نهائي لا يطابق summary، أو fingerprint/source/seed/cohort لا يطابق الهوية المعتمدة.
7. غياب MaxCase payload مع بقاء شرط الخمسة أدوار يجب أن يبقى BLOCKED؛ أي مسار pending-data لا يقبل إلا بقرار مكتوب ولا يصطنع أرصدة.

## المرحلة 2 — تحليل `log_events`

`PENDING_ANALYSIS` — ستضاف هنا بعد إنهاء مقارنة تاريخ validator وسلوك V2/V3، دون أي تعديل على artifact أو validator.

## الحالة العامة المحفوظة

`C050_G000 V3 = temporary only`; `log_events = PENDING_APPROVAL`; Gate A `BLOCKED`; Stage 9C `PARTIAL/CONFLICTED`; delivery `NOT_ACCEPTED`; Release `BLOCKED / NOT_AUTHORIZED`.
