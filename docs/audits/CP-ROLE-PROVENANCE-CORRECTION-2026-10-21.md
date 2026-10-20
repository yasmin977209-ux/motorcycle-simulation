# CP — تصحيح تقرير عقد الأدوار وأدلة provenance — 2026-10-21

**الحالة:** تصحيح توثيقي فقط؛ لا تغيير كود أو اختبار أو Workflow أو بيانات أو Parquet.
**الفرع:** `tmp/cp-session-continuity-20261017`
**المرجع الأصلي:** SHA-256 `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479` (تمت إعادة مطابقة بايتات الملف المحلي).
**التقرير السابق المحفوظ دون تعديل:** `docs/audits/CP-ROLE-CONTRACT-LOG-EVENTS-2026-10-21.md`, blob `804a682ddf8b6797173de7d5e461f0a9a5ee34d1`.

## 1. تصحيح عقد `Cumulative_Project_Profit`

التقرير السابق ذكر أن العلاقة بين `Cumulative_Project_Profit` و`Retained_Earnings` لا يحسمها قرار نافذ. هذا الوصف غير صحيح ويُصحّح هنا دون حذف التقرير التاريخي.

- المرجع الأصلي §10.9 يعرّف `Retained_Earnings_current = Opening_Loss + Cumulative_Operating_Net_Profit_since_start`.
- المرجع الأصلي §10.10 يعرّف `Cumulative_Project_Profit = Opening_Loss + Operating_Net_Profit`، وينص صراحةً على أن ذلك يساوي دائماً `Final_Retained_Earnings` عند أي لحظة.
- البصمة المحسوبة للمرجع المحلي: `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`.
- تأييد تنفيذي عند المصدر المثبت `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`: `accounting.py` blob `8bbbfacbefa4290dd3efbdee2aee3cc7661a42b4` يحسب `project.cumulative_project_profit` ثم يعيّن `project.retained_earnings = project.cumulative_project_profit`; و`monte_carlo.py` blob `a8c3603487f92d3e15c3d754ce3faee3580a5f46` يصدر `Retained_Earnings` في DAILY snapshot.

**التصرف الصحيح:** يحذف `Cumulative_Project_Profit` من قائمة القرارات/الحقول التي تحتاج قرار مالك. يجوز اشتقاقه من `Retained_Earnings` فقط بعد إثبات تطابق trial والتاريخ وهوية المصدر، ودون أي تحويل مالي أو تقريب. هذا لا يحسم نقص أرصدة Memo للشريكين، ولا يثبت أن سجل MaxCase اليومي الناقص موجود.

## 2. عيب اختبار provenance — اكتشاف على مرشح قديم، لا على main

الـArtifact المرفق `stage13-integration-evidence-39473433150.zip` يخص Run `39473433150` على الفرع المرشح القديم `tmp/cp-stage13-integration-20261020`، مع `tested_sha=493cbe515afc081d6dcbf34d39b0952b0d36dccc`. الاختبارات المسجلة `50 passed` هي اختبارات اصطناعية/توافقية وليست إثباتًا ذاتيًا لصحة provenance الخارجية.

- اختبار `test_source_audit_accepts_exact_representative_inventory_identity` في `tests/test_stage13_assembler.py`, blob `fc56eb36d3f5b8aa19e06db3db4097fc24cf0bf4`، يمرر tuple يتضمن Artifact `11503191706` وRun `37662891608` ثم يتوقع عدم وجود mismatch.
- الدليل المقارن الفعلي المثبت في تقرير V2/V3 يربط Artifact V2 `11503191706` بـRun `37660610243`، بينما Artifact V3 `11503510055` مرتبط بـRun `37662891608`. بالتالي tuple الاختبار يجمع Artifact V2 مع Run V3، وهو زوج غير صحيح.
- الدالة `inventory_identity_mismatches()` في `scripts/stage13_maxcase_source_audit.py`, blob `f7835b5a6f2584f9a0679a496b565a5a229f6b4c` على المرشح، تقارن قيم manifest بالقيم التي يعطيها الاختبار؛ لا تستعلم بذاتها من GitHub API لإثبات أن tuple يطابق Artifact المنتج الفعلي. لذلك يمكن للاختبار أن ينجح عند تكرار زوج خاطئ في fixture وmanifest معًا.
- على `main`, manifest blob `e796fa2443493b607f1f9c60b58eb63607959c26` يربط `C050_G000` بـArtifact `11503191706` وRun `37662891608`; وهذا تعارض provenance موثق سابقًا. manifest المرشح blob `ec0d4749f86c6f81d743dbb071f92e9f0eddef3d` يربط V3 `11503510055` بـRun `37662891608` على نحو يطابق سجل Artifact API.
- التصنيف: `K_TEST / DATA-PROVENANCE` للمرشح القديم. لا يُنقل هذا الحكم إلى `main` أو إلى CI المسار 4 الأحدث، ولا يعني أن كل اختبار في الـRun القديم فشل.

**حدود التصحيح:** لا اختبار عُدّل أو عُطّل أو وُسم skip؛ لا manifest أو Artifact أو بيانات تاريخية تغيّرت؛ ولم يُعد تشغيل أي Run.

## 3. عقد الأدوار بعد التصحيح

- P10=131، P50=29، P90=18: `PASS_SCOPED` لوجود الحمولة وربطها، لا لإعادة حساب جميع صفوف Parquet محليًا.
- LossCase=304 من الملف القديم `representatives/Loss.json`: `PASS_SCOPED_MAPPING`، ويجب حفظ الربط المعياري صراحةً دون اختراع filename بديل.
- MaxCase: لا يوجد `representatives/MaxCase.json` في V3. Trial 60 يأتي من دليل Stage 12 لكوهورت أكبر (11,005 trials)، ولا يثبت وحده أن trial 60 هو الأعلى في V3 ذات 450 trial. يلزم فحص صفوف `trial_results.parquet` من V3 نفسها قبل تحديد MaxCase الفعلي.
- `Partner1_Reinvestment_Balance` و`Partner2_Reinvestment_Balance`: ما زالت `MISSING_EVIDENCE / PENDING_DATA_SOURCE` في حمولة MaxCase. لا اشتقاق من Cash أو Net Equity أو الأرباح المرحّلة، ولا أصفار، ولا إعادة Trials.
- لأن صفوف `trial_results.parquet` في V3 لم تُفك محليًا في الفحص السابق (قارئ Parquet غير متاح وتعذر تثبيت الاعتماد عبر DNS)، لا يُدّعى هنا أن MaxCase V3 حُسم.

## 4. حالة `log_events` والبوابات

- `C050_G000`: V3 (`11503510055` / Run `37662891608`) معتمد مؤقتًا من ناحية provenance فقط.
- `log_events contract = PENDING_APPROVAL; V3 metadata used provisionally`. لا تعديل للـvalidator أو metadata في هذا CP.
- Gate A: `BLOCKED`؛ لم يتم ربط provider.
- Stage 9C التاريخية: `PARTIAL` محفوظة، وحالة إغلاقها `CONFLICTED`.
- لا تغيير في `main`, `SOURCE_SHA`, seed/RNG, cohort, trial IDs, Parquet أو manifest. لم يجر تشغيل CI جديد أو اختبار أو محاكاة أو Trial أو CS.
- التسليم `NOT_ACCEPTED`; Release `BLOCKED / NOT_AUTHORIZED`.

## 5. الخطوة التالية المقترحة

فصل R4 لعيب اختبار provenance قبل أي تعديل: (1) إصلاح اختبار التوقعات ضد الهوية الخارجية المثبتة، أو (2) استبعاد هذا الاختبار من أدلة قبول provenance إلى أن يُصحح، أو (3) تعطيله مؤقتًا بـskip موثق. لا يُنفذ أي خيار قبل قرار المالك. بعد قرار المالك فقط، يستمر مسار التحقق من V3 نفسها ومصدر أرصدة الشركاء؛ لا يُنتج P16 أو الملفات السبعة ضمن هذا التصحيح التوثيقي.
