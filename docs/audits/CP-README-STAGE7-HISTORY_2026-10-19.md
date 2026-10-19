# CP-README-STAGE7-HISTORY — تصحيح توثيق README على فرع مرشح — 2026-10-19

## الحكم

**DOCS_CANDIDATE_UPDATED_AND_READ_BACK; MAIN_UNCHANGED.** تم تصحيح وصف Stage 7 في README على فرع مرشح فقط، والحصول على قراءة راجعة مستقلة ومقارنة commits تثبت أن المسار الوحيد المتغير هو `README.md`. لم يتم دمج التغيير أو فتح PR.

## الهوية والدليل

- المستودع: `yasmin977209-ux/motorcycle-simulation`.
- Base/main SHA: `647c19826b90d8224ce73ef9b90c306a45e03fb0`.
- المرشح: `tmp/cp-readme-stage7-history-20261019`; commit `0642e4325e2fdcc941783410b2680a65b7f909a5`; parent = main SHA أعلاه.
- الملف: `README.md`; blob قبل التغيير `08d666bff504609fc26acb4523c25812c61fac6e`; blob بعد التغيير `e997794450352d9d4d3135413fc1120830166c5a`.
- مقارنة GitHub: `main...candidate` = commit واحد إلى الأمام، ملف واحد فقط `README.md` (20 إضافة، 8 حذف، 28 سطر تغيير).
- قراءة راجعة من الفرع أعادت Blob SHA المطابق تمامًا للـblob الناتج من الكتابة. لم يتغير main/state.json ولا المصدر أو الاختبارات أو أي Workflow.

## ما صُحّح في README

1. صُرّح بأن `.github/workflows/stage7-gates.yml` ليس ضمن مجلد Workflows النشطة على `main)، مع ذكر النسخة التاريخية المؤرشفة والمعطّلة `docs/legacy-workflows/stage7-gates.yml.disabled`.
2. أُبقي وصف البوابات الأربع لكنه وُسم صراحةً بوصفه تاريخيًا وليس دليلًا على تشغيل حالي أو PASS.
3. سُجل الفرق بين تعريفي `stage7-authoring-verify.yml` و`stage7-full-run.yml`, مع توثيق أن تشغيل `stage7-full-run.yml` مربوط بدفع إلى الفرع `tmp/stage7-full-run-20261004` تحديدًا وبصلاحيات كتابة عالية.
4. أُبقيت نتيجة 163 اختبارًا (119 ناجحًا و44 فاشلًا) بوصفها لقطة تاريخية، لا نتيجة اختبارات حالية لـmain.
5. نُبه إلى خطر Stage 7 `G2_RISK` مع إبقاء قيم timeout 40/45 دون تغيير.

## التحقق والحدود

- اختُبرت هوية التغيير بمقارنة commits فقط؛ لا pytest، ولا YAML check، ولا Workflow، ولا CLI، ولا Monte Carlo، ولا Trial أو Checkpoint.
- لم يتغير main ولم يُفتح أو يُدمج PR. لم تتغير SOURCE_SHA أو master_seed/RNG أو sampling أو البيانات التاريخية أو Trial IDs أو Golden coverage.
- لم يُلمس `.github/workflows/stage7-full-run.yml` أو `tests/test_stage7_authoring.py`. أي إصلاح لمفتاح concurrency ما زال يتطلب الموافقة الصريحة المحددة التي يطلبها المشروع.
- `tested_sha=NOT_RUN`; هذا تغيير توثيقي فقط.
