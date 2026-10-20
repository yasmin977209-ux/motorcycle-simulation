# R4 — تدقيق Parquet للأدوار في V3 وحقول Stage 12 — 2026-10-21

**النطاق:** قراءة أدلة موجودة فقط؛ لا إنتاج ولا تعديل بيانات.
1. **الملفات/المدخلات:** V3 Artifact `11503510055` / Run `37662891608` / producer SHA `6128b22864bb171ba49ec15dbb42439a6513c30c`، ZIP SHA-256 `111eb7a2abd7b85625a02c55ee6f3140a14644ef253141bfdc3f8fc5ae4c287d`.
2. **Stage 12:** Artifact `11634501915` / Run `37964656154` / producer SHA `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`; official evidence pins ZIP SHA-256 `7d67097186dad801c6f0377a70decb5cf8dadea8f82a0b86956823a6a4191cf1` and Parquet member SHA-256 `6beecb837a3c6b71f34aedbeb958e8dd176cce3d60b2dfa1b95ee9bd57e6a380`.
3. **المشكلة:** runtime المحلي لا يحتوي pyarrow/fastparquet، لذلك لا يمكن إعادة حساب MaxCase V3 أو التحقق من schema Stage 12 مباشرةً محليًا.
4. **التصنيف:** `DATA/PROVENANCE / MISSING_EVIDENCE`، ليس عيبًا مثبتًا في محرك المحاكاة.
5. **التغيير المقترح الأدنى:** workflow مؤقت بقراءة فقط، يستخدم `GITHUB_TOKEN` بصلاحية `actions: read` لتنزيل Artifact IDs المثبتة، ثم يثبت SHA-256 قبل الفك.
6. يفك فقط `trial_results.parquet` من V3 ويقرأه بـPyArrow؛ لا يشغل Trial أو Monte Carlo أو CS.
7. يتحقق من `scenario=C050_G000` و`source_sha` و450 صفًا و450 trial_id فريدًا متصلًا من 1 إلى 450.
8. يحسب أعلى `Final_Net_Project_Equity` موجب فعليًا من الصفوف الـ450، مع كسر التعادل بأصغر `trial_id` كما ينص `D-2026-10-10-03`.
9. يثبت IDs والقيم المحفوظة لـP10/P50/P90/Loss من البيانات نفسها للمقارنة، ولا يستخدم manifest المرشح مصدرًا للحقيقة.
10. يقرأ schema وسجلات Stage 12 Parquet لتحديد الأسماء الفعلية لأي أعمدة تتضمن partner/reinvestment/memo/balance، وكذلك `Cumulative_Project_Profit` و`Retained_Earnings`.
11. معيار القبول: artifact hashes صحيحة؛ coverage/IDs سليمة؛ equity أعداد صحيحة؛ JSON evidence يتضمن cohort/source/artifact/run/head SHA والنتيجة وسجل أسماء الأعمدة.
12. يرفع JSON evidence كArtifact مستقل، ولا يغير ملفات المدخلات أو يعيد رفعها بوصفها Golden.
13. **المخاطر:** أي اختلاف في digest أو هوية المصدر/السيناريو أو تغطية التجارب يجعل النتيجة `BLOCKED` ولا يُستبدل الملف بمرجع آخر.
14. لا تغيير لـ`main` أو `SOURCE_SHA` أو seed/RNG/cohort/trial IDs/manifest/Parquet؛ ولا إنتاج XLSX أو ملفات التسليم.
15. الفرع يبدأ من `main` HEAD `6a218ebe0fccf210ec18f3552b141afbdd1a49ef` ويظل مؤقتًا.
