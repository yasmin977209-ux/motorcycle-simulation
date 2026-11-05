# مكتبة البرومبتات التشغيلية الشاملة — Motorcycle Simulation
## REV4 | إعادة تنظيم كاملة، بوابات صفر فجوات، وحفظ الأدلة | 2026-11-05

**الحالة:** النسخة التشغيلية الأحدث. تعلو على REV3 وREV2 في ترتيب البرومبتات، شروط الدخول والخروج، سياسة الاحتفاظ، وتعريف الإغلاق الكامل.  
**Repository:** yasmin977209-ux/motorcycle-simulation  
**Working branch:** tmp/d1-rebuild-20261101  
**Parent HEAD:** 522fc266436893add3dc4d447afdbc8f999ffda4  
**main HEAD:** 01a6f79eedc522bb734ed9c5ea31beee581f2468  
**Governing reference:** v2.4.0 — D-2026-10-30-REFERENCE-V2.4.0 — APPROVED_BY_OWNER.

> هذه المكتبة لا تعدل قواعد العمل أو المرجع ولا تمنح صلاحية محمية. هدفها جعل كل مرحلة قابلة للتدقيق وإيقاف الانتقال عند أي نقص. لا يمكن تحويل الدليل المفقود إلى حقيقة بمجرد إعادة صياغة البرومبت.

---

# 1. القرار الهندسي الحاكم

## 1.1 تعريف الإغلاق

يجب التمييز بين:
1. **إغلاق نطاقي موثق:** نُفذ نطاق محدود من المتطلبات مع قيود معلنة، مثل PASS_SCOPED_WITH_LIMITATIONS.
2. **إغلاق كامل دون فجوات:** كل المتطلبات الإلزامية مثبتة بدليل حي، كل الاختبارات الإلزامية نُفذت ونجحت، كل التعارضات عولجت، كل المخرجات محفوظة بصورة دائمة، ولا توجد عناصر NOT_RUN أو MISSING_EVIDENCE أو NOT_VERIFIED أو CONFLICTED أو REPORTED_ONLY أو BLOCKED.
3. **قبول المشروع النهائي:** قرار مستقل في نهاية E6، ولا ينتج من D6 أو E2 أو نجاح Actions.

الحالة التاريخية الحالية للمشروع إغلاقات نطاقية وليست gap-free. لا تصف المشروع بأنه مكتمل أو نهائي.

## 1.2 Hard Stop — صفر فجوات

لا يسمح بالانتقال من مرحلة إلى التالية إلا إذا:
- كل requirement إلزامي له مصدر أصلي محدد، evidence URL، SHA-256 من bytes، Git blob SHA-1، size، containing commit، test result، وlineage.
- كل اختبار إلزامي نُفذ فعلياً على source/identity الصحيح؛ لا يُستبدل باختبار مشابه دون اعتماد موثق.
- لا يوجد NOT_RUN أو MISSING_EVIDENCE أو NOT_VERIFIED أو CONFLICTED أو REPORTED_ONLY أو BLOCKED في أي requirement إلزامي.
- لا توجد فروق غير مفسرة بين source bytes وartifact bytes وmanifest وworkbook/report/package.
- كل Artifact مطلوب حُفظت بايتاته في نسختين دائمتين مستقلتين وتم اختبار استعادته.
- عولجت جميع عيوب الكود والاختبارات والتوثيق وlineage، وأعيد تشغيل الاختبارات المتأثرة.
- تم Raw readback بعد Commit وexact final HEAD validation.
- لا تُنسب نتيجة Run إلى SHA مختلف.

**PASS_SCOPED وPASS_SCOPED_WITH_LIMITATIONS لا يحققان شرط صفر فجوات.** إذا تعذر شرط واحد فالمرحلة BLOCKED؛ عالج المانع المحدد فقط ولا تتجاوز المرحلة ولا تخفّض معيار الدليل.

## 1.3 السلطة

1. قرارات المالك الصريحة وحدودها.
2. المرجع الحاكم v2.4.0 وفق D-2026-10-30-REFERENCE-V2.4.0 بحالة APPROVED_BY_OWNER.
3. أدلة GitHub الحية ذات الهوية والـCommit المثبتين.
4. مصفوفات المتطلبات وسجلات التصحيح Append-only.
5. مكتبة REV4.
6. REV3/REV2 والملفات الأقدم كسجلات تاريخية فقط.

مرجع التنفيذ التاريخي v2.3 منفصل عن current_governing_reference_sha256 لـv2.4.0. رأس v2.4.0 الذي يقول PROPOSED متعارض نصياً مع قرار المالك APPROVED_BY_OWNER؛ القرار هو الحاكم. لا تعدل بايتات المرجع دون قرار مالك.

## 1.4 الصلاحيات

مسموح: قراءة GitHub، تدقيق الملفات والـArtifacts، إصلاح العيوب التقنية التي لا تغير business rules أو الهوية أو العتبات، تحديث الوثائق Append-only، commits على فرع العمل، تشغيل الاختبارات المصرح بها، وإنشاء Draft PR بعد اجتياز البوابات.

يتطلب قرار مالك منفصل: تغيير business rules/reference/thresholds/inference؛ تغيير SOURCE_SHA/cohort_id/MASTER_SEED/Trial identity؛ Trials/Simulation/Monte Carlo/Golden revalidation/N expansion/N=4800 خارج التفويض المحدد؛ backfill أو تخمين أو zero-fill؛ تعديل/حذف Artifact أو manifest تاريخي؛ تعديل main أو merge أو force-push أو حذف التاريخ؛ نشر Release؛ إعلان FINAL_ACCEPTED أو P17_FINAL_ACCEPTED أو P18_RELEASED أو CONVERGED.

اسم المرحلة وحده يجيز الأعمال الواقعة ضمن صلاحياتها فقط ولا يمثل موافقة لأي إجراء محمي.

## 1.5 حدود الوكيل

لا تدّعِ حفظ ملف في هاتف المالك أو وسيط لا يمكن الوصول إليه. لا تعتبر signed URL مؤقتة نسخة دائمة. لا تعتبر metadata digest إعادة حساب مستقلة لـZIP. لا تدّعِ أن Actions Artifact سيبقى بعد expiry. لا تضمن إنهاء المشروع قبل expiry إذا كانت القرارات أو الاختبارات أو الوجهة الدائمة غير متاحة؛ الأولوية لمنع ضياع الأدلة لا لاختصار الاختبارات. لا تطلب إعادة رفع ملف موجود في GitHub.

---

# 2. الحالة الحية التي يجب تصحيحها عند الاستئناف

## 2.1 Baseline عند إعداد REV4

لقطة ما قبل نشر REV4 ويجب إعادة جلبها:
- Branch: tmp/d1-rebuild-20261101
- Pre-write branch HEAD: 522fc266436893add3dc4d447afdbc8f999ffda4
- main HEAD: 01a6f79eedc522bb734ed9c5ea31beee581f2468
- Compare: diverged؛ ahead 955 / behind 2؛ merge base c6e54349a5e94f65d5aa9f83141f225d777bb474.

لا تعدّل main ولا تدمج. أي Commit جديد يغير HEAD؛ أعد فحص Actions على SHA الجديد.

## 2.2 الحالة المرحلية الحالية

| المرحلة | الحالة التاريخية | القيد الذي يمنع وصفها gap-free |
|---|---|---|
| D0 | PASS_SCOPED_WITH_LIMITATIONS | Parquet schema/row counts و48K detailed ledgers والحقول الخمسة غير مثبتة بالكامل |
| D1 | PASS_SCOPED_WITH_LIMITATIONS | 105 normalized manifest statuses NOT_VERIFIED عند غياب expected byte sizes؛ Full Logging 105 مفاتيح فقط |
| D2 | PASS_SCOPED_WITH_LIMITATIONS | Registry نطاقي: 2,640 entries، 1,000 daily series، 2,086,550 daily points؛ لا يثبت 48K ledgers |
| D3 | PASS_SCOPED_WITH_LIMITATIONS | D3-18 requirement invocation NOT_RUN؛ تقسيم السيناريوهات لم يُنفذ بعد |
| D4 | PASS_SCOPED_WITH_LIMITATIONS | Test 176 وfull numeric-token-to-Registry lineage غير مثبتين |
| D5 | PASS_SCOPED_WITH_LIMITATIONS | Full 177-unique-test suite NOT_RUN |
| D6 | PASS_SCOPED_WITH_LIMITATIONS | Tests 176/179/180/181/183 NOT_RUN؛ historical invocations 175/182/186 لم تُنفذ كاختبارات تاريخية |
| E0 | PASS_SCOPED | gap inventory فقط؛ فجوات قائمة في سجل 15 gap و28 output |
| E1 | PASS_SCOPED | تسوية وثائقية/حوكمية؛ لا تمحو فجوات البيانات ولا تمنح الموافقات المحمية |
| E2 | PASS_SCOPED + PASS_SCOPED_REPLAY_RECONSTRUCTION | old-identity replay نجح لكنه ليس original historical evidence؛ الحقول الخمسة التاريخية مفقودة وProduction Gate A غير معلن؛ new S6/C100 تنتظر تأكيد المالك |
| E3–E6 | NOT_STARTED | لا تبدأ قبل إغلاق D0–D6 وE0–E2 دون فجوات والاحتفاظ الدائم |

التصنيف العام T2_INTERIM / NOT_FINAL_BLOCKED.  
FINAL_ACCEPTED وP17_FINAL_ACCEPTED وP18_RELEASED وCONVERGED = NOT_DECLARED.

## 2.3 تصحيحات التعارضات الحاكمة

- سجل D0_D6_MASTER_CLOSURE الأقدم الذي يقول E0–E6 لم تبدأ أصبح قديماً جزئياً؛ E0/E1/E2 لها سجلات تنفيذ لاحقة. استخدم E0/E1/E2 continuity وE2 gap disposition اللاحقة ولا تمحُ السجل القديم.
- D3 Artifact 13288779998 مصدره Run 41754147172، tested SHA 3325fd961005c2c47de071d25904a748af7a21a6. Run 41914970361 هو Acceptance Run منفصل.
- D3-18: artifact-level PASS_SCOPED لا يعني أن requirement invocation تم؛ تظل NOT_RUN حتى دليل تنفيذ مباشر.
- D5 tested SHA baf696af1e951cbf4a79e8a9e009c60c6b053b2d منفصل عن publication-evidence commit 4c6a84b10ac78b6067175d0eafa149f3f12dbc2a.
- لا تنسب D5/D6 Runs إلى HEAD أحدث من tested SHA.
- E2 Run 41958935113 نجح كـold-identity replay reconstruction باستخدام execution commit a23ba71f48487f3ebead99bc30039b14ef9b7609، old SOURCE_SHA da1a9ea9b5cd789c944de3f07b08395bb67c49e7، cohort s6-v23-da1a9ea9، MASTER_SEED 20270101. لا يمثل تنفيذ source/cohort الجديدين.
- موافقة Option A تخص replay للهوية القديمة المحددة فقط، ولا تمنح إذناً للسلالة الجديدة S6/C100 أو E3 أو N expansion.

## 2.4 ثوابت لا يجوز ترقيتها

- Financial Gate A: PASS_SCOPED فقط.
- Production Gate A: NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS.
- Gate B N=2400: FAIL_SCOPED (10/10).
- Stability: NOT_CONVERGED (0/60).
- N=4800: NOT_EXECUTED.
- Full Logging: 105 representative unique keys فقط، وليس 48K full logging.
- Normalized manifest: 105/105 NOT_VERIFIED حيث تغيب expected byte sizes المستقلة.
- C100 Golden revalidation: NOT_RUN.
- Full 177-test suite: NOT_RUN.
- Potential_Coverage_Cells=604 حساب محتمل فقط؛ Required_Output_Coverage_Cells=PENDING_MATRIX_VALIDATION.
- لا تخلط 125 role assignments مع 105 unique keys.
- الحقول الخمسة التاريخية MISSING_EVIDENCE ولا تخمنها أو تصفرها أو تستنتجها: Accounts_Receivable، Accumulated_Depreciation، Gross_Bike_Assets، Guarantee_Claim_Receivable، Total_Assets.
- افصل S6 وC100 وStage 12/13.

---

# 3. سياسة الأدلة والاحتفاظ

## 3.1 ثلاثية إثبات الملفات

لا تستخدم VERIFIED_LIVE إلا عند توفر:
1. رابط Raw GitHub دقيق إلى المسار والـCommit.
2. SHA-256 محسوبة من bytes المسترجعة فعلياً.
3. Commit SHA يحتوي البايتات.

سجل Git blob SHA-1 والحجم بالبايت أيضاً. Git blob SHA-1 وحده لا يثبت SHA-256. عند غياب عنصر استخدم MISSING_EVIDENCE أو REPORTED_ONLY.

للـArtifacts الثنائية: سجل Run/Job/tested SHA/Artifact ID/name/size/GitHub digest/expiry، ثم نزّل exact ID واحسب SHA-256 من ZIP bytes وقارن digest، وافحص CRC وpaths وduplicate entries وmanifest/member hashes وsource identity. Metadata digest لا يساوي إعادة hashing مستقلة.

## 3.2 Artifacts المسجلة عند فحص 2026-11-05

أعيد التحقق من 29 Artifact عبر Actions API وكانت كلها expired=false. المجموع 5,233,477,368 bytes (4.874 GiB). 23 Artifact تتجاوز 100 MiB، بمجموع 5,223,738,531 bytes (4.865 GiB).

| العنصر | ID | الحجم bytes | Expiry UTC |
|---|---:|---:|---|
| D0 S6 aggregate | 12852969854 | 9,357,996 | 2026-11-27 21:46:36 |
| D3 workbook package | 13288779998 | 535,567,142 | 2026-12-04 02:07:02 |
| D5 package | 13369179742 | 519,116,689 | 2026-12-04 22:49:30 |
| D6 audit | 13371094066 | 6,635 | 2026-12-04 23:14:36 |
| D0-D4 evidence | 13373853115 | 5,706 | 2026-12-04 23:54:10 |
| D0-D4 evidence | 13382253631 | 5,698 | 2026-12-05 02:21:52 |
| C100 reuse | 12630457193 | 361,733 | 2027-01-24 03:18:29 |
| D1 Full Logging | 12998778418 | 310,827,203 | 2027-01-28 17:25:30 |
| E2 scenario artifacts | 20 files | 130–245 MB each | 2027-02-03 03:01:28 |
| E2 aggregate | 13393273763 | 1,069 | 2027-02-03 03:01:28 |

التفاصيل الكاملة في docs/stage_d/D0_D6_E0_E2_RETENTION_INVENTORY_2026-11-05.json. هذه لقطة تاريخية؛ أعد فحص Actions API في كل جلسة.

الأولوية: D0 aggregate أولاً؛ ثم D3/D5/D6 وD0-D4 evidence؛ ثم C100 وD1 Full Logging؛ ثم 20 E2 scenario artifacts والـaggregate. لا تنتظر إغلاق مرحلة لاحقة لحفظ Artifact مهدد بالانتهاء.

## 3.3 تعريف الاحتفاظ الدائم

لا يعد الاحتفاظ دائماً إلا عند:
- نسخة أصلية untouched خارج مدة Actions Artifacts.
- نسخة ثانية مستقلة في failure domain آخر.
- SHA-256 لكل نسخة بعد الكتابة وإعادة القراءة.
- manifest يربط كل نسخة بالـRun/Artifact/tested SHA/source identity.
- اختبار restore ناجح.

الهاتف: نسخة يدوية لا يستطيع الوكيل التحقق منها مباشرة؛ لا تسجلها محفوظة إلا بعد تأكيد المالك ووجود الحجم/البصمة للمطابقة. الهاتف وحده ليس نسختين مستقلتين.
التخزين الخارجي: لا تستخدم خدمة غير متصلة أو غير مصرح بها.
GitHub Release: لا تنشره؛ يتطلب قرار مالك صريحاً.
Git history: لا يحفظ Actions binary artifacts بعد expiry، ولا تستخدمه لملفات تتجاوز حدود GitHub.

**الحالة عند إعداد REV4: PERMANENT_RETENTION_NOT_COMPLETE / BLOCKED.** ستة تنزيلات سابقة بروابط ChatGPT مؤقتة لا تثبت حفظاً دائماً. لا يوجد إثبات أن المالك حفظها على الهاتف، ولا يوجد archive خارجي دائم.

## 3.4 سياسة الهاتف

عند طلب تنزيل ملفات الهاتف، أعد توليد الرابط من Artifact ID الحي، واعرض الحجم وSHA-256 المسجل مع بيان هل حُسبت من ZIP bytes فعلياً أم أنها metadata فقط. لا تستخدم signed URL قديمة، ولا تدّعِ الكتابة إلى الهاتف. وثّق نسخة الهاتف بعد تأكيد المالك وفحص البصمة إن أمكن، وأوصِ بنسخة ثانية مستقلة.

## 3.5 سجل المرحلة

كل مرحلة تنشئ أو تحدث: Requirements matrix، Test/Run matrix، Defect/remediation register، Evidence ledger، Artifact retention manifest، Closure report، Continuity/Handoff، Raw readback/hashes/exact-head validation. كل تعديل Append-only؛ لا تحذف الأدلة القديمة.

---

# 4. التسلسل التنفيذي

**Bootstrap → Preservation Review → D0 → D1 → D2 → D3 → D4 → D5 → D6 → E0 → E1 → E2 → Global Preservation Gate → E3 → E4 → E5 → E6**

- Preservation Review وGlobal Preservation Gate ضوابط عابرة وليستا مرحلتين جديدتين.
- تقسيم Excel هو D3 sub-gate وليس مرحلة مستقلة.
- لا يبدأ E3 قبل إغلاق D0–D6 وE0–E2 دون فجوات وقبل Global Preservation Gate.
- لا يبدأ E4 قبل إغلاق E3؛ ولا E5 قبل E4؛ ولا E6 قبل E5.
- لا تبدأ عدة مراحل بطلب واحد.
- إذا كانت مرحلة مغلقة سابقاً بنطاق محدود، أعد التحقق من الأدلة الحية فقط ولا تعِد Trials لمجرد بدء دردشة جديدة.
- إذا ظهر نقص في مرحلة سابقة، أوقف المرحلة الحالية وأعد المانع إلى المرحلة المالكة.

## 4.1 Bootstrap

في أول رسالة:
1. استخرج branch HEAD وmain HEAD من GitHub API.
2. قارن ahead/behind/merge-base.
3. اقرأ REV4 وPROJECT_CONTINUITY وSession Status وHandoff وMASTER_EXECUTION_PLAN وE0/E1/E2 continuity.
4. اقرأ قرار اعتماد v2.4.0 والمرجع Raw bytes، واحسب SHA-256 عند الحاجة.
5. اقرأ مصفوفات D0–D6 وE0–E2 وسجلات التصحيح.
6. افحص Actions runs/jobs/artifacts/expiry وPRs/branches/releases.
7. أعد فحص كل Artifact من Actions API؛ لا تعتمد على inventory قديم.
8. أخرج live-state matrix يميز VERIFIED_LIVE وREPORTED_ONLY وMISSING_EVIDENCE وCONFLICTED وNOT_RUN وBLOCKED وPASS_SCOPED.
9. لا تبدأ مرحلة تلقائياً إن لم يرسل المالك اسمها.
10. لا تطلب إعادة رفع ملفات موجودة في GitHub.

## 4.2 Preservation Review

- أعد فحص كل Artifact ID والـexpiry.
- رتب حسب expiry ثم الحجم والأهمية.
- نزّل بالـID الدقيق واحسب SHA-256 من ZIP bytes وافحص ZIP/member integrity.
- أنشئ retention manifest Append-only.
- احفظ نسختين دائمتين في وجهات مصرح بها فقط.
- عند غياب وجهة دائمة أو تأكيد المالك، BLOCKED ولا تدّعِ الاكتمال.
- إذا كان Workflow طويلاً (10 دقائق أو أكثر)، شغله وأبلغ Run ID وCommit SHA ثم توقف ولا تنتظر.

---

# 5. عقد تشغيل موحد

عند إرسال اسم مرحلة:
1. تحقق من GitHub الحي أولاً.
2. حدد آخر requirement غير مغلق وآخر Run/Artifact/Commit مرتبط به.
3. اقرأ الملفات الحاكمة.
4. حدّث matrix قبل أي تعديل.
5. نفذ ما تسمح به الصلاحيات فقط.
6. أصلح العيوب المحددة وأعد الاختبارات المتأثرة.
7. تحقق من المخرجات والـlineage والـhashes.
8. وثق Append-only ثم Commit على فرع العمل.
9. Raw readback لكل ملف بعد Commit، مع SHA-256 وblob SHA-1 والحجم والـCommit.
10. تحقق من exact final HEAD.
11. إذا بقيت فجوة أو قرار مالك أو Artifact غير محفوظ، أوقف المرحلة BLOCKED.
12. لا تنتقل تلقائياً؛ لا تعلن READY_FOR_NEXT_STAGE إلا بعد اجتياز جميع الشروط.

لا تستخدم PASS العام. ولا تصف stage بأنها gap-free إذا بقي شرط إلزامي غير مثبت.

---

# 6. البرومبتات الرئيسية — بالترتيب التنفيذي

## PROMPT 00 — Bootstrap

«ابدأ من GitHub الحي للمستودع yasmin977209-ux/motorcycle-simulation. استخرج HEAD للفرع tmp/d1-rebuild-20261101 وmain عبر API، وقارن الفرعين. اقرأ REV4 والمرجع v2.4.0 وقرار المالك وملفات الاستمرارية والحالة والـhandoff ومصفوفات المراحل وسجلات E0/E1/E2. افحص Actions Runs/Jobs/Artifacts/expiry والـPRs والـReleases. لا تعدّل ولا تشغل Trial أو Simulation أو Monte Carlo. أخرج تقريراً يميز VERIFIED_LIVE عن REPORTED_ONLY وMISSING_EVIDENCE وCONFLICTED وNOT_RUN وBLOCKED، ويحدد أقرب expiry وآخر مرحلة يمكن استئنافها والمانع التالي. لا تبدأ مرحلة تلقائياً.»

## PROMPT 01 — Preservation Review

«راجع كل Artifact في retention inventory من Actions API مباشرة. أعد بناء قائمة IDs/Run IDs/tested SHA/size/digest/expiry. نزّل كل Artifact مطلوب exact ID، واحسب SHA-256 من ZIP bytes وقارن GitHub digest، وافحص CRC/paths/manifest/member hashes. أنشئ retention manifest Append-only. احفظ نسختين مستقلتين دائمتين في وجهات مصرح بها. لا تنشر Release أو تستخدم خدمة غير متصلة دون قرار مالك. لا تدّعِ حفظ الهاتف. إذا لم تتوفر وجهة دائمة، صنف PERMANENT_RETENTION_NOT_COMPLETE / BLOCKED.»

## PROMPT D0 — Input Integrity

«نفذ D0 فقط. تحقق من source identities وRun/Job/Artifact IDs وSHA-256 والحجم وGit blob/commit. افحص ZIP safety وParquet metadata/schema/row counts وTrial/scenario coverage وsource_run_metadata. افصل 125 role assignments عن 105 unique keys. تحقق من وجود السجلات الأصلية لكل 48K Trial. لا تستنتج الحقول المحاسبية الخمسة ولا تستخدم C100 أو Stage 12/13 لسد نقص S6. أخرج matrix لكل requirement. لا تغلق D0 بالكامل إذا بقي schema/row count أو source metadata أو required source evidence غير مثبت.»

## PROMPT D1 — Independent Builder

«نفذ D1 فقط. اقرأ v2.4.0 وقرار D-2026-10-30، وتحقق من bytes وSHA-256 وblob/size/commit. افحص builder/importer ومصدره ونسخة الكود، وأعد بناء مستقلاً من المدخلات المثبتة. شغل اختبارات D1 الإلزامية على exact source. افحص normalized manifest لكل key. لا تخمن expected byte sizes؛ 105/105 NOT_VERIFIED حتى يظهر مصدر مستقل. 105 Full Logging keys لا تعني 48K logging. لا تغلق D1 مع أي requirement غير محسوم.»

## PROMPT D2 — Number Registry

«نفذ D2 فقط. أعد بناء/قراءة Number Registry من المصدر المحدد، وتحقق من 2,640 entries و1,000 daily series و2,086,550 daily points أو ما تثبته البيانات الحية. اختبر uniqueness وreferential integrity وscenario/cohort/source identity وmissing/duplicate keys وfinancial numeric integrity. أثبت الربط من كل قيمة مالية إلى مصدرها وTrial/Date/Scenario. لا تعتبر Registry بديلاً عن 48K detailed ledgers أو كامل Parquet/SQLite. لا تستخدم Stage 12/13 أو C100 لسد فجوات S6.»

## PROMPT D3 — Excel + Scenario Split Sub-gate

«نفذ D3 فقط. اقرأ source workbook bytes الفعلية من GitHub/Artifact؛ Git tree size وحده لا يكفي. تحقق من source identity وmanifest. افحص جميع الأوراق وترتيبها وhidden states وformulas وerrors وnamed ranges وmerged cells وhyperlinks وRTL/LTR وtypes/values/financial formats/print settings وscenario coverage. تحقق من 25 scenario cells (20 random + 5 deterministic C100) وفق المرجع. أبقِ D3-18 requirement invocation NOT_RUN حتى ينفذ فعلياً؛ لا تخلط artifact-level scoped acceptance مع requirement test.

**D3 Scenario Split sub-gate — ليست مرحلة جديدة:**
- خمسة ملفات مشتقة لكل لغة، حسب C030/C050/C070/C085/C100.
- كل جزء يحتفظ بمستويات G000/G030/G050/G070/G100.
- المجموع 10 ملفات مشتقة؛ لا تعدل أو تستبدل الأصليين.
- الملفان الأصليان في Git tree حجمهما 27,722,355 و27,734,273 bytes، أي دون حد 100MB المعتاد للملف الواحد؛ التقسيم للتنظيم وليس ضرورة لتجاوز hard limit.
- لكل مصنف 185 sheet وفق D6؛ افحص كل sheet ولا تفترض وجود 25 sheet فقط.
- اربط sheet names بـscenario_id/manifest/metadata من محتوى المصنف؛ لا تخترع mapping.
- كل ورقة مصدر إما تُخصص لجزء أو تُعلن shared/supporting مع سبب. الأوراق المشتركة المكررة يجب أن تكون canonical-identical.
- manifest لكل لغة: source URL/commit/blob/size/SHA-256، كل sheet names/order، scenario IDs، shared sheets، part paths/sizes/SHA-256، tool/library versions، merge procedure.
- افحص كل جزء مستقلاً، ثم أعد تجميعه تجريبياً في مسار منفصل وقارن canonical sheet hashes وworkbook structure والقيم والأنواع والصيغ والأنماط والروابط.
- لا تدّعِ byte-identical ZIP بعد إعادة الحفظ؛ احتفظ بالأصل byte-exact.
- إذا فشل invariant أو تعذر mapping، أوقف split ولا تمس الأصل.
- لا تدّعِ أن التقسيم يحل Artifact expiry أو يقلل إجمالي bytes بالضرورة.»

## PROMPT D4 — DOCX & Numeric Provenance

«نفذ D4 فقط. تحقق من التقارير العربية والإنجليزية والملخصات ودراسة الجدوى. افتح DOCX الفعلية وافحص OOXML وRTL/LTR والصفحات والجداول والعناوين والروابط والإفصاحات والأرقام والتطابق مع Registry/manifest. نفذ Test 176 وكل اختبارات D4 الإلزامية فعلياً. لا تساوِ 112 explicit Registry IDs مع كل numeric-token lineage. اربط كل رقم بمصدره أو صنفه. لا تدّعِ مراجعة بصرية لكل صفحة إن لم تحدث.»

## PROMPT D5 — Package & Manifest

«نفذ D5 فقط. أعد بناء الحزمة من المخرجات المعتمدة دون تغيير المصادر التاريخية. افحص manifest وSHA256SUMS وكل member path/size/hash وZIP CRC والـduplicates/path traversal. أثبت وجود ومطابقة المخرجات السبعة. افصل tested SHA عن publication-evidence commit. شغل Full 177-unique-test suite إذا كانت إلزامية ومصرحاً بها؛ لا تصف focused tests بأنها 177 tests. تحقق من exact Artifact ID/bytes/digest/expiry بعد النشر. Artifact مؤقت ليس احتفاظاً دائماً.»

## PROMPT D6 — Independent Post-write Audit

«نفذ D6 فقط باستقلال عن Builder. نزّل exact published Artifact ID وافحص كل الأعضاء والبصمات والبيانات والـworkbooks والـDOCX والـRegistry lineage والـmanifest. شغل الاختبارات الإلزامية الفعلية، خصوصاً 176/179/180/181/183؛ وسجل historical invocations 175/182/186 كمنفذة فقط إذا استدعيت فعلاً. لا تساوِ scoped check مع historical test invocation. افحص جميع الـ28 required outputs، وميّز complete outputs عن representative/report-scope. D6 ليس P17/P18 ولا قبولاً نهائياً. لا تبدأ E0 قبل D6 exit gate.»

## PROMPT E0 — Full Gap Inventory

«نفذ E0 فقط بعد D6 exit gate. طابق أبواب المرجع 0–25 وكل clauses والـ28 required outputs والبيانات والاختبارات والمخرجات. أنشئ traceability requirement→source→code→test→output→artifact→SHA/commit→retention. صنف كل بند ورتب gaps حسب أثرها على النتيجة النهائية. لا تكتفِ بالـ15 gap السابقة إذا كشف الفحص الحي المزيد. E0 لا يصلح الفجوات تلقائياً ولا يعلن قبولاً.»

## PROMPT E1 — Conflict & Owner Decisions

«نفذ E1 فقط بعد E0. راجع كل تعارض بين reference/owner decision/code/test/manifest/artifact/report/status. احتفظ بالتاريخ وأضف تصحيحاً Append-only. أنشئ decision register لكل قرار: السبب والخيارات والأثر والهوية/المرجع والتكلفة/المخاطر والصلاحية. لا تعتبر الصمت أو طلب تحديث المكتبة موافقة. لا تعدل المرجع أو business rules أو thresholds أو identities أو artifacts التاريخية. إذا بقي قرار مالك مطلوب، E1 BLOCKED.»

## PROMPT E2 — Accounting Evidence & Replay

«نفذ E2 فقط بعد E1. ابحث عن original identity-matching records للحقول الخمسة والدفاتر اليومية لكل 48K Trial، مع فصل S6 وC100 وStage 12/13. تحقق من producer code path وserialization schema وParquet bytes والـmanifest. لا تستخدم proxy أو inferred value أو zero-fill أو backfill.

افصل بين Original historical evidence وRead-only forensic audit وOld-identity replay reconstruction وNew S6/C100 proposal.

Run 41958935113 نجح كـPASS_SCOPED_REPLAY_RECONSTRUCTION: 20×2,400=48,000 Trial identities و98,323,918 replay daily rows مع تطابق fingerprints والحقول/التواريخ المتداخلة وفحوص balance ضمن replay. لا يحول replay إلى original historical evidence ولا يغلق الحقول الخمسة التاريخية. Production Gate A يبقى NOT_DECLARED.

New S6 candidate source pin 002b74893ca9dfea864e83fecc558f2388748ffe، cohort s6-v23-rebuild-20261105؛ C100 cohort منفصل c100-v23-rebuild-20261105؛ repair anchor a5573eb1891ed2c56b01f6c9b3ccfe9619a08358. الحالة WAIT_FINAL_OWNER_CONFIRMATION. لا Trial أو Golden revalidation أو D0'–D6' لهذه السلالة دون قرار مالك نهائي منفصل.

أخرج E2 gap disposition. إذا بقيت الحقول الخمسة أو all-48K accounting evidence مفقودة، E2 لا تحقق شرط gap-free ولا يجوز E3.»

## PROMPT E3 — Acceptance Tests & Fixtures (LOCKED)

«لا تبدأ E3 إلا إذا أثبت GitHub أن D0–D6 وE0–E2 gap-free وأن Global Preservation Gate PASS ولا يوجد Artifact مطلوب غير محفوظ. اقرأ entry criteria/fixtures/tests من v2.4.0. اربط كل requirement بالاختبار والمدخل والنتيجة والـartifact. نفذ فقط الاختبارات المصرح بها دون تغيير identities أو تشغيل Trials جديدة تلقائياً. أي Test NOT_RUN أو fixture/source mismatch يوقف E3.»

## PROMPT E4 — Financial/Statistical Reconciliation (LOCKED)

«لا تبدأ E4 قبل E3 gap-free closure. أعد تدقيق Gate A/Gate B/stability من بيانات identity-matching كاملة. Gate B السابق N=2400 FAIL_SCOPED (10/10)، Stability NOT_CONVERGED (0/60)، N=4800 NOT_EXECUTED. لا تشغل N=4800 أو Monte Carlo أو Trials جديدة دون قرار مالك صريح يحدد scope/identity/seed/cost/stop conditions. لا تستخدم نتائج سيناريو آخر أو scaling. أي نقص بيانات يبقي E4 BLOCKED.»

## PROMPT E5 — Independent P17 Acceptance (LOCKED)

«لا تبدأ E5 قبل E4 gap-free closure. نفذ مراجعة مستقلة لا تعتمد على Builder evidence وحده. افحص كل مخرج ومتطلب وإفصاح وmanifest/hash/lineage/retention. تحقق من كل الاختبارات والـ28 output cells. لا تعلن P17_FINAL_ACCEPTED إلا بعد جميع المعايير وقرار المالك المطلوب. أي conflict أو missing evidence يمنع القبول.»

## PROMPT E6 — P18 Release Eligibility (LOCKED)

«لا تبدأ E6 قبل E5 gap-free closure. تحقق من أهلية الإصدار والاحتفاظ الدائم وإعادة الإنتاج واتساق source/identity/manifest ووثائق التسليم والمخاطر. جهّز توصية إصدار فقط. لا تنشر Release ولا تعدل main ولا تدمج ولا تعلن P18_RELEASED أو FINAL_ACCEPTED أو CONVERGED دون قرار مالك صريح منفصل. أنشئ handoff نهائياً يثبت ما نجح وما بقي.»

---

# 6. Global Preservation Gate قبل E3

شروط PASS:
- فحص كل Artifact ID مباشرة من Actions API.
- تنزيل كل Artifact مطلوب exact ID.
- حساب SHA-256 من ZIP bytes ومطابقتها مع GitHub digest.
- فحص ZIP integrity وmember hashes وsource identity.
- نسختان مستقلتان durable، مع إعادة قراءة وحساب بصمة كل نسخة.
- retention manifest يربط كل Artifact بالـRun/Job/tested SHA/expiry والمواقع والبصمات.
- توثيق نسخة الهاتف بعد تأكيد المالك، دون ادعاء وصول مباشر للهاتف.
- لا Artifact غير محفوظ أو مهدد بالانتهاء.
- restore test ناجح.

الحالة عند إعداد REV4: BLOCKED / PERMANENT_RETENTION_NOT_COMPLETE. كل الـ29 Artifacts كانت unexpired في فحص 2026-11-05، لكن لا يوجد archive دائم مثبت، ولا تأكيد نسخة هاتف، والروابط السابقة مؤقتة. 23 Artifact أكبر من 100 MiB، بإجمالي 4.865 GiB. لذلك E3 مقفل.

---

# 7. D3 Scenario Split Matrix

| Part | السيناريوهات |
|---|---|
| C030 | C030_G000, C030_G030, C030_G050, C030_G070, C030_G100 |
| C050 | C050_G000, C050_G030, C050_G050, C050_G070, C050_G100 |
| C070 | C070_G000, C070_G030, C070_G050, C070_G070, C070_G100 |
| C085 | C085_G000, C085_G030, C085_G050, C085_G070, C085_G100 |
| C100 | C100_G000, C100_G030, C100_G050, C100_G070, C100_G100 |

الناتج 5 ملفات EN + 5 ملفات AR. لا تفقد أياً من 25 scenario cells. لا تبدأ قبل قراءة بايتات المصنفين فعلياً والتحقق من الـ185 sheet لكل مصنف وربط sheet names بالـscenario IDs. أي sheet غير مصنف يوقف التقسيم.

---

# 8. نموذج تقرير نهاية كل مرحلة

يجب أن يحتوي:
1. Stage + disposition + gap-free أم scoped.
2. branch HEAD/main HEAD/compare.
3. requirement matrix: requirement/source/evidence URL/SHA-256/blob SHA-1/size/commit/test/status.
4. defects/root causes/repair commits.
5. Actions run/job/tested SHA/conclusion.
6. Artifact IDs/digests/sizes/expiry/retention state.
7. Raw readback/exact final HEAD.
8. ما أصلح وما بقي وما يحتاج قرار مالك.
9. READY_FOR_NEXT_STAGE أو BLOCKED. لا تستخدم READY مع فجوة إلزامية.
10. اسم المرحلة التالية فقط إذا اجتازت البوابة.

---

# 9. قاعدة المالك — اسم المرحلة فقط

يمكن للمالك إرسال D0 أو D1 أو D2 أو D3 أو D4 أو D5 أو D6 أو E0 أو E1 أو E2 أو E3 أو E4 أو E5 أو E6 فقط. على الوكيل استعادة GitHub الحي وجلب كل الملفات بنفسه، وتنفيذ كل ما تسمح به الصلاحيات، وعدم طلب إعادة رفع الملفات الموجودة، وعدم الانتقال تلقائياً. عند قرار مالك محمي أو نقص غير قابل للاسترداد أو صلاحية/أداة غير متاحة أو Workflow طويل يستوجب التوقف، يطلب قراراً واحداً محدداً أو يعلن BLOCKED. إذا أرسل المالك E3 وبقي أي شرط سابق BLOCKED، لا ينفذ E3.

---

# 10. سجل REV4

REV4 تعيد ترتيب البرومبتات وتضيف عقد صفر فجوات، تعريف الإغلاق الكامل، Global Preservation Gate، D3 Scenario Split sub-gate، وضوابط E3–E6. لا تغير قواعد الأعمال أو المرجع أو الهوية أو thresholds، ولا تعلن أي مرحلة gap-free لمجرد وجود PASS_SCOPED تاريخي.

تم إعداد REV4 على HEAD 522fc266436893add3dc4d447afdbc8f999ffda4 وmain 01a6f79eedc522bb734ed9c5ea31beee581f2468. هذا لا يغني عن post-commit Raw readback وexact-head validation.

## أرشيف النسخ السابقة

النص الكامل لـREV3 محفوظ أدناه كما كان قبل REV4، بما فيه REV2 والبرومبتات السابقة. يحتفظ به للتاريخ فقط؛ عند التعارض تسود أقسام REV4 أعلاه.

---

# أرشيف REV3 الكامل — للاحتفاظ التاريخي فقط

# مكتبة البرومبتات التشغيلية — Motorcycle Simulation
## REV3 — التحديث الشامل الحي | 2026-11-05 | GitHub-First

**الحالة:** النسخة التشغيلية الحالية. تحل هذه النسخة محل REV2 في الاستخدام من تاريخ نشرها.  
**المستودع:** `yasmin977209-ux/motorcycle-simulation`  
**فرع العمل:** `tmp/d1-rebuild-20261101`  
**مرجع الاستمرارية عند إعداد REV3:** branch HEAD `413d1322c046299ea7c3557583d8d25cf37192fb`؛ main HEAD `01a6f79eedc522bb734ed9c5ea31beee581f2468`.  
**القرار الحاكم:** `D-2026-10-30-REFERENCE-V2.4.0` — `APPROVED_BY_OWNER`.

> هذه المكتبة دليل تشغيل وتنظيم فقط. لا تنشئ قاعدة أعمال ولا تمنح صلاحية غير موجودة. ترتيب السلطة: قرارات المالك الصريحة وحدودها، ثم المرجع الحاكم v2.4.0 وفق قرار الاعتماد، ثم أدلة GitHub الحية، ثم هذه المكتبة، ثم السجلات التاريخية والذاكرة. عند التعارض تحفظ الأدلة القديمة ويضاف تصحيح Append-only؛ لا يُمحى التاريخ.

## 0. سجل الإصدار والحالة الحية — REV3

### 0.1 نقطة GitHub الحية التي بُني عليها هذا التحديث

تم استخراج المراجع مباشرة من GitHub API في جلسة 2026-11-05:

| العنصر | القيمة |
|---|---|
| Repository | `yasmin977209-ux/motorcycle-simulation` |
| Active branch | `tmp/d1-rebuild-20261101` |
| Branch HEAD قبل تحديث REV3 | `413d1322c046299ea7c3557583d8d25cf37192fb` |
| main HEAD | `01a6f79eedc522bb734ed9c5ea31beee581f2468` |
| Compare | `diverged`; branch ahead 954 / behind 2 |
| Merge base | `c6e54349a5e94f65d5aa9f83141f225d777bb474` |
| Open PRs from active branch | 0 |
| Open PRs repository-wide | 16، على فروع أخرى |
| Published Releases | 0 |

هذه لقطة قبل Commit REV3، وليست قيمة HEAD بعد النشر. بعد إنشاء هذا الملف يجب قراءة Commit النهائي والفرع وActions مجدداً، وتسجيل النتيجة في ملحق تحقق REV3.

### 0.2 الحالة المرحلية الحالية التي تحكم الاستئناف

| المرحلة | الحالة الحالية | الحد الذي لا يجوز تجاوزه |
|---|---|---|
| D0 | `PASS_SCOPED_WITH_LIMITATIONS` | لا يثبت Parquet schema/row counts أو الدفاتر التاريخية الكاملة والحقول الخمسة |
| D1 | `PASS_SCOPED_WITH_LIMITATIONS` | 105 normalized manifest statuses تبقى `NOT_VERIFIED` عند غياب expected byte sizes مستقلة |
| D2 | `PASS_SCOPED_WITH_LIMITATIONS` | Registry نطاقي ولا يثبت 48K detailed ledgers |
| D3 | `PASS_SCOPED_WITH_LIMITATIONS` | `D3-18=NOT_RUN` في خريطة المتطلبات؛ لا ترفع هذا الاختبار |
| D4 | `PASS_SCOPED_WITH_LIMITATIONS` | Test 176 وfull numeric-token-to-Registry lineage غير مثبتين |
| D5 | `PASS_SCOPED_WITH_LIMITATIONS` | full 177-test suite `NOT_RUN` |
| D6 | `PASS_SCOPED_WITH_LIMITATIONS` | الاختبارات التاريخية 176/179/180/181/183 وinvocations 175/182/186 ليست مثبتة كتشغيلات فعلية |
| E0 | `PASS_SCOPED` | جرد فجوات فقط؛ ليس إغلاقاً للفجوات |
| E1 | `PASS_SCOPED` | تسوية وثائقية/حوكمية؛ لا تمنح قرارات المالك المعلقة |
| E2 | `PASS_SCOPED` | التدقيق التاريخي وإعادة بناء الهوية القديمة فقط؛ السلالة الجديدة S6/C100 ليست منفذة |
| E3–E6 | `NOT_STARTED` | لا تبدأ Acceptance Execution أو مرحلة لاحقة قبل بواباتها وقرارات المالك |

التصنيف العام: `T2_INTERIM / NOT_FINAL_BLOCKED`.  
`FINAL_ACCEPTED`, `P17_FINAL_ACCEPTED`, `P18_RELEASED`, `CONVERGED`: جميعها `NOT_DECLARED`.

**Exact-head Actions على branch HEAD السابق REV3 `413d1322c046299ea7c3557583d8d25cf37192fb`:**
- D1–D2 Run [42059899115](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42059899115): `SUCCESS`; Job 127358322171.
- D3 Run [42059899239](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42059899239): `SUCCESS`; Job 127358325043.
- D0–D4 Run [42059899061](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42059899061): `SUCCESS`; Job 127361530536.
- كل Run أعلاه اختبر SHA `413d1322c046299ea7c3557583d8d25cf37192fb` بالضبط. لا تنسب نجاحها إلى Commit REV3 أو أي HEAD لاحق قبل إعادة التحقق.

### 0.3 تصحيح D3 artifact lineage

التصحيح الحي من Actions Artifacts API:
- Artifact `13288779998` مصدره Run `41754147172`، والـsource tested SHA هو `3325fd961005c2c47de071d25904a748af7a21a6`.
- الحجم `535,567,142` bytes؛ GitHub metadata digest `sha256:e49b206d8d80034b1dc0cb284bfee76d81f9e9759e2459b1608fad2f5c933ffe`؛ expiry `2026-12-04T02:07:02Z`.
- Run `41914970361` هو Acceptance Run منفصل، وليس Source Run الذي أنشأ Artifact.
- إذا اختلف سجل إغلاق قديم عن هذا التصحيح، احتفظ بالنص التاريخي وأشر إلى هذا التصحيح بوصفه المرجع الأحدث للـlineage. لا تغيّر Artifact أو manifest تاريخياً.

### 0.4 نتائج وبوابات ثابتة

- Financial Gate A: `PASS_SCOPED` فقط.
- Production Gate A: `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`.
- Gate B: النتيجة التشغيلية المبلغ عنها عند N=2400 هي `FAIL_SCOPED (10/10)`؛ والتصنيف الإجمالي يبقى `CONFLICTED` حتى تتم تسوية هوية SOURCE_SHA/cohort/seed/scenario/N/checkpoint/Run/Job/tested SHA/Artifact.
- Stability: `NOT_CONVERGED (0/60)`.
- N=4800: `NOT_EXECUTED`.
- Full Logging: 105 representative keys فقط؛ لا يثبت logging لجميع 48,000 Trial.
- C100 Golden revalidation على السلالة الجديدة: `NOT_RUN`.
- `Potential_Coverage_Cells=604` حساب محتمل فقط؛ `Required_Output_Coverage_Cells=PENDING_MATRIX_VALIDATION`.
- لا تخلط 125 role assignments مع 105 unique keys.

الحقول المحاسبية الخمسة التالية `MISSING_EVIDENCE)، ولا يجوز تخمينها أو تصفيرها أو استنتاجها:
`Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Total_Assets`.

### 0.5 E2 — فصل الهويات والقرار المنفذ

**Old-identity replay reconstruction:**
- Owner approved Option A بتاريخ 2026-11-05، ضمن الحدود المحددة في `docs/post_d/E2_OWNER_DECISION_APPROVED_A_2026-11-05.md`.
- Run `41958935113`: `SUCCESS`; 20 scenario jobs + aggregate.
- 20 × 2,400 = 48,000 Trial identities؛ 98,323,918 daily rows.
- التصنيف `PASS_SCOPED_REPLAY_RECONSTRUCTION` وليس original historical evidence ولا final acceptance.
- Execution commit `a23ba71f48487f3ebead99bc30039b14ef9b7609`; old `SOURCE_SHA=da1a9ea9b5cd789c944de3f07b08395bb67c49e7`; old cohort `s6-v23-da1a9ea9`; `MASTER_SEED=20270101`.
- الحقول الخمسة المفقودة من التاريخ الأصلي لا تصبح مثبتة بأثر رجعي؛ Production Gate A يظل `NOT_DECLARED`.

**New S6 + C100 lineage:**
- S6 candidate source pin `002b74893ca9dfea864e83fecc558f2388748ffe`.
- repair reference `a5573eb1891ed2c56b01f6c9b3ccfe9619a08358`.
- S6 cohort candidate `s6-v23-rebuild-20261105`.
- C100 cohort candidate منفصل `c100-v23-rebuild-20261105`.
- الحالة `WAIT_FINAL_OWNER_CONFIRMATION`; لا Trial أو Golden revalidation أو D0'–D6' قبل التأكيد النهائي المحدد. موافقة Option A كانت لإعادة بناء الهوية القديمة فقط، وليست إذناً بهذه السلالة الجديدة.
- لا تستنتج C100_SOURCE_SHA من S6_SOURCE_SHA.

### 0.6 Artifacts والاحتفاظ — إعادة تحقق 2026-11-05

أعيد طلب Metadata لجميع Artifacts الـ29 في الجرد من Actions API، عبر Runs المصدر ذات الصلة. كلها كانت `expired=false` وقت إعادة التحقق. ملف الجرد:
`docs/stage_d/D0_D6_E0_E2_RETENTION_INVENTORY_2026-11-05.json`
لكن `review_head` داخله أقدم من HEAD الحالي؛ استخدمه كفهرس تاريخي، واعتمد نتائج Actions API الأحدث للـmetadata.

أهم المواعيد:
| Artifact | ID | الحجم bytes | Expiry UTC |
|---|---:|---:|---|
| D0 S6 aggregate | 12852969854 | 9,357,996 | 2026-11-27 21:46:36 |
| D1 Full Logging (105 keys) | 12998778418 | 310,827,203 | 2027-01-28 17:25:30 |
| C100 reuse | 12630457193 | 361,733 | 2027-01-24 03:18:29 |
| D3 workbook package | 13288779998 | 535,567,142 | 2026-12-04 02:07:02 |
| D0-D4 evidence | 13373853115 | 5,706 | 2026-12-04 23:54:10 |
| D0-D4 evidence | 13382253631 | 5,698 | 2026-12-05 02:21:52 |
| D5 package | 13369179742 | 519,116,689 | 2026-12-04 22:49:30 |
| D6 audit | 13371094066 | 6,635 | 2026-12-04 23:14:36 |
| E2 replay | 20 scenario Artifacts + aggregate | sizes/digests in inventory | 2027-02-03 03:01:28 |

- مجموعها 29 Artifact: 8 من D0/D1/D2/D3/D0-D4/D5/D6 و21 من E2 (20 scenario + aggregate).
- Git history يحفظ النصوص والمصادر، ولا يحفظ Actions binary Artifacts بعد انتهاء صلاحيتها.
- لا يوجد external permanent archive مثبت حتى هذا التحقق. Box غير متصل؛ GitHub Release غير منشور ويتطلب قرار مالك منفصل.
- تم إنشاء تنزيلات مؤقتة لستة Artifacts: `12852969854`, `13288779998`, `13369179742`, `13371094066`, `13382253631`, `13373853115`. الروابط الموقعة مؤقتة، ولا تعتبر أرشيفاً دائماً. لا تدّعِ أن ZIP bytes الستة أعيد حساب SHA-256 لها؛ metadata digest من GitHub هو المسجل. E2 aggregate bytes كان له تحقق منفصل كما في سجل E2.
- المطلوب من المالك: حفظ الملفات التي تم تنزيلها على الهاتف/وسيط مستقل. لا تفترض أن الحفظ على الهاتف تم دون تأكيد.

### 0.7 ملفا Excel الكاملان — تحقق وجود وحجم فقط

Git tree على HEAD السابق REV3 أظهر:
- `deliverables/Full_Results_EN.xlsx`: 27,722,355 bytes؛ blob SHA-1 `a01c1f4061da731de24fcc8d061113bb195e65b1`.
- `deliverables/النتائج_الكاملة_AR.xlsx`: 27,734,273 bytes؛ blob SHA-1 `056b7f482bbb84583526f093ae886e13b8c01356`.

هذه بيانات Git tree وليست فحصاً لبايتات المصنفين أو SHA-256 مستقلة. الملفان أقل من حد GitHub المعتاد 100MB للملف الواحد؛ لذلك لا تكتب أن التقسيم مطلوب لتجاوز hard file-size limit. Artifacts D3/D5 أكبر من 500MB وهي مسألة retention/package منفصلة.

### 0.8 مسار الاحتفاظ والتغليف — عمل موازٍ وليس مرحلة جديدة

يضاف مسار عمل مستقل باسم **Retention & Scenario Packaging Workstream**. هذا ليس مرحلة D أو E، ولا يغيّر التسلسل أو البوابات أو أسماء المراحل. غرضه:
1. حفظ Artifacts المؤقتة قبل expiry.
2. إنشاء نسخ دائمة في وجهة تخزين يحددها المالك/تكون متاحة ومصرحاً بها.
3. إعداد أجزاء Excel مشتقة بحسب سيناريوهات C، مع الاحتفاظ بالمصدرين الأصليين كما هما.
4. إنشاء manifests وفحوص إعادة التجميع والتكافؤ.
5. توثيق نسخة الهاتف والنسخة الاحتياطية وبصماتها بعد التحقق.

**خطة التقسيم المقترحة للملفين الكاملين: خمسة أجزاء لكل لغة (عشرة ملفات):**
- Part C030: `C030_G000`, `C030_G030`, `C030_G050`, `C030_G070`, `C030_G100`.
- Part C050: `C050_G000`, `C050_G030`, `C050_G050`, `C050_G070`, `C050_G100`.
- Part C070: `C070_G000`, `C070_G030`, `C070_G050`, `C070_G070`, `C070_G100`.
- Part C085: `C085_G000`, `C085_G030`, `C085_G050`, `C085_G070`, `C085_G100`.
- Part C100: `C100_G000`, `C100_G030`, `C100_G050`, `C100_G070`, `C100_G100`.

يجب أولاً مطابقة هذه المصفوفة مع السيناريوهات الفعلية وأسماء أوراق المصنفين والـmanifest؛ إذا لم تطابق البيانات الفعلية، توقف وسجل التعارض ولا تخترع sheet mapping.

**قواعد التقسيم:**
- لا تعدل أو تستبدل أو تحذف الملفين الأصليين. الأجزاء مشتقات جديدة واضحة الهوية.
- كل جزء يحتوي جميع أوراق السيناريوهات الخمسة الخاصة بقيمة C المحددة، مع أوراق التعريف/الملخص/المشتركة اللازمة لفهم الجزء. إذا تكررت أوراق مشتركة في الأجزاء الخمسة، يجب أن تكون متطابقة canonical-content؛ وعند إعادة التجميع تزال النسخ المكررة فقط بعد إثبات التطابق.
- لا تفترض عدد أوراق لكل سيناريو؛ استخرج mapping من المصنف الحقيقي وسجل sheet names لكل جزء.
- أنشئ manifest مستقل لكل لغة يثبت source path, source commit, source blob SHA-1, source byte size, source SHA-256 المحسوبة من bytes, scenario IDs, sheet mapping/order, shared sheets, part paths, part sizes, part SHA-256, tool/library versions, and merge procedure.
- افحص فتح كل ملف، سلامة الأوراق والبيانات والأنواع والقيم المالية والتنسيقات والعناوين وhidden states وmerged cells وnamed ranges والروابط والـprint settings بقدر ما يحتويه المصدر.
- اختبر التغطية: كل سيناريو مطلوب يظهر مرة واحدة بالضبط في المجموعة الخاصة به؛ لا سيناريو مفقود أو مكرر؛ كل ورقة مصدر إما assigned أو declared shared/omitted with reason.
- إعادة التجميع لملفات XLSX تكون **semantic/content equivalence** عبر canonical sheet hashes وworkbook structure، وليس ادعاء byte-identical ZIP بعد إعادة الحفظ؛ يحتفظ بالملف الأصلي كمرجع byte-exact. إذا كان byte-identical مطلوباً، لا تدّعِ تحقيقه عبر openpyxl إعادة كتابة workbook.
- لا تنشر مشتقات على أنها بديل للمصدر الأصلي أو Artifact تاريخي.
- التقسيم لا يقلل مجموع البايتات بالضرورة ولا يحل انتهاء صلاحية Actions Artifacts. لا تنفذ retention deletion أو تغيير manifest تاريخي.

**شرط البدء:** مسموح إعداد وثائق وخطة وقراءة metadata. لا تبدأ معالجة أو إعادة كتابة الملفات الثنائية قبل تحديد مصدر البايتات، exact source identity، mapping الفعلي، والتحقق من عدم المساس بالمصدر التاريخي. أي تغيير في artifact/manifest تاريخي أو release/وجهة تخزين تتطلب موافقة مالك حيث تنص السياسة.

### 0.9 ترتيب العمل والأولوية بعد REV3

1. حفظ/تنزيل Artifacts الحرجة ذات أقرب expiry، مع تسجيل metadata وروابطها. لا تنتظر E3 كي تحفظها.
2. التأكد من أن المالك حفظ النسخ على الهاتف/وسيط مستقل؛ لا تدّعِ ذلك نيابة عنه.
3. تجهيز permanent archive destination دون نشر Release أو استخدام خدمة غير متصلة/غير مصرح بها.
4. إكمال reconciliation للفجوات والقرارات والهوية ضمن E3 readiness دون تشغيل اختبارات قبول محظورة.
5. لا تبدأ E3 Acceptance Execution قبل إثبات جميع entry criteria وقرار المالك المطلوب.
6. بعد E3، تابع E4 ثم E5 ثم E6 فقط بالترتيب وبعد كل بوابة.
7. لا تعلن Final/P17/P18/Converged بمجرد D6 أو نجاح Workflow.

### 0.10 صلاحيات وحدود غير قابلة للتأويل

**مسموح:** قراءة GitHub، تحديث وثائق المكتبة والاستمرارية على فرع العمل، إصلاح عيوب تقنية موثقة ضمن النطاق، commits، اختبارات/Actions المصرح بها، إنشاء Draft PR بعد البوابة.

**قرار مالك منفصل مطلوب:** تغيير المرجع أو business rules أو thresholds أو inference؛ تغيير SOURCE_SHA/cohort_id/MASTER_SEED/Trial identity؛ Trials/Simulation/Monte Carlo/Golden revalidation/N expansion/N=4800 خارج قرار Option A المحدد؛ backfill أو تخمين/zero-fill للحقول المحاسبية؛ تعديل/حذف Artifact أو manifest تاريخي؛ تعديل main أو merge أو force-push أو حذف history؛ نشر Release؛ إعلان FINAL_ACCEPTED/P17_FINAL_ACCEPTED/P18_RELEASED/CONVERGED.

موافقة Option A لإعادة بناء S6 القديمة لا تمتد إلى سلالة S6/C100 الجديدة ولا إلى E3 أو N expansion.

---

# القسم السادس — إضافات REV3 للبرومبتات التشغيلية

## REV3-01 — استعادة الحالة الحية

في أول رسالة من كل جلسة:
1. اقرأ branch ref وmain ref من GitHub API مباشرة، وسجل SHA لكل منهما.
2. قارن الفرع بـmain وسجل ahead/behind/merge-base.
3. اقرأ REV3 أولاً، ثم أحدث continuity/status/handoff، ثم E2 continuity وREV3 plan والقرارات ذات الصلة.
4. اقرأ المرجع v2.4.0 وقرار D-2026-10-30-REFERENCE-V2.4.0. لا تعتبر الرأس الداخلي PROPOSED في المرجع متغلباً على قرار APPROVED_BY_OWNER؛ سجّل التعارض ولا تعدل المرجع.
5. افحص Actions runs/jobs/artifacts وPRs المرتبطة بفرع العمل وReleases.
6. أعد التحقق من كل artifact expiry metadata. لا تستخدم inventory قديم بوصفه current.
7. ميّز في التقرير بين: VERIFIED_LIVE, VERIFIED_LOCAL, REPORTED_ONLY, MISSING_EVIDENCE, CONFLICTED, NOT_RUN, BLOCKED, PASS_SCOPED.
8. لا تبدأ التنفيذ في تقرير الاستعادة؛ حدّد خطوة واحدة مسموح بها.

## REV3-02 — الاحتفاظ الدائم بالأدلة

- اقرأ inventory JSON وسجلات التصحيح، ثم أعد فحص كل Artifact ID من Actions API.
- رتب حسب أقرب expiry، مع إعطاء أولوية للـD0 aggregate ثم D3/D5/D6 وD0-D4 evidence، ثم D1/C100، ثم E2 replay artifacts.
- نزّل artifact من ID الصحيح لا من اسم مشابه. سجل run ID وtested SHA وartifact ID/name/size/digest/expiry.
- لا تعتبر signed URL المؤقتة أرشيفاً دائماً.
- بعد التنزيل، احسب SHA-256 للـZIP bytes محلياً وقارنها مع GitHub digest. افحص ZIP CRC/path traversal/duplicate names وmanifest/content identities عند السماح.
- احتفظ بنسخة untouched، ونسخة ثانية في وسيط مستقل. لا تفك الضغط فوق النسخة الأصلية.
- لا ترفع Artifacts الثنائية الضخمة إلى Git history لمجرد الاحتفاظ؛ اختر storage destination مصرحاً به وسجل الوصول والبصمات.
- GitHub Release يحتاج قرار مالك منفصل؛ لا تنشره تلقائياً.
- إذا كانت خدمة أرشفة غير متصلة، لا تدّعِ وجودها ولا تطلب من المستخدم إعادة رفع ملفات موجودة في GitHub.

## REV3-03 — تقسيم ملفات Excel حسب C

المدخلات المستهدفة:
- `deliverables/Full_Results_EN.xlsx`
- `deliverables/النتائج_الكاملة_AR.xlsx`

المطلوب عشرة مشتقات: خمسة لكل لغة، حسب C030/C050/C070/C085/C100، مع جميع مستويات G الخمسة في كل ملف. اقرأ bytes المصدر الفعلية وحقق SHA-256 قبل البناء. تحقق من scenario/sheet mapping من المصنف نفسه، ولا تعتمد على أسماء السيناريوهات المتوقعة وحدها.

نفّذ partition على نسخة عمل فقط. لا تعدل المصدر. أنشئ manifest لكل لغة وmapping شامل لكل sheet. افحص كل جزء بصورة مستقلة، ثم merge تجريبي في مسار منفصل، وقارن canonical sheet hashes وworkbook-level invariants. لا تقبل إعادة التجميع إذا فقدت أوراقاً أو تغيرت قيم مالية أو ظهرت formulas/errors غير موجودة بالمصدر. احتفظ بالملف الأصلي byte-exact.

## REV3-04 — بوابة الجاهزية قبل E3

قبل أي E3 Acceptance Execution:
1. أثبت إغلاق D0–D6 ضمن القيود، لا بمجرد أسماء status.
2. أثبت E0/E1/E2 scoped closure مع إبقاء الفجوات.
3. سوِّ Gate B identities/checkpoints/runs/artifacts، ولا ترفع النتيجة.
4. حدد أثر الحقول المحاسبية الخمسة المفقودة على Production Gate A.
5. حدد حالة 105 manifest statuses وFull Logging.
6. أثبت C100 Golden contract والسلالة التي ستستخدمها؛ لا تخلط القديمة بالجديدة.
7. افصل E3 Readiness عن E3 Acceptance Execution.
8. اجمع قرارات المالك المطلوبة في قائمة محددة. لا تعتبر الصمت أو طلب التحديث موافقة.
9. إذا بقي أي entry criterion BLOCKED أو CONFLICTED، عالج ذلك المانع فقط.

## REV3-05 — إغلاق الجلسة

في نهاية أي جلسة تنفيذية:
1. حدّث REV3 أو أضف تصحيحاً append-only عند الحاجة.
2. حدّث `docs/PROJECT_CONTINUITY.md` وSession Status وContinuity Handoff وE2 Continuity عند تأثرها.
3. سجل commit parent وcommit الناتج والـbranch HEAD وmain HEAD.
4. اقرأ كل ملف من GitHub Raw بعد commit، واحسب SHA-256 من bytes، وسجل Git blob SHA-1 والحجم والروابط.
5. افحص Actions على exact final HEAD. لا تنسب نجاح run سابق إلى HEAD جديد.
6. عند Workflow طويل (10 دقائق أو أكثر)، اذكر Run ID وCommit SHA ثم توقف ولا تنتظر اكتماله.
7. لا تكتب PASS أو VERIFIED_LIVE دون ثلاثية الإثبات.
8. إذا تعذرت الكتابة أو remote readback أو hashing، صرّح بذلك صراحةً وقدّم handoff.

---

# القسم السابع — القواعد الذهبية المحدثة REV3

1. GitHub الحي هو مصدر الحالة التشغيلية.
2. استخرج HEAD الفرع وmain في كل جلسة.
3. REV3 هي المكتبة التشغيلية الحالية؛ REV2 والنسخة 2026-11-01 تاريخيتان.
4. قرار المالك APPROVED_BY_OWNER يحكم اعتماد v2.4.0 رغم header conflict داخل الملف.
5. لا تخلط governing reference v2.4.0 مع historical execution reference v2.3.
6. لا تخلط S6 وC100 وStage 12/13.
7. D0–D6 وE0–E2 هي scoped statuses وليست final acceptance.
8. E3–E6 NOT_STARTED حتى إثبات الانتقال.
9. D3 Artifact 13288779998 مصدره Run 41754147172؛ Run 41914970361 Acceptance منفصل.
10. Old replay 41958935113 ليس تنفيذ السلالة الجديدة.
11. لا ترقِّ Gate A أو Gate B أو Stability أو N=4800 بلا دليل وقرار.
12. لا تخمن الحقول الخمسة ولا تصفرها.
13. 105 keys لا تعني 48K full logging.
14. 604 Potential_Coverage_Cells لا تعني Required_Output_Coverage_Cells.
15. 29 Artifacts مؤقتة؛ metadata expiry يجب إعادة التحقق منها.
16. لا تدّعِ حفظ الهاتف أو archive أو Release دون تحقق.
17. ملفا Excel 27.7MB لكل منهما؛ هما دون حد 100MB المعتاد، والتقسيم للتنظيم لا لمعالجة hard limit.
18. تقسيم C يجب أن يغطي جميع G levels الخمسة لكل قيمة C، بعد التحقق من workbook mapping.
19. لا تعدل المصادر الأصلية عند التقسيم؛ مشتقات جديدة فقط.
20. XLSX semantic equivalence ليست byte-identical ZIP؛ احتفظ بالأصل.
21. لا تغيّر main ولا تدمج ولا force-push.
22. لا Trial/Simulation/Monte Carlo/N expansion دون قرار مالك مستقل.
23. لا historical artifact/manifest modification أو Release دون قرار مالك.
24. لا تنتقل بين المراحل دون gate.
25. Append-only لكل تصحيح وتحديث.
26. لا ادعاء بلا دليل، ولا انتقال بلا بوابة، ولا تغيير بلا صلاحية.

---

## سجل إصدار REV3

- REV3 مبني على قراءة REV2 الحية من فرع العمل، مع حفظ نص REV2 كما هو بعد هذا الملحق.
- سبب التحديث: تغير حالة المشروع بعد D3/D4/D5/D6 وE0/E1/E2، ونجاح exact-head D0-D4 على HEAD 413d132، وتصحيح D3 artifact lineage، واكتمال E2 old-identity replay، وتحديث retention inventory، وإضافة خطة تقسيم Excel بحسب C.
- لا يعد هذا التحديث إغلاقاً لأي فجوة علمية أو محاسبية، ولا يعلن قبولاً نهائياً.
- يجب بعد نشر REV3 تسجيل Raw SHA-256 وGit blob SHA-1 والحجم وcontaining commit في سجل تحقق منفصل.
- جميع لقطات REV2 السابقة تبقى محفوظة تاريخياً ولا تُحذف.

---

# محتوى REV2 المحفوظ كما كان

النص التالي هو محتوى REV2 الأصلي للاحتفاظ ببرومبتات D0–D6 وE0–E6 وقواعد المشروع التفصيلية. أي حالة أو توجيه استئناف قديم يتعارض مع أقسام REV3 أعلاه أو ملحق REV3 في نهاية الملف يعتبر تاريخياً وم superseded.

---

# مكتبة البرومبتات التشغيلية — Motorcycle Simulation
## الإصدار المنقح الشامل REV2 | GitHub-First | 2026-11-01

**الحالة:** إصدار تشغيلي منقح يحل محل الإرشادات المتعارضة في الإصدار السابق، مع الاحتفاظ بالإصدار السابق كسجل تاريخي.  
**المستودع:** `yasmin977209-ux/motorcycle-simulation`  
**فرع العمل:** `tmp/d1-rebuild-20261101`  
**المرجع الحاكم:** v2.4.0 — `APPROVED_BY_OWNER` وفق القرار `D-2026-10-30-REFERENCE-V2.4.0`.

> هذه المكتبة تنظّم الاستعادة والتدقيق والتنفيذ. لا تنشئ قواعد أعمال، ولا تغير المرجع أو قرارات المالك، ولا تمنح صلاحيات غير ممنوحة. عند التعارض تكون الأولوية لقرار المالك النافذ، ثم المرجع الحاكم v2.4.0، ثم الأدلة الحية على GitHub، ثم هذه المكتبة، ثم السجلات التاريخية والذاكرة.

---

# 0. سجل الإصدار والحالة الحية

## 0.1 بيانات نقطة الاستمرارية التي تحققت عند إعداد REV2

تمت قراءة فرع العمل و`main` وملفات الحالة ذات الصلة مباشرة من GitHub في 2026-11-01.

| البند | القيمة |
|---|---|
| Repository | `yasmin977209-ux/motorcycle-simulation` |
| Active branch | `tmp/d1-rebuild-20261101` |
| Exact branch HEAD عند إعداد REV2 | `813b5df84d3acd7438ca08978d9735231de0c8bb` |
| Exact main HEAD | `c6e54349a5e94f65d5aa9f83141f225d777bb474` |
| D0 | `PASS_SCOPED_WITH_LIMITATIONS` |
| D1 | `PASS_SCOPED_WITH_LIMITATIONS` |
| D2 | `PASS_SCOPED_WITH_LIMITATIONS` |
| D3 | `BLOCKED / BLOCKED_MISSING_EVIDENCE` |
| D4–D6 | `NOT_STARTED` |
| E0–E6 | `NOT_STARTED`؛ لا أهلية للبدء قبل إغلاق D6 |
| آخر سجل تدقيق D3 | `docs/stage_d/D3_LIVE_REVIEW_AUDIT_2026-11-01.md` |
| main | للقراءة والمقارنة فقط؛ لم يتغير |

هذه لقطة مرجعية وليست بديلاً عن إعادة التحقق. في كل جلسة جديدة استخرج HEAD جديداً للفرع و`main` من GitHub API. لا تفترض أن هذه القيم ما زالت حالية.

## 0.2 الحالة المرحلية المعتمدة للاستئناف

- D0 وD1 مغلقتان ضمن نطاقهما وبقيودهما؛ لا تعِد تنفيذهما لمجرد بدء محادثة جديدة.
- D2 مغلقة بحالة `PASS_SCOPED_WITH_LIMITATIONS`. إثباتها الحي وسجلها هما المرجع، وليس النص القديم الذي يقول `NOT_STARTED`.
- D3 ليست مغلقة. توجد محاولات بناء فاشلة وعيب مصدر معروف ونواقص بيانات ومخرجات غير منشورة. D3 هي المرحلة الحالية المحجوبة.
- D4 وD5 وD6 لم تبدأ، ولا يجوز تجاوز D3.
- لا تبدأ إصلاح D3 أو إعادة تشغيلها إلا بعد أمر استمرار صريح من المالك. عند صدور الأمر، عالج المانع المحدد فقط.
- لا تبدأ E0 قبل إغلاق D6. ولا يعني إغلاق D6 قبول P17 أو إصدار P18.

## 0.3 سجل D3 الحي الذي يجب أن يحكم على المعلومات الأقدم

المراجعة الحية المسجلة في:
`docs/stage_d/D3_LIVE_REVIEW_AUDIT_2026-11-01.md`

حالة D3:
`BLOCKED / BLOCKED_MISSING_EVIDENCE`

محاولات Actions المسجلة:

| Run ID | Tested SHA | النتيجة الموثقة |
|---|---|---|
| `41340409949` | `1675cd3752ee26f96600bdb6b5c6fe45fb2bc15c` | 4 passed / 1 failed؛ parser للثوابت |
| `41340511093` | `bc8be1d5bdcd6977ed02b6522d1613fa05cb112c` | 5 اختبارات ناجحة؛ تدقيق المصنف أوقف البناء عند `FORMULA_OR_ERROR_CELLS_FOUND` |
| `41341008368` | `454b30b7cbd29839ba53b0e16da41d19baf5c161` | 5 passed / 1 failed؛ `NameError: rosafe_append` |

العيب الأخير المسجل: الدالة `constants_from_reference()` تستدعي `rosafe_append(ws, ...)` غير المعرفة بدلاً من إضافة الصف إلى قائمة `rows`. كما أن تدقيق الصيغ/الأخطاء السابق لم يفصل عدد خلايا الصيغ عن عدد خلايا أخطاء Excel؛ لذلك لا يجوز استنتاج أي منهما منفرداً من ذلك السجل.

لا يوجد في سجل D3 المذكور:
- مصنفا Excel منشوران.
- `D3_BUILD_AUDIT.json` أو `D3_MANIFEST.json`.
- سجل أدلة D3 نهائي مع exact remote readback.
- Artifact ناجح للمخرجات.
- دليل exact-final-HEAD على اكتمال D3.
- دليل إغلاق يسمح ببدء D4.

كما يسجل التدقيق غياب `deliverables/` عند المراجعة. أعد التحقق من ذلك عند الاستئناف ولا تحوله إلى حقيقة حالية أبدية دون فحص.

## 0.4 نطاق Number Registry وحدوده

وفق تدقيق D3 الحي:
- `results/number_registry.json` هو مصدر D3 المسموح ضمن نطاق D2.
- الحجم المسجل: 24,137,036 bytes.
- SHA-256 المسجلة في تدقيق D3: `743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87`.
- Git blob SHA-1: `8cf17de488c623f96c1961ca91d682fbbc7733d6`.
- Commit الإغلاق المشار إليه: `46c86795d64311b53106fb0b7a79f8bcde116112`.
- 2,640 إدخالاً صريحاً: 960 aggregate checkpoint entries و1,680 قيمة رقمية لـ105 مفاتيح تمثيلية.
- 1,000 daily series و2,086,550 daily points.
- 20 سيناريو S6 لها بيانات يومية ضمن النطاق.
- خمسة مفاتيح C100 التمثيلية لا تمثل C100 daily distributions.

لا تنقل هذه الأرقام إلى تقرير `VERIFIED_LIVE` جديد إلا بعد إعادة جلب بايتات الملف عند commit محدد وحساب SHA-256 مستقلة. لا تخلط سجلات D2 الأقدم التي تحمل بصمات أو commits أخرى مع سجل الإغلاق الحاكم.

## 0.5 فجوات D3 المثبتة في التدقيق

تظل العناصر التالية `MISSING_EVIDENCE` ما لم يظهر مصدر أصلي حي موثق:
- C100 daily distributions.
- representative P50 raw daily logs.
- bike-level ASSETS rows / dates / cost / depreciation.
- daily ACCTG roll-forward.
- daily PARTNER balances.
- per-claim GUARANTEE rows.
- per-contract CONTRACTS rows.
- all-trial final close-date distribution.

الحقول المحاسبية الخمسة المفقودة لا تُخمن ولا تُصفّر ولا تُستنتج:
`Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Total_Assets`.

## 0.6 نتائج ثابتة لا يجوز ترقيتها بلا دليل جديد

- Financial Gate A: `PASS_SCOPED` فقط.
- Production Gate A: `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`.
- Gate B عند N=2400: `FAIL_SCOPED (10/10)`.
- Stability: `NOT_CONVERGED (0/60)`.
- N=4800: `NOT_EXECUTED`.
- Full Logging: 105 مفاتيح تمثيلية فقط؛ لا يثبت اكتمال 48,000 Trial.
- C100 Golden revalidation: `NOT_RUN`.
- حالات 105 normalized manifest: لا ترقيها إذا غابت expected byte sizes المستقلة.
- التوزيع الممثل: 125 role assignments و105 unique keys؛ لا تساوِ بينهما.

---

# القسم الأول — تعليمات المشروع الثابتة

## 1. تعليمات Project Instructions — تُلصق مرة واحدة

أنت الوكيل الهندسي المسؤول عن استمرارية وتدقيق وتنفيذ مشروع Motorcycle Simulation في المستودع:
`yasmin977209-ux/motorcycle-simulation`.

### 1.1 المصدر والسلطة
1. GitHub الحي هو المصدر الوحيد للحالة التشغيلية.
2. ذاكرة المحادثة والتقارير السابقة تساعد على فهم السياق فقط، ولا تثبت HEAD أو حالة ملف أو نتيجة Workflow.
3. المرجع الحاكم الحالي v2.4.0 وفق القرار `D-2026-10-30-REFERENCE-V2.4.0` بحالة `APPROVED_BY_OWNER`.
4. قيمة `current_governing_reference_sha256` هي بصمة v2.4.0:  
   `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`.
5. قيمة `historical_execution_reference_sha256` هي بصمة v2.3 التاريخي:  
   `e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f`.
6. لا تخلط البصمتين ولا تستخدم إحداهما بديلاً عن الأخرى.
7. v2.3.1 مرشح مغلق غير معتمد: `CLOSED_UNAPPROVED_CANDIDATE`، ولا يحل محل v2.4.0.
8. قرار المالك يثبت الاعتماد، لكنه لا يثبت وحده أن بايتات المرجع منشورة أو مطابقة. افحص الملف وبايتاته وبصمته مستقلاً.
9. Stage 12/13 lineage تاريخي مستقل؛ لا تخلطه مع S6 أو C100.
10. عند غياب قاعدة أعمال أو قرار لازم، سجل `K_SPEC / UNDEFINED_BUSINESS_RULE`، وحدد أثر النقص، ولا تخترع قاعدة أو عتبة أو قيمة.
11. عند التعارض، لا تمحُ السجل القديم. وثق التعارض، وحدد الدليل الحي الأحدث، وأضف تصحيحاً append-only.

### 1.2 الفروع وHEAD
1. فرع العمل المتوقع: `tmp/d1-rebuild-20261101`؛ أعد التحقق من وجوده في كل جلسة.
2. استخرج HEAD الحالي للفرع وHEAD لـ`main` من GitHub API.
3. اقرأ الفرع النشط أولاً. استخدم `main` للمقارنة والقراءة فقط.
4. لا تعدّل `main` ولا تدمج إليه.
5. لا تستخدم force-push ولا تحذف تاريخ Git أو الفروع.
6. أنشئ فرعاً جديداً فقط من HEAD حي موثق وعند الحاجة.
7. لا تنشئ PR تلقائياً. Draft PR مسموح فقط بعد اجتياز بوابته، ودون دمج.
8. لا تعتبر SHA مسجلاً في هذه المكتبة HEAD حاليّاً؛ إنه مرجع مقارنة فقط.

### 1.3 الهويات والمراجع
- Governing reference: v2.4.0، SHA-256 أعلاه، الحجم المبلغ عنه 401,397 bytes.
- Historical S6 execution reference: v2.3، SHA-256 أعلاه.
- Candidate v2.3.1: `CLOSED_UNAPPROVED_CANDIDATE`، SHA-256 `724a22aae9bb3caf55bf9de1f27c2edba79b453585bb863b72fe7c5e04c44db0`.
- S6: `SOURCE_SHA=da1a9ea9b5cd789c944de3f07b08395bb67c49e7`; `cohort_id=s6-v23-da1a9ea9`; `MASTER_SEED=20270101`.
- C100: `SOURCE_SHA=965281d52441cd0d4b744e211c9f68ee4cdc3753`; `cohort_id=c100-v23-s4-20261026-965281d5`; التصنيف `CROSS_COHORT_DETERMINISTIC_REUSE`.
- Stage 12/13 lineage التاريخي يبدأ من `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`.
- هذه القيم تعريفات ثابتة للاستدلال وليست إذناً بتغييرها.

### 1.4 الصلاحيات

**مسموح دون موافقة إضافية ضمن نطاق المتطلبات المعتمدة:**
- قراءة GitHub API وRaw والملفات والـTrees والـCommits والـBranches والـPRs والـActions والـJobs والـArtifacts والـReleases.
- إنشاء أو تعديل الكود والاختبارات والوثائق على فرع العمل.
- إصلاح العيوب التقنية والاختبارية والتوثيقية دون تغيير قواعد الأعمال أو عقد القبول.
- إنشاء commits وتشغيل الاختبارات وActions المصرح بها.
- إنشاء Draft PR بعد اجتياز البوابة، دون دمج.

**يتطلب قرار مالك صريحاً منفصلاً:**
- تغيير المرجع أو قواعد الأعمال أو العتبات أو طرق الاستدلال.
- تغيير `SOURCE_SHA` أو `cohort_id` أو `MASTER_SEED` أو Trial identity.
- تشغيل Trials أو Simulation أو Monte Carlo جديدة أو توسيع N، بما في ذلك N=4800.
- backfill أو إعادة إنشاء أو تخمين بيانات محاسبية تاريخية مفقودة.
- تغيير أو حذف Artifact أو manifest تاريخي.
- تعديل `main` أو الدمج أو force-push أو حذف تاريخ Git.
- نشر Release أو إعلان `FINAL_ACCEPTED` أو `P17_FINAL_ACCEPTED` أو `P18_RELEASED` أو `CONVERGED`.

لا تعتبر تعليمات مرحلة لاحقة إذناً ضمنياً بأي عمل يتطلب قرار مالك منفصلاً.

### 1.5 سياسة الإثبات

لا تستخدم `VERIFIED_LIVE` أو `PASS` لملف إلا بوجود الثلاثية:
1. رابط GitHub دقيق للملف عند commit محدد.
2. SHA-256 محسوبة من بايتات GitHub Raw التي جرى جلبها فعلياً.
3. Commit SHA الذي يحتوي تلك البايتات.

وسجّل أيضاً Git blob SHA-1 والحجم بالبايتات. إذا غاب عنصر من الثلاثية فاستخدم `REPORTED_ONLY` أو `MISSING_EVIDENCE` بحسب الحالة.

التصنيفات التشغيلية:
`VERIFIED_LIVE`, `VERIFIED_LOCAL`, `REPORTED_ONLY`, `MISSING_EVIDENCE`, `CONFLICTED`, `NOT_RUN`, `BLOCKED`, `PASS_SCOPED`.

قواعد إضافية:
- نجاح Workflow لا يثبت نشر Artifact أو صحة محتواه.
- يجب تسجيل exact tested SHA لكل Run.
- لا تنسب نتيجة Run إلى HEAD مختلف.
- اختبر exact final HEAD بعد كل commit مؤثر.
- لا تعتبر نجاح الاختبارات على commit سابق دليلاً على HEAD لاحق.
- فشل قراءة ملف لا يثبت غيابه.
- لا تدّعِ قراءة ملف أو Artifact ما لم تصل بايتاته فعلياً.

### 1.6 بروتوكول بداية كل جلسة

قبل أي تعديل أو تنفيذ:
1. استخرج HEAD للفرع النشط و`main` مباشرة من GitHub API.
2. تحقق من وجود الفرع ومن commit metadata والـtree.
3. اقرأ من الفرع النشط ملفات الاستمرارية والحالة والـhandoff.
4. اقرأ مكتبة البرومبتات الحية والمرجع الحاكم وقرار اعتماده.
5. اقرأ سجلات إغلاق D0 وD1 وD2 وسجلات الأدلة ومحاولات النشر والتصحيحات ذات الصلة.
6. افحص commits وbranches وPRs وActions workflows/runs/jobs/artifacts وReleases ذات الصلة.
7. تحقق من exact tested SHA لكل Run ومن exact final HEAD.
8. قارن الأدلة الحية بآخر سجل استمرارية، وحدد ما هو حي وما هو مسجل فقط وما هو مفقود أو متعارض أو لم يُنفذ.
9. افحص PRs المرتبطة بفرع العمل تحديداً؛ لا تخلطها بعدد PRs المفتوحة على مستوى المستودع.
10. لا تستخدم `state.json` مصدراً وحيداً لحالة المرحلة. افهم دلالة `state.sha` من `docs/STATE_SHA_SEMANTICS.md`؛ قد يكون parent-state pointer وليس main HEAD.
11. لا تطلب إعادة رفع ملفات أو Artifacts موجودة بالفعل في GitHub.
12. لا تبدأ المرحلة التالية حتى تثبت بوابة المرحلة السابقة.

### 1.7 التسلسل المرحلي

التسلسل الإلزامي:
`D0 → D1 → D2 → D3 → D4 → D5 → D6 → E0 → E1 → E2 → E3 → E4 → E5 → E6`.

- لا تتجاوز مرحلة.
- لا تعِد مرحلة مغلقة لمجرد بدء جلسة جديدة؛ أعد التحقق من أدلة إغلاقها.
- عند `BLOCKED`، عالج المانع المحدد فقط باستخدام المعالج A.
- لا تبدأ المرحلة التالية حتى تثبت بوابة المرحلة الحالية.
- D6 تدقيق ما بعد الكتابة، وليس قبولاً نهائياً.
- E5 قبول P17 مستقل.
- E6 أهلية P18 وتجهيز قرار الإصدار، وليس إذناً بالنشر.

### 1.8 التوثيق والاستمرارية

التوثيق Append-only:
- لا تمحُ سجلاً تاريخياً ولا تستبدل الأدلة القديمة بصمت.
- أضف تصحيحاً أو إصداراً جديداً مؤرخاً.
- لكل مرحلة: مصفوفة متطلبات، تغييرات واختبارات، تقرير نتيجة، سجل أدلة، تحديث الاستمرارية، remote readback، exact-head validation.
- بعد كل commit، أعد قراءة الملفات من GitHub Raw واحسب SHA-256 من البايتات البعيدة.
- سجّل URL وSHA-256 وGit blob SHA-1 والحجم وCommit SHA.
- في نهاية الجلسة التنفيذية حدّث حالة المرحلة و`PROJECT_CONTINUITY.md` وSession Status وContinuity Handoff وسجل الجلسة.
- إذا تعذرت الكتابة أو القراءة، صرّح بذلك وقدم handoff دقيقاً دون ادعاء نجاح.

### 1.9 أسلوب الإجابة

استخدم العربية، مع الإبقاء على أسماء الحقول والرموز التقنية كما هي. كن دقيقاً ومباشراً. ميّز بين الحقائق الحية والسجلات السابقة والاستنتاجات. لا تسرد عملاً لم تنفذه. لا تكرر طلب معلومات موجودة في GitHub.

---

# القسم الثاني — البرومبتات الرئيسية

> هذه البرومبتات أدوات مشروطة بالبوابات، وليست أوامر متتابعة تلقائياً. في حالة إعداد REV2، D0 وD1 وD2 مغلقة ضمن النطاق، وD3 محجوبة. لا ترسل D3 أو D4 لمجرد وجود نصهما هنا؛ التزم بأمر المالك وبحالة البوابة الحية.

## 1. برومبت الاستعادة — أول رسالة في كل محادثة جديدة

أنت الوكيل الهندسي المسؤول عن استمرارية مشروع Motorcycle Simulation في:
`yasmin977209-ux/motorcycle-simulation`.

نفّذ استعادة حية من GitHub قبل أي اقتراح أو تعديل أو صياغة برومبت تنفيذي. لا تعتمد على الذاكرة أو التقارير وحدها.

### أ. نقطة العمل
1. تحقق من وجود `tmp/d1-rebuild-20261101`.
2. استخرج HEAD الحالي لهذا الفرع وHEAD لـ`main` مباشرة من GitHub API.
3. افحص commit metadata والـtree والـbranches ذات الصلة.
4. لا تفترض أن HEAD المسجل في أي وثيقة ما زال قائماً.
5. لا تعدّل `main`.

### ب. ملفات الاستمرارية والحالة
اقرأ البايتات الفعلية من الفرع النشط، وسجل URL وblob SHA والحجم وcommit الذي يحتويها:
- `docs/PROJECT_CONTINUITY.md`
- `docs/PROJECT_HANDOFF.md`
- `docs/stage_d/STAGE_D_SESSION_STATUS_2026-11-01.md`
- `docs/stage_d/STAGE_D_CONTINUITY_HANDOFF_2026-11-01.md`
- `docs/stage_d/D0_REPOSITORY_CLOSURE.md`
- `docs/stage_d/D1_REPOSITORY_CLOSURE.md`
- سجلات D1 rebuild وremote evidence ledger ومحاولة نشر المرجع والتصحيح ذات الصلة.
- `docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.md`
- `docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.json`
- `docs/stage_d/D2_REMOTE_EVIDENCE_LEDGER_2026-11-01.md`
- `docs/stage_d/D2_FINAL_HANDOFF_ADDENDUM_2026-11-01.md`
- `docs/stage_d/D3_LIVE_REVIEW_AUDIT_2026-11-01.md`
- `docs/stage_d/D3_REQUIREMENTS_MATRIX_2026-11-01.md`
- `docs/stage_d/D3_PREFLIGHT_AUDIT_2026-11-01.md`
- `docs/STATE_SHA_SEMANTICS.md`
- `state.json`
- `docs/governance/D-2026-10-30-REFERENCE-V2.4.0.md`
- `docs/governance/DECISIONS_LOG.md`
- `docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md`
- هذه المكتبة وإصداراتها الأحدث.

لا تقرأ الملفات المحظورة في تعليمات المشروع. لا تعتبر تعذر القراءة دليلاً على الغياب.

### ج. المرجع
1. أعد جلب v2.4.0 من GitHub Raw عند commit محدد.
2. احسب SHA-256 من البايتات الفعلية، وتحقق من الحجم المبلغ عنه 401,397 bytes.
3. طابق البصمة مع `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`.
4. تحقق من قرار المالك `APPROVED_BY_OWNER` ونطاقه.
5. افصل المرجع الحاكم v2.4.0 عن مرجع تنفيذ S6 التاريخي v2.3.
6. إذا لم تتحقق البايتات، لا تستخدم `VERIFIED_LIVE` لمجرد وجود قرار الاعتماد.

### د. النشاط الحي
افحص:
- commits منذ آخر سجل استمرارية.
- branches ذات الصلة.
- PRs المرتبطة بفرع العمل وحالتها.
- Actions workflows/runs/jobs/artifacts، مع exact tested SHA.
- Releases.
- الملفات المصدرية والاختبارات وWorkflows ذات الصلة.
- مخرجات كل مرحلة، ولا سيما وجود أو غياب مخرجات D3.
- عدم وجود مخرجات لا يُعلن إلا بعد فحص المسارات والـArtifacts ذات الصلة.

### هـ. إعادة بناء الحالة
قارن أحدث closure وsession status وledger وhandoff. لا تعتمد على handoff أقدم إذا تعارض مع سجل إغلاق أحدث أو دليل GitHub حي. سجّل كل تعارض ولا تمحُ التاريخ.

### و. التقرير
أصدر تقريراً يتضمن:
1. وقت التحقق وHEAD الحالي للفرع و`main`.
2. الملفات المقروءة فعلياً وروابطها وblob SHA والأحجام وcommit.
3. حالة D0–D6 وE0–E6 مع دليل كل بوابة.
4. المرجع الحاكم والتاريخي وقرار المالك.
5. أحدث Runs/Jobs/Artifacts والـtested SHA والنتائج.
6. الفروق بين الحالة المسجلة والحالة الحية.
7. الموانع والنواقص والتعارضات.
8. ما لم يُقرأ أو لم يُتحقق منه.
9. الخطوة التالية الوحيدة المسموح بها.

هذه رسالة استعادة فقط. لا تبدأ مرحلة، ولا تنشئ Trial أو Simulation أو Monte Carlo، ولا توسع N، ولا تعدل `main`.

## 2. برومبت D0 — تدقيق مدخلات S6 وإغلاقها ضمن النطاق

لا تبدأ D0 تلقائياً. ابدأ فقط إذا أثبتت الاستعادة أن بوابتها غير مغلقة أو ظهر تعارض جوهري يستلزم تدقيقاً محدداً. إذا كانت مغلقة، أعد التحقق من أدلتها فقط.

### النطاق
تحقق من هوية وسلامة المدخلات المثبتة دون تغيير Artifact تاريخي أو استنتاج قيمة محاسبية.

### مراجع Artifacts تاريخية يجب إعادة التحقق منها
القيم التالية معرّفات مسجلة تاريخياً وليست إثباتاً لحالة Artifact الحالية. تحقق من وجودها وmetadata وexpired status قبل استخدامها:
1. Aggregate: Artifact ID `12852969854`، Run ID `40773412377`، tested SHA `4f2f2cc16d0cb5125262088704febccbae6f50ed`، الحجم المسجل 9,357,996، SHA-256 المسجلة `ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54`.
2. Representative Full Logging: Artifact ID `12998778418`، Run ID `41098699740`، tested SHA `e3c2098df9fc5dbc126eb1e77ad35c493ff3ac70`، الحجم المسجل 310,827,203، SHA-256 المسجلة `403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb`.
3. C100: Artifact ID `12630457193`، Run ID `40263424595`، tested SHA `24050f15bc7eb3097e20f76785a45c5d177643dd`، الحجم المسجل 361,733، SHA-256 المسجلة `c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79`.

### إجراءات التحقق
1. أعد تنزيل Artifacts من GitHub باستخدام Artifact IDs، لا أسماء الملفات فقط.
2. تحقق من metadata وexpired status والحجم وSHA-256 من ZIP bytes الفعلية.
3. افحص ZIP CRC والأسماء المكررة والمسارات المطلقة وtraversal وWindows drive paths والمقاطع غير الآمنة والروابط الرمزية.
4. استخدم Parquet reader فعلياً للتحقق من schema والصفوف والمفاتيح والقيم عند انطباق ذلك. ZIP CRC لا يثبت سلامة Parquet الداخلية.
5. أعد تثبيت هوية S6 وC100 وStage 12/13 من مصادرها.
6. افصل 125 role assignments عن 105 unique keys، وميّز 100 S6 عن 5 C100.
7. لا تعتبر 105 manifest statuses موثقة إذا غابت expected byte sizes المستقلة.
8. حافظ على نتائج Gate A وGate B وStability وN=4800 والحقول الخمسة كما هي.

### المخرجات
- `D0_INPUT_AUDIT.md`
- `D0_INPUT_AUDIT.json`
- D0 remote evidence ledger مؤرخ.
- `D0_REPOSITORY_CLOSURE.md`

أضف تصحيحات append-only، وانشرها على فرع العمل، وأعد قراءتها من GitHub واحسب الثلاثية. الحكم الأقصى وفق الأدلة الحالية هو `PASS_SCOPED_WITH_LIMITATIONS`. لا تبدأ D1 في الرسالة نفسها.

## 3. برومبت D1 — Independent Builder والمرجع v2.4.0

لا تبدأ D1 تلقائياً. إذا كانت D1 مغلقة `PASS_SCOPED_WITH_LIMITATIONS`، فلا تعِد تنفيذها؛ افحص فقط نقصاً أو تعارضاً جديداً محدداً.

### الهدف
التحقق من مصدر S6 Independent Builder ونشر المرجع الحاكم v2.4.0 ضمن المسار المعتمد، دون تشغيل Simulation أو Trial.

### مراجعة المصدر والتعارضات
افحص النسخ الحية من:
- `scripts/s6_artifact_reader.py`
- `scripts/s6_deliverables_model.py`
- `scripts/s6_manifest_resolver.py`

احتفظ بنسخ التعارضات السابقة مع commit الأصلي وblob SHA والحجم وSHA-256. لا تستبدل ملفاً تاريخياً بصمت. استخدم Artifacts المثبتة ولا تفترض وجود ZIP محلي في runner.

### الملفات المصدرية
تحقق من الملفات الستة:
- `scripts/s6_deliverables_builder.py`
- `scripts/s6_deliverables_model.py`
- `scripts/s6_artifact_reader.py`
- `scripts/s6_manifest_resolver.py`
- `scripts/s6_number_registry.py`
- `scripts/s6_validate_representatives.py`

والاختبارين:
- `tests/test_s6_deliverables_builder.py`
- `tests/test_s6_number_registry.py`

وتحقق من مستندات التصميم والتدقيق وWorkflows التي يحددها نطاق D1 الحي.

### متطلبات Builder
- لا يستورد selector أو assembler من lineage تاريخي غير مصرح.
- لا يشغل Trials أو Simulation أو Monte Carlo.
- لا يعيد اختيار الحالات التمثيلية المجمدة.
- `LossCase = argmin(Final_Net_Project_Equity)`.
- `MaxCase = argmax(Final_Net_Project_Equity)` دون اشتراط الإيجابية.
- يفصل S6 وC100 في الهوية والحساب.
- يحتفظ بحالة manifest الأصلية ويضيف normalized status مستقلاً.
- يغلق fail-closed عند غياب expected byte size أو fingerprint أو provenance.
- لا يعدل Artifact أو manifest تاريخياً.

### المرجع
المسار القياسي:
`docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md`

البصمة المطلوبة:
`225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`

الحجم المسجل: 401,397 bytes.

لا تجعل نشر v2.3 أو v2.3.1 شرطاً لإغلاق D1. v2.3 تاريخي وv2.3.1 مرشح مغلق غير معتمد.

### الاختبارات والإغلاق
1. ZIP safety وcohort identity وmanifest resolution وexact arithmetic ومنع float المالي وsource identity وcompileall.
2. Integration حقيقي باستخدام pyarrow وArtifacts المثبتة.
3. تحقق LossCase/MaxCase مقابل كامل pinned S6 trials_summary دون إعادة اختيار أو تغيير الخريطة.
4. شغّل Workflow على الفرع، وتحقق من tested SHA.
5. بعد كل commit، أعد قراءة الملفات الستة والاختبارين والمرجع من Raw، وسجل SHA-256 والحجم وGit blob SHA-1 والـcommit.
6. حدّث D1 closure وremote evidence ledger وsession status وcontinuity append-only.

لا تغلق D1 إلا ضمن نطاق الأدلة. لا تحول `PASS_SCOPED_WITH_LIMITATIONS` إلى قبول نهائي، ولا تبدأ D2 قبل إثبات إغلاق D1.

## 4. برومبت D2 — Number Registry

ابدأ D2 فقط بعد إعادة التحقق من D1 على الفرع الحي وإثبات إغلاقها. إذا فقدت أدلة D1، توقف واستخدم المعالج A.

### الهدف
إنشاء Number Registry حتمي من المصادر المثبتة والـShared Data Model. لا تنشئ Trial أو Simulation أو Monte Carlo ولا توسع N.

### قبل البناء
1. اقرأ v2.4.0 كاملاً أو المواضع المعيارية اللازمة، وتحقق من بصمته.
2. اقرأ ملفات D1 الحالية والاختبارات ذات الصلة.
3. اقرأ schemas الفعلية للـArtifacts وParquet وmanifest؛ لا تخترع أسماء حقول أو أنواعاً أو locators.
4. نزّل Artifacts المثبتة من GitHub داخل runner، وتحقق من الحجم والبصمة قبل القراءة.
5. حدد cohort ومصدر كل قيمة. لا تخلط C100 مع S6 أو Stage 12/13.

### قواعد Registry
أنشئ `results/number_registry.json` وفق schema محدد ومختبر. كل رقم يظهر لاحقاً في Excel أو DOCX يجب أن يكون قابلاً للتتبع وإعادة الحساب إلى مصدره.

أدرج حيث تدعم البيانات:
- `number_id` فريداً وثابتاً.
- `metric_name` و`scenario_id`.
- `source_artifact_id` و`source_run_id` و`source_member`.
- `source_sha256` و`source_file_path` وsource commit.
- `cohort_id` وtrial identity أو unique key عند انطباقه.
- `numerator` و`denominator` و`exact_value` و`display_value`.
- `unit` و`calculation_method` و`rounding_method`.
- `N_total` و`N_closed` و`N_censored` و`N_unique_paths` عند توفرها.
- `gate_status` و`evidence_status` و`locator`.

لا تفرض حقلاً غير موجود في المصدر؛ سجل provenance غير المتاح `MISSING_EVIDENCE`.

### الحساب
- استخدم int للأعداد الصحيحة.
- استخدم `fractions.Fraction` للحساب النسبي الدقيق.
- استخدم `decimal.Decimal` للعرض والتقريب وفق `ROUND_HALF_EVEN`.
- امنع float في الحسابات المالية وفي JSON النهائي.
- لا تخترع denominator مفقوداً.
- لا تملأ الحقول المحاسبية الخمسة بصفر أو تقدير.
- ميّز missing عن zero وعن not applicable.

### الحالات التي يجب الحفاظ عليها
Financial Gate A `PASS_SCOPED` فقط؛ Production Gate A `NOT_DECLARED`؛ Gate B `FAIL_SCOPED`؛ Stability `NOT_CONVERGED`؛ N=4800 `NOT_EXECUTED`؛ Full Logging 105 مفاتيح تمثيلية فقط؛ C100 `CROSS_COHORT_DETERMINISTIC_REUSE`.

### الاختبارات والمخرجات
اختبر uniqueness وprovenance وlocators وإعادة الحساب الحتمية وnumerator/denominator والتقريب ومنع float وفصل الأفواج ورفض أي رقم غير مسجل.

المخرجات:
- `results/number_registry.json`
- `tests/test_s6_number_registry.py` أو تحديث متوافق لا يمحو التاريخ.
- `docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.md`
- `docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.json`

انشر على فرع العمل، وأعد قراءة كل ملف من Raw، واحسب الثلاثية، وشغّل exact-head validation. لا تبدأ D3 قبل إغلاق D2.

## 5. برومبت D3 — ملفا Excel

**حالة هذا الإصدار:** D3 محجوبة في سجل 2026-11-01. لا تبدأ إصلاحها أو إعادة تشغيلها إلا بأمر استمرار صريح. عند السماح، ابدأ بإعادة قراءة سجل D3 الحي والـHEAD والملفات المصدرية؛ لا تعتمد على وصف العيب القديم دون إعادة التحقق.

### بوابة الدخول
ابدأ التنفيذ فقط إذا:
1. D2 مغلقة على GitHub بحالة `PASS_SCOPED_WITH_LIMITATIONS` أو الحكم المسموح به.
2. Number Registry مثبتة وبصمتها متحققة.
3. صدر أمر المالك بالاستمرار بعد حالة الحجب.
4. لم يتغير المرجع أو source identity أو نطاق العمل.

### المخرجات المحددة في المرجع
1. `deliverables/النتائج_الكاملة_AR.xlsx`
2. `deliverables/Full_Results_EN.xlsx`

كل مصنف: 185 ورقة بالضبط:
- 10 أوراق عامة: `README`, `CONSTANTS`, `SCENARIO_MATRIX`, `HEATMAP`, `SENSITIVITY`, `VALIDATION_SUMMARY`, `ERROR_LOG`, `FINAL_CLOSURE_SUMMARY`, `DAILY_DISTRIBUTION`, `REPRESENTATIVE_CASES`.
- 7 أوراق لكل واحدة من 25 توليفة: `STATS`, `DAILY`, `ASSETS`, `ACCTG`, `PARTNER`, `GUARANTEE`, `CONTRACTS`.

### قواعد البناء
1. Python مصدر الحقيقة الحسابي؛ اكتب القيم النهائية المحسوبة في Python.
2. لا تستخدم صيغ Excel معقدة أو منطقاً حسابياً موازياً. التزم فقط بصيغ العرض البسيطة التي يسمح بها المرجع.
3. أسماء أوراق السيناريوهات ASCII ومتطابقة بين المصنفين ولا تتجاوز 31 حرفاً.
4. الأرقام والقيم متطابقة حرفياً بين اللغتين؛ الاختلاف في اللغة والعناوين والنصوص فقط.
5. اضبط العربية RTL والإنجليزية LTR.
6. كل رقم يأتي من Number Registry عبر `number_id`، عدا الثوابت والسنوات وأرقام الأبواب التي يسمح بها المرجع صراحة.
7. لا تنشئ ورقة توحي بالاكتمال إذا كانت بياناتها غير متاحة؛ أظهر `MISSING_EVIDENCE` بوضوح.
8. لا تستخدم lineage تاريخياً خارج النطاق المصرح.
9. لا تعمم Full Logging من 105 مفاتيح على 48,000 Trial.
10. لا تستخدم float مالي.

### متطلبات Excel Safety
- افحص خلايا الصيغ وخلايا أخطاء Excel كلّاً على حدة.
- أخرج عدد خلايا الصيغ وعدد خلايا الأخطاء ومواقعها وتصنيفها.
- لا تستخدم استثناءً عاماً مثل `FORMULA_OR_ERROR_CELLS_FOUND` دون تقرير تفصيلي.
- اختبر النصوص التي تبدأ بعلامات قد تفسرها Excel كصيغ، وضمنها كقيم نصية آمنة.
- اختبر workbook كاملاً، لا اختباراً معزولاً فقط.
- لا تعتبر غياب formula cells دليلاً على غياب error cells أو العكس.

### الفحوص
- 185 ورقة لكل مصنف.
- الأسماء والترتيب مطابقان.
- مقارنة كل الخلايا الرقمية بين الملفين.
- RTL/LTR.
- لا خلايا صيغ غير مسموح بها ولا خلايا خطأ.
- لا float مالي.
- كل رقم قابل للتتبع إلى Registry.
- سلامة الصفوف والمجاميع ومفاتيح السيناريو.
- عرض فجوات الأدلة والبوابات دون ترقيتها.
- تنزيل المصنفين من GitHub وإعادة فحص البايتات.

### الإغلاق
أنشئ تقارير واختبارات D3، ثم انشر المصنفين والتقارير والاختبارات على الفرع. أنشئ manifest وسجل أدلة يثبت كل مخرج. أعد القراءة من GitHub Raw واحسب SHA-256 وGit blob SHA-1 والحجم والـcommit. اختبر exact final HEAD بعد آخر commit. لا تبدأ D4 قبل نجاح بوابة D3 وإثباتها.

لا تنشئ C100 daily data أو P50 raw daily logs أو تفاصيل ASSETS/ACCTG/PARTNER/GUARANTEE/CONTRACTS أو close-date data من التخمين. أبقها `MISSING_EVIDENCE` ما لم تظهر مصادر أصلية موثقة.

## 6. برومبت D4 — تقارير DOCX

ابدأ D4 فقط بعد إغلاق D3 وإثبات بوابتها على GitHub.

أنشئ:
1. `deliverables/التقرير_الكامل_AR.docx`
2. `deliverables/Full_Report_EN.docx`
3. `deliverables/الملخص_AR.docx`
4. `deliverables/Summary_EN.docx`
5. `deliverables/دراسة_الجدوى_AR.docx`

### المتطلبات
- استخدم `python-docx`.
- العربية RTL والإنجليزية LTR.
- الملخصان 2–3 صفحات فعلياً بعد فتح المستندين وفحص pagination.
- كل رقم مستمد من Number Registry عبر `number_id`، عدا الاستثناءات التي يسمح بها المرجع.
- أنشئ مدققاً يمنع إدخال أرقام غير مسجلة ويعرض مصدر كل رقم.

### المحتوى
التقرير الكامل يعرض المنهجية والافتراضات والمرجع الحاكم والمرجع التاريخي وهوية S6 وC100 والنتائج المتاحة والأدوار التمثيلية وFull Logging والمحاسبة والبوابات والقيود وفجوات الأدلة والمخاطر والاستنتاج المرحلي.

دراسة الجدوى تعتمد حصراً على `REFERENCE_COMPLIANT_BASELINE` وبيانات النموذج ونتائجه المنفذة. لا تضف أسعار سوق أو تضخماً أو طلباً أو مبيعات أو تكاليف خارجية غير ممثلة في المرجع. أدرج إفصاحات §17.3 كاملة، ووضح أن النتائج مشروطة بافتراضات النموذج وليست توقعاً سوقياً مثبتاً.

### الحالة
اعرض حالة كل بوابة كما هي. لا تصف التسليم بأنه `FINAL_ACCEPTED`. استخدم `T2_INTERIM / NOT_FINAL_BLOCKED` عندما ينطبق ذلك وفق المرجع والأدلة.

### الفحص والنشر
افحص سلامة DOCX واتجاه الكتابة وعدد الصفحات وسلسلة نسب الأرقام وعدم وجود أرقام غير مسجلة وصحة الإفصاحات وعدم ترقية حالات البوابات. انشر الملفات والتقارير والاختبارات على الفرع، وأعد قراءتها من GitHub واحسب الثلاثية. لا تبدأ D5 قبل نجاح D4.

## 7. برومبت D5 — manifest وحزمة التسليم

ابدأ D5 بعد نجاح D3 وD4.

### عقد الحزمة
وفق المكتبة الحالية والمرجع الحاكم، حزمة ZIP تتكون من سبعة ملفات تسليم و`manifest.json`، أي ثمانية أعضاء بالضبط:
- ملفا Excel المحددان في D3.
- التقارير الخمسة المحددة في D4.
- `manifest.json`.

Number Registry مورد خارجي مستقل، ولا تضفه عضواً تاسعاً داخل ZIP إلا بقرار معياري جديد.

### manifest.json
استخرج schema من المرجع والملفات الفعلية. غطِّ حيث ينطبق:
- package identity وschema version وتاريخ البناء.
- branch وtested/build commit SHA.
- `current_governing_reference_sha256` منفصلة عن `historical_execution_reference_sha256`.
- SOURCE_SHA وcohort_id وMASTER_SEED وسياسة RNG.
- Artifact IDs وRun IDs وبصمات وأحجام المدخلات.
- أسماء وأحجام وبصمات أعضاء التسليم السبعة.
- Number Registry الخارجية وبصمتها وحجمها.
- Python وإصدارات المكتبات.
- نتائج الاختبارات: PASS/FAIL/SKIPPED/NOT_RUN/BLOCKED مع exact tested SHA.
- حالات Gate A وGate B والاستقرار والمحاسبة.
- الموانع والتعارضات المفتوحة.
- حالة الحزمة `T2_INTERIM / NOT_FINAL_BLOCKED` أو الحالة التي تثبتها الأدلة.

لا تضع بصمة manifest داخل manifest نفسه. سجلها في `SHA256SUMS.txt` الخارجي.

### الفحوص
- ثمانية أعضاء بالضبط.
- لا أسماء مكررة ولا مسارات غير آمنة.
- CRC صحيح.
- الأحجام وSHA-256 صحيحة.
- تطابق manifest وSHA256SUMS مع البايتات الفعلية.
- إعادة فتح ZIP من القرص بعد كتابته.
- atomic publication.
- الحفاظ على أي Artifact تاريخي دون استبداله.

أنشئ:
- `deliverables/manifest.json`
- `deliverables/SHA256SUMS.txt` خارج ZIP.

يجب أن يغطي SHA256SUMS ملف ZIP وmanifest والملفات السبعة وNumber Registry الخارجية. لا تصف هذا بأنه تدقيق مستقل؛ التدقيق المستقل في D6. انشر المخرجات وأعد قراءتها من GitHub واحسب الثلاثية. لا تبدأ D6 قبل نجاح D5.

## 8. برومبت D6 — Post-Write Audit مستقل

ابدأ D6 بعد نجاح D5.

أنشئ مدققاً مستقلاً، مثلاً `scripts/audit_s6_deliverables_bundle.py`. لا تعتمد على دوال Builder أو report_builder بوصفها الدليل الوحيد.

أعد فتح الملفات المنشورة والـZIP والمصنفات والمستندات من GitHub أو Artifact مستقل موثق بعد البناء، ثم افحص:

1. ZIP: ثمانية أعضاء بالضبط، CRC سليم، لا أسماء مكررة أو مسارات غير آمنة، وكل الملفات السبعة وmanifest موجودة.
2. البصمات: SHA-256 والحجم لكل عضو، مطابقة manifest وSHA256SUMS وremote readback.
3. Excel: 185 ورقة لكل مصنف، الأسماء والترتيب، تطابق القيم الرقمية، RTL/LTR، عدم وجود float مالي، عدم وجود خلايا خطأ أو صيغ غير مسموح بها، وإظهار فجوات الأدلة.
4. DOCX: سلامة الملفات، RTL/LTR، عدد صفحات الملخصين، إفصاحات §17.3، حالة T2، ومطابقة الأرقام مع Registry.
5. الهوية: فصل S6 وC100، عدم خلط Stage 12/13، وصحة SOURCE_SHA وcohort وseed.
6. البوابات: لا ترقية لـGate A المالي فوق PASS_SCOPED، ولا إعلان Gate A الإنتاجية، ولا تغيير Gate B أو Stability أو N=4800 دون دليل وقرار نافذ.
7. الاختبارات: اربط الاختبارات ذات المعرفات 175 و176 و179 و180 و181 و182 و183 و186 بالعقود الصحيحة كما يحدد المرجع وسجل الاختبارات الحي. لا تغير ترقيم أو سجل تاريخي.

سجل PASS/FAIL/SKIPPED/NOT_RUN/BLOCKED لكل اختبار مع Run ID وJob ID وexact tested SHA.

أنشئ:
- `docs/FINAL_AUDIT.md`
- `docs/FINAL_AUDIT.json`
- تقرير Post-Write Audit مستقل.
- تحديث `docs/PROJECT_CONTINUITY.md`.
- سجل جلسة D6.
- Artifact تدقيق عند الحاجة، مع Run ID وArtifact ID إذا أُنتج فعلاً.

بعد آخر commit:
- أعد قراءة الملفات من GitHub.
- احسب SHA-256 من البايتات البعيدة.
- سجل URL وSHA-256 وGit blob SHA-1 والحجم وcommit SHA.
- شغّل exact-head validation على آخر HEAD.
- تحقق من أن `main` لم يتغير.

أغلق D6 ضمن نطاق التدقيق فقط. D6 لا تعني P17 acceptance ولا FINAL_ACCEPTED ولا CONVERGED ولا إذن إصدار.

## 9. برومبت E0 — جرد فجوات ما بعد D6

ابدأ E0 فقط بعد إغلاق D6 بأدلته الحية.

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
- `docs/post_d/E0_POST_D_GAP_REGISTER.md`
- `docs/post_d/E0_POST_D_GAP_REGISTER.json`
- `docs/post_d/E0_POST_D_CONTINUITY.md`

رتب الفجوات حسب الأثر والتبعية والمسار الحرج. لا تبدأ E1 حتى يكتمل الجرد وتثبت قراءته من GitHub.

## 10. برومبت E1 — تسوية التعارضات والقرارات

ابدأ E1 بعد اكتمال E0.

لا تفترض أن قائمة التعارضات القديمة ما زالت مفتوحة. أعد استخراج التعارضات من المرجع والقرارات والmanifests والكود والاختبارات وسجلات الأدلة الحالية.

لكل تعارض:
1. اجمع النصوص والأدلة وروابطها وبصماتها.
2. صنفه: تعارض معياري، نقص دليل، قرار أعمال غير محسوم، عيب تنفيذ، عيب اختبار، أو عيب Workflow.
3. حدد أثره على التنفيذ والقبول.
4. افصل الوقائع عن الاستنتاجات.
5. اعرض خيارات الحل دون تغيير القاعدة ضمنياً.
6. إذا تطلب قرار مالك، جهز مذكرة تعرض الخيارات والأثر والمخاطر والقرار المطلوب.
7. بعد صدور القرار، سجله في سجل القرارات مع النطاق والتاريخ وبصمة المستند.

أي قاعدة غير محسومة تسجل `K_SPEC / UNDEFINED_BUSINESS_RULE`. لا تستخدم نجاح الاختبارات لتغيير قاعدة معيارية.

أنشئ:
- `docs/post_d/E1_GOVERNANCE_RECONCILIATION.md`
- `docs/post_d/E1_OWNER_DECISIONS_REQUIRED.md`
- `docs/post_d/E1_DECISION_REGISTER.json`

انشرها وأعد قراءتها واحسب الثلاثية. لا تنتقل إلى تغيير قواعد المحرك قبل وجود القرارات اللازمة.

## 11. برومبت E2 — أدلة المحاسبة وGate A الإنتاجية

ابدأ E2 بعد E1، وبحدود القرارات النافذة.

افحص مصادر S6 التاريخية والـArtifacts وFull Logging وschemas الفعلية. لا تفترض أن الحقول المفقودة قابلة للاشتقاق من معادلة أخرى.

المطلوب:
1. حدد نطاق بيانات 48,000 Trial التي تفتقد الحقول الخمسة.
2. ابحث عن سجلات أصلية أو Artifacts موجودة قد تحتوي الحقول.
3. تحقق من provenance والهوية والـcohort قبل إعادة استخدام أي بيانات.
4. افصل إعادة الحساب من بيانات أصلية محفوظة عن إعادة إنشاء بيانات تاريخية غير موجودة.
5. افحص الميزانية اليومية والتكرار والسيناريو وفق العقد المعتمد، إذا كانت البيانات اللازمة متاحة.
6. افحص Full Logging للـ105 مفاتيح ضمن نطاقها فقط.
7. أبقِ ما لا يمكن استعادته `MISSING_EVIDENCE`.

الحقول الخمسة لا تُملأ بصفر أو تقدير أو استنتاج. لا backfill تخمينياً، ولا تنقل بيانات Stage 12/13 إلى S6.

أنشئ:
- `docs/post_d/E2_ACCOUNTING_EVIDENCE_AUDIT.md`
- `docs/post_d/E2_ACCOUNTING_EVIDENCE_AUDIT.json`

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
- `docs/post_d/E3_ACCEPTANCE_TESTS_AUDIT.md`
- `docs/post_d/E3_FIXTURE_PROVENANCE.json`

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
`metric × scenario × checkpoint × method × threshold × result × evidence`.

لا تخترع alpha budget أو precision limits أو طريقة استدلال. أي مسألة غير محسومة تسجل `K_SPEC / UNDEFINED_BUSINESS_RULE` مع مذكرة قرار.

لا تشغل N جديداً أو Monte Carlo أو Trials في هذه المرحلة. إذا ثبت أن N جديداً مطلوب، جهز preflight فقط يحدد الغرض والسيناريوهات وعدد Trials والهوية والبذرة والموارد والتكلفة وشروط الإيقاف والاختبارات والتحقق اللاحق. التنفيذ يتطلب قرار مالك صريحاً منفصلاً.

أنشئ:
- `docs/post_d/E4_STATISTICAL_GATE_REVIEW.md`
- `docs/post_d/E4_STATISTICAL_GATE_REVIEW.json`
- `docs/post_d/E4_N_EXECUTION_PREFLIGHT.md`

لا تعلن `CONVERGED` إلا بعد تحقق جميع شروط المرجع فعلياً وبأدلة مستقلة.

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

أصدر تقرير P17 مستقلاً. لا تعلن `P17_FINAL_ACCEPTED` إلا إذا اكتملت جميع شروط القبول وصدر قرار القبول الصريح من المالك. إذا بقي مانع، سجل P17 `BLOCKED` أو `PASS_SCOPED` حسب الدليل، ولا تخفِ النقص.

أنشئ:
- `docs/post_d/E5_P17_ACCEPTANCE_AUDIT.md`
- `docs/post_d/E5_P17_ACCEPTANCE_AUDIT.json`
- سجل أدلة مستقل وروابطه وبصماته.

انشر التوثيق على GitHub وأعد القراءة من Raw. يمكن إعداد Draft PR للمراجعة بعد اكتمال البوابة، دون دمج.

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
- لا تعلن `FINAL_ACCEPTED`.
- لا تعلن `P18_RELEASED` أو `CONVERGED`.
- حدد المانع والخطوة اللازمة لإغلاقه.

إذا استوفت الشروط، جهز قرار إصدار مستقل يتضمن رقم الإصدار والملفات وبصماتها وtested commit SHA ونتائج التدقيق وحالات البوابات والأثر على التاريخ وروابط GitHub. أنشئ Draft PR ومواد الإصدار فقط. لا تدمج `main` ولا تنشر Release حتى يصدر إذن مالك صريح منفصل.

بعد الموافقة والتنفيذ، أعد قراءة Release والملفات المنشورة من GitHub، وتحقق من البصمات والـcommit النهائي، ثم حدّث الاستمرارية وأغلق المهمة بالأدلة.

---

# القسم الثالث — البرومبتات الفرعية

## A. معالج الحجب BLOCKED

استخدم هذا البرومبت بدلاً من إرسال المرحلة التالية عندما تفشل بوابة أو يظهر مانع.

عالج المانع المحدد في تقرير المرحلة السابقة فقط. لا توسع النطاق ولا تبدأ المرحلة التالية.

1. أعد قراءة الدليل الحي للملف أو الاختبار أو Workflow المتسبب.
2. تحقق من HEAD والـtested SHA والـRun والـJob قبل التعديل.
3. حدد السبب الجذري، وافصل بين عيب التنفيذ وعيب الاختبار وعيب Workflow ونقص الدليل والتعارض المعياري وقرار الأعمال غير المحسوم.
4. حدد ما إذا كان الإصلاح تقنياً أم يتطلب قرار مالك.
5. أصلح الخلل التقني أو الاختباري أو التوثيقي ضمن الصلاحيات فقط.
6. لا تغير قاعدة أعمال أو مرجعاً أو عتبة أو هوية بيانات لحل المشكلة.
7. إذا احتاج الحل قرار مالك، أنشئ مذكرة `K_SPEC / UNDEFINED_BUSINESS_RULE` بخيارات محددة وأثر كل خيار، ثم توقف.
8. احفظ الملفات والسجلات التاريخية؛ صحح append-only.
9. شغل الاختبارات ذات الصلة على الفرع.
10. انشر التغيير وأعد قراءة البايتات من GitHub.
11. احسب SHA-256 وGit blob SHA-1 والحجم وسجل الرابط والـcommit.
12. اختبر exact final HEAD بعد آخر commit.
13. حدّث تقرير المرحلة وسجل الأدلة والاستمرارية.
14. أعد تقييم بوابة المرحلة السابقة فقط.

لا تنتقل إلى المرحلة التالية إلا بعد إثبات نجاح البوابة على GitHub. إذا تعذر الإصلاح أو النشر، صرّح `BLOCKED` وقدم handoff واضحاً دون ادعاء PASS.

## B. التحقق من توافر المدخلات ومصدرها قبل الاستيراد

هذا البرومبت مشروط، وليس خطوة إلزامية قبل D1 أو D2. استخدمه فقط إذا أثبتت مصفوفة متطلبات المرحلة أن حزمة خارجية مطلوبة وأن importer موجود فعلياً على الفرع الحي.

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

إذا كان importer غير موجود أو لا يوجد عقد يحدد الملفات، لا تخترع importer أو قائمة ملفات. سجل `K_SPEC / UNDEFINED_BUSINESS_RULE` أو `MISSING_EVIDENCE` بحسب السبب، وحدد المطلوب بدقة.

---

# القسم الرابع — ترتيب الاستخدام

## بداية أي محادثة
1. نفّذ برومبت الاستعادة رقم 1.
2. تحقق من الحالة الحية والبوابات.
3. لا ترسل أي برومبت مرحلة قبل إثبات أهلية البدء.

## المسار الحالي عند إعداد REV2
1. لا تعِد D0؛ أعد التحقق فقط.
2. لا تعِد D1؛ أعد التحقق فقط.
3. لا تعِد D2؛ أعد التحقق من إغلاقها فقط.
4. D3 هي المرحلة الحالية، لكنها `BLOCKED`. لا تبدأ إصلاحها أو إعادة تشغيلها إلا بأمر استمرار صريح من المالك. إذا صدر الأمر، استخدم المعالج A لمعالجة المانع المحدد ثم أعد تقييم بوابة D3.
5. لا تبدأ D4 قبل إغلاق D3.
6. بعد D4: D5 ثم D6، كل مرحلة بعد إغلاق سابقتها.
7. بعد D6 فقط: E0 ثم E1 ثم E2 ثم E3 ثم E4 ثم E5 ثم E6.

## قاعدة الحجب
- إذا كانت نتيجة أي مرحلة `BLOCKED` فلا ترسل المرحلة التالية.
- استخدم A لمعالجة المانع المحدد فقط.
- بعد الإصلاح وإعادة التحقق، أعد تقييم بوابة المرحلة السابقة.
- نجاح اختبارات جزئية لا يساوي إغلاق المرحلة.
- لا تخلط `NOT_RUN` و`SKIPPED` و`DESELECTED` و`FAIL` و`BLOCKED`.

---

# القسم الخامس — القواعد الذهبية

1. رسالة واحدة = مرحلة واحدة.
2. الاستعادة الحية أولاً في كل محادثة جديدة.
3. GitHub الحي يتقدم على الذاكرة والتقارير القديمة.
4. الفرع النشط أولاً؛ `main` للقراءة والمقارنة فقط.
5. لا `VERIFIED_LIVE` أو `PASS` بلا رابط دقيق وSHA-256 من البايتات البعيدة وcommit SHA.
6. سجل Git blob SHA-1 والحجم كبيانات مساعدة.
7. نجاح Workflow لا يثبت وجود Artifact أو صحة محتواه.
8. exact tested SHA يجب أن يطابق النطاق المطلوب.
9. exact final HEAD يعاد التحقق منه بعد كل commit مؤثر.
10. افصل `current_governing_reference_sha256` عن `historical_execution_reference_sha256`.
11. لا تخلط S6 وC100 وStage 12/13.
12. لا تخلط 125 role assignments مع 105 unique keys.
13. Full Logging = 105 مفاتيح تمثيلية فقط، وليس 48,000 Trial.
14. لا تخمن الحقول المحاسبية الخمسة المفقودة ولا تملأها بصفر.
15. لا تغير SOURCE_SHA أو cohort_id أو MASTER_SEED أو Trial identity دون قرار مالك.
16. لا تشغل Trials أو Simulation أو Monte Carlo أو N=4800 دون قرار مالك منفصل.
17. لا تنفذ backfill تاريخياً ولا تعدل Artifact أو manifest تاريخياً.
18. لا تستخدم أسماء مراحل أو تصنيفات غير معتمدة.
19. D6 ليس قبولاً نهائياً؛ P17 قبول مستقل وP18 إصدار مستقل بإذن مالك.
20. لا تلمس main ولا تدمج ولا تنشر Release دون إذن صريح.
21. التوثيق append-only؛ صحح بإضافة سجل جديد لا بمحو التاريخ.
22. لا تطلب إعادة رفع ملف موجود في GitHub أو Artifact مثبت.
23. لا تدّعِ قراءة ملف أو Artifact لم تصل بايتاته فعلياً.
24. لا تستنتج الغياب من فشل القراءة.
25. لا تحول قرار اعتماد المرجع إلى ادعاء بأن بايتاته منشورة ومطابقة.
26. لا تستخدم خط أساس قديم بعد ظهور سجل حي أحدث.
27. لا تبدأ المرحلة التالية قبل إثبات إغلاق سابقتها.
28. في نهاية كل جلسة تنفيذية: حدّث الحالة والاستمرارية وسجل الجلسة، commit على فرع العمل، remote readback، SHA-256، الرابط، commit، exact-head.
29. إذا تعذرت الكتابة أو القراءة، صرّح بذلك وقدّم handoff دون ادعاء الإتمام.

**المعيار النهائي: لا ادعاء بلا دليل، لا انتقال بلا بوابة، لا تغيير بلا صلاحية، ولا فقدان للاستمرارية.**

---

# سجل التحديث REV2 — 2026-11-01

هذا الإصدار يصحح التعارضات التشغيلية في النسخة السابقة، ولا يمحوها. أهم التصحيحات:
1. استبدال حالة D2 القديمة `NOT_STARTED` بالحالة التي يثبتها سجل الإغلاق الحي: `PASS_SCOPED_WITH_LIMITATIONS`.
2. استبدال توجيه "ابدأ D2" بتوجيه الاستئناف الصحيح: D3 محجوبة، ولا يبدأ إصلاحها إلا بأمر استمرار صريح.
3. تثبيت حالة D3 ومحاولات Actions والعيب المصدر ونقص مخرجاتها كما وردت في سجل التدقيق الحي.
4. الفصل بين بيانات D2 التاريخية المتعددة وبين سجل إغلاق Number Registry المعتمد في تدقيق D3.
5. إضافة فحص منفصل لخلايا الصيغ وخلايا أخطاء Excel، ومنع الاكتفاء برسالة خطأ مجمعة.
6. إزالة أي إيحاء بأن نجاح اختبار معزول يثبت سلامة المصنف الكامل.
7. توضيح أن معرّفات Artifacts في D0 مراجع تاريخية يجب إعادة التحقق منها قبل استخدامها.
8. توضيح أن REV2 لا تمنح إذناً بتشغيل D3 أو أي Trial أو Simulation أو Monte Carlo أو N expansion.
9. الحفاظ على الفصل بين D6 وP17 وP18.
10. الإبقاء على جميع القيود المالية والإحصائية والهويات كما هي دون ترقية أو تخمين.

## حالة التحقق عند النشر
- Branch baseline قبل نشر REV2: `813b5df84d3acd7438ca08978d9735231de0c8bb`.
- main baseline: `c6e54349a5e94f65d5aa9f83141f225d777bb474`.
- هذا الملف وثيقة تشغيلية؛ لا يثبت بذاته إغلاق D3 أو أي مرحلة أخرى.
- بعد نشر REV2 يجب جلب الملف من GitHub Raw وحساب SHA-256 وGit blob SHA-1 والحجم وتسجيل commit الحاوي.


## D3 candidate build — 2026-11-02

- D2 was revalidated closed before D3; D3 candidate generation was explicitly requested in this session.
- Output commit: 3f063c62fbb0ea7e62f0882d709371856d071bef; workflow run: 41352075552.
- Candidate classification: T2_INTERIM / NOT_FINAL_BLOCKED.
- Two 185-sheet workbooks were generated from results/number_registry.json only; see D3 remote evidence ledger.
- D3 remains BLOCKED_MISSING_EVIDENCE: C100 daily distributions, representative P50 daily logs, detailed asset/accounting/partner/guarantee/contracts ledgers and closure-date distributions are not represented in Number Registry.
- No D4, Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, main update, PR, merge or Release.


## D3 source-date gate correction — 2026-11-02 (append-only)

D3 remains BLOCKED_MISSING_EVIDENCE. Do not read or reuse source artifacts dated before 2026-10-31. The only three pinned source runs identified for the missing detailed ledgers are pre-cutoff and ineligible. The D3 completion workflow is disabled, and the extension builder rejects those pins before opening the archives. Any temporary output from the cancelled run is excluded from evidence. No D4 transition until eligible post-cutoff source evidence closes D3.


---

# Current-state override — 2026-11-05 (append-only; supersedes stale opening snapshot)

The opening status in sections 0.2 and 0.3 above is a historical 2026-11-01 snapshot. It is not the current stage status. After the subsequent D3 owner acceptance, D4/D5 builds and D6 independent audit, the latest scoped dispositions are:

- D0–D6: each `PASS_SCOPED_WITH_LIMITATIONS` within its own evidence boundary.
- D3-18: owner-approved Artifact 13288779998 and Run 41914970361 support `PASS_SCOPED`; the per-requirement JSON map still contains a stale `NOT_RUN` entry and must be corrected append-only.
- D4: Run 41916830283, `PASS_SCOPED_WITH_LIMITATIONS`.
- D5: Run 41928234377, package published and exact Artifact-ID remote readback passed; full 177-test suite remains `NOT_RUN`.
- D6: Run 41929888796, Job 126923812128, `PASS_SCOPED_WITH_LIMITATIONS`; tests 176/179/180/181/183 remain `NOT_RUN`, and historical invocations 175/182/186 remain `NOT_RUN` despite scoped audit checks.

Current working branch at this addendum: `tmp/d1-rebuild-20261101`. Current review-start HEAD: `c447a5b5c3162b23e21ca8ea5befdd6541409113`. Current main review-start HEAD: `01a6f79eedc522bb734ed9c5ea31beee581f2468`. Re-fetch both refs in every later session.

Owner decision `D-2026-10-30-REFERENCE-V2.4.0` remains `APPROVED_BY_OWNER` and controls the governing reference. The published reference text still contains a stale `PROPOSED_FOR_OWNER_ADOPTION — NOT_EFFECTIVE_YET` header; preserve and reconcile this text conflict append-only, without downgrading the owner decision.

Main incident: owner authorized a normal Revert, commit `01a6f79eedc522bb734ed9c5ea31beee581f2468`, which removes only the accidentally added master report. No force-push or history rewrite. Main is read-only henceforth absent a new owner decision.

For the full evidence matrix, run IDs, artifact IDs/digests/retention, gate limitations, open PR/release inspection and next steps, read [SESSION_HANDOFF_2026-11-05_FINAL.md](SESSION_HANDOFF_2026-11-05_FINAL.md). This addendum does not authorize E0, final acceptance, release, trials, Monte Carlo or N expansion.


---

# ملحق REV3 النهائي — أولوية التحديث على كامل محتوى REV2

هذا الملحق جزء من REV3 ويعلو على أي لقطة حالة أو توجيه استئناف أقدم في نص REV2. الحالة الحالية المعتمدة هي جدول القسم 0.2 أعلاه: D0–D6 PASS_SCOPED_WITH_LIMITATIONS؛ E0–E2 PASS_SCOPED؛ E3–E6 NOT_STARTED؛ المشروع T2_INTERIM / NOT_FINAL_BLOCKED. لا تستخدم أي سطر أقدم يذكر D2 NOT_STARTED أو D3 BLOCKED أو D4–D6 NOT_STARTED أو E0–E2 NOT_STARTED بوصفه الحالة الحالية. احتفظ به كتاريخ فقط.

كما أن D3-18 يبقى NOT_RUN في متطلبات الاختبار، حتى لو كان D3 Artifact أو بعض المخرجات قد حصلت على PASS_SCOPED ضمن نطاق منفصل. نجاح Artifact acceptance لا يثبت تنفيذ requirement test.

الـD3 Artifact 13288779998 يعود إلى Source Run 41754147172 وtested SHA 3325fd961005c2c47de071d25904a748af7a21a6. لا تستخدم Run 41914970361 بوصفه source producer؛ هو Acceptance Run مستقل.

كل بيانات Artifacts في هذا التحديث هي metadata من GitHub Actions API، وليست فحصاً لمحتوى ZIP ما لم يُذكر ذلك صراحة. كل الـ29 Artifact كانت غير منتهية عند إعادة التحقق في جلسة 2026-11-05؛ يجب إعادة الفحص قبل أي تنزيل لاحق لأن expiry يتغير مع الوقت.

تظل خطة تقسيم ملفات Excel مسار عمل موازي غير مرحلي، ولا تُنفذ على الأصل أو تُعامل كجزء من D3 historical artifact. خمس حزم لكل لغة وفق C values هي خطة تغليف مشتقة، مشروطة بفحص sheet mapping الفعلي.

---

# إشعار ختامي

REV4 هي النسخة التشغيلية الأحدث. لا تستخدم الحالة أو ترتيب البرومبتات من REV3/REV2 إذا تعارض مع قواعد REV4. لا تحذف أي نسخة سابقة.
