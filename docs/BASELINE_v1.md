# BASELINE_v1 — خط الأساس للاختبارات الحالية كما هي

**التاريخ:** 2026-10-25  
**مرجع المقارنة:** `المرجع_النهائي_الموحد_v2.2.md` — 23.2 و23.4 وج.1 وج.5 وج.6.  
**رأس المصدر/الاختبارات المختبَر:** `c6e54349a5e94f65d5aa9f83141f225d777bb474` (`main`).  
**Commit تشغيل الاختبار:** `798aa1c0584b3063d025ce9362685d6b14d0fa57`; الأب هو رأس المصدر أعلاه. فحص Commit يؤكد أنه أضاف `.github/workflows/u1-baseline-20261025.yml` فقط؛ لم يغيّر ملفات المصدر أو الاختبارات.  
**الأمر المنفَّذ كما هو:** `python -m pytest -q tests`  
**بيئة التنفيذ:** GitHub Actions، `ubuntu-latest`، Python `3.11.17`، وتثبيت `requirements.txt` نجح.  
**تشغيل Actions:** [40203751819](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40203751819)  
**وقت pytest كما سجله المخرج:** `403.31 seconds (0:06:43)`; **رمز خروج pytest:** `1`.

## 1. ملخص المخرج الفعلي

| الحالة | العدد الفعلي في مخرج pytest |
|---|---:|
| PASS | 511 |
| FAIL | 5 |
| DEFERRED (حالة pytest أصلية) | 0؛ pytest لا يصدر هذه الفئة |
| ADJUDICATION (حالة pytest أصلية) | 0؛ pytest لا يصدر هذه الفئة |
| SKIPPED | 1 |
| التحذيرات | 1 |
| إجمالي عناصر النتيجة | 517 |

هذه نتيجة تشغيل خام (ليست بوابة قبول ناجحة). لا يُعاد توصيفها على أنها all-tests PASS. إخراج `-q` لم يُظهر اسم عنصر الاختبار الذي تم تخطيه؛ لذلك لا يُخمن اسمه.

### بصمة دليل التنفيذ

- مخرج pytest الحرفي: `5 failed, 511 passed, 1 skipped, 1 warning in 403.31s (0:06:43)`.
- متغير الفحص في الـrunner: `U1_PYTEST_EXIT_CODE=1`.
- سجل الأمر ورمز الخروج حُفظا كـArtifact: [u1-baseline-798aa1c0584b3063d025ce9362685d6b14d0fa57.zip](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40203751819/artifacts/12603068262).
- SHA-256 لبصمة ZIP كما أبلغ بها Actions عند الرفع: `6121563c9f09d32118e983064864e6fe0f0c20d850e91824d97a2140b7eb017c`.
- التحذير الوحيد من pytest: `scripts/stage13_assemble.py:346 — DeprecationWarning: invalid escape sequence '\\ '`.

## 2. كل إخفاق ورسالة التنفيذ

1. **الاختبار 127 — `test_127_تطابق_التسلسلي_والمتوازي`**  
   الرسالة: `FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/motorcycle-simulation/motorcycle-simulation/results_stage5/worker_equivalence_manifest.json'`.  
   ما تعنيه الرسالة: ملف دليل Stage 5 المطلوب غير موجود في تشغيل pytest الخام؛ لم يصل الاختبار إلى مقارنة نتائج التسلسلي والمتوازي.

2. **الاختبار 159 — `test_159_اختيار_التكرار_التمثيلي_حسب_Final_Net_Project_Equity_فقط`**  
   الرسالة: `FileNotFoundError: /home/runner/work/motorcycle-simulation/motorcycle-simulation/results_stage5/trials_summary.parquet`.  
   ما تعنيه الرسالة: ملف مدخل Stage 5 غائب؛ لم يُختبر اختيار التكرار من بيانات هذا التشغيل.

3. **الاختبار 160 — `test_160_التكرارات_التوضيحية_الاربعة_تنتج_فعليا`**  
   الرسالة: `FileNotFoundError: /home/runner/work/motorcycle-simulation/motorcycle-simulation/results_stage5/trials_summary.parquet`.  
   ما تعنيه الرسالة: نفس ملف الملخص غائب؛ لم يُختبر إنتاج التكرارات التوضيحية من هذا التشغيل.

4. **الاختبار 161 — `test_161_DAILY_DISTRIBUTION_لكل_يوم_تقويمي_بلا_فجوات`**  
   الرسالة: `FileNotFoundError: /home/runner/work/motorcycle-simulation/motorcycle-simulation/results_stage5/daily_distribution.parquet`.  
   ما تعنيه الرسالة: ملف التوزيع اليومي غائب؛ لم يُختبر اكتمال تواريخ التوزيع من هذا التشغيل.

5. **`tests/test_monte_carlo_round2.py::test_parallel_fingerprints_match_across_python_hash_seeds`**  
   رسالة pytest: `subprocess.CalledProcessError: Command '['/opt/hostedtoolcache/Python/3.11.17/x64/bin/python', '/tmp/pytest-of-runner/pytest-0/test_parallel_fingerprints_mat0/round2_hashseed_probe.py']' returned non-zero exit status 1.`  
   تشخيص منفصل لنفس المسار، على المصدر نفسه ومن دون تعديل الاختبار، أكد `PYTHONPATH=None` وخرج الابن: `ModuleNotFoundError: No module named 'monte_carlo'` عند السطر `import monte_carlo` داخل السكربت المؤقت في `/tmp`. إذن فشل العملية حصل قبل حساب البصمات؛ لا يصلح دليلاً على اختلاف RNG أو على فشل مقارنة البصمات.

## 3. فصل حالة pytest عن سجل القبول الرسمي

سجل المستودع الحالي `docs/ACCEPTANCE_PORT.md` ما زال يذكر `127/159/160/161 = DEFERRED`، والاختبار `158 = ADJUDICATION`، وبوابة فعالة `162`. هذه حالات سجل/حوكمة قديم، وليست قيم PASS/FAIL التي أخرجها تشغيل pytest.

المرجع 2.2 الحاكم في 16.0 و16.17 يطلب **170 اختباراً فريداً** (186 صفاً: 170 فريداً + 15 ALIAS + 1 DOC) ويتضمن الاختبارات 180–186. أما `tests/test_acceptance_16_v2.py` على الرأس المفحوص فيحتوي 163 تعريف اختبار مرقماً، وأعلى رقم تعريف فيه 163؛ ولم يُعثر على تعريفات 180–186 في شجرة `tests/`. هذه فجوة توثيق/اختبارات بين الرأس والمرجع، لا يُحسم علاجها بتغيير أرقام سجل القبول القديم.

## 4. تصنيف الإخفاقات بحسب طلب U1 (من دون تعديل كود/اختبارات)

| الفئة | الاختبارات | الحكم والأثر |
|---|---|---|
| أ — يُعالج بمواءمة v2.0 | 127، 159، 160، 161 | اعتماد تجهيز الـfixtures/المخرجات قبل تشغيل اختبارات Stage 5 ومسارات الملفات ضمن تعديل ج.1 رقم 26، مع مراجعة تحديثات سجل الاختبارات في رقم 21. حالات هذه الاختبارات تبقى **DEFERRED/MISSING_EVIDENCE** في التشغيل الخام الحالي؛ لم يُعلن نجاحها ولم تُنشأ ملفات نتائج داخل `results/`. |
| ب — خلل كود حقيقي مثبت من هذا الإخفاق | لا شيء مثبت | الإخفاقات الأربعة الأولى بسبب مدخلات غائبة، وليست نتيجة حساب محرك. |
| ج — خلل في إعداد الاختبار/التوقع | `test_parallel_fingerprints_match_across_python_hash_seeds` (غير مرقم في سجل القبول) | سكربت الاختبار المؤقت يُشغّل من `/tmp` دون `PYTHONPATH` أو إضافة جذر المستودع لمسار الاستيراد؛ يفشل قبل تشغيل المحرك. |
| د — غموض قاعدة أعمال | لا شيء مستنتج من رسائل الإخفاق | لا تسند رسائل الاختبارات الخمس غموضاً بين بندين تجاريين. لا يُختلق `UNDEFINED_BUSINESS_RULE` بلا تعارض موثق. |

**قيد مهم:** هذا تصنيف سببي للمخرج الخام فقط. لا ينفي الفروق المصدرية الموثقة في `SPEC_DIFF_v1_to_v2.md`، ولا يعفي من إصلاح الكود في مرحلة لاحقة؛ ولم يُعدّل أي اختبار لإجبار PASS.

## 5. العناصر المفتوحة للمرحلة التالية

- مواءمة سجل الاختبارات في المستودع مع 16.0/16.17، وبناء/تثبيت تعريفات الاختبارات 180–186 كما يطلب المرجع.
- حسم عقد مخرجات/مسارات Stage 5 التي تعتمد عليها الاختبارات 127 و159–161، ثم تشغيل مسار fixture-first منفصل؛ لم يُنفَّذ هذا المسار ضمن خط الأساس الخام U1.
- إصلاح إعداد تشغيل subprocess في اختبار تطابق البصمات بحيث يستطيع استيراد وحدة المشروع، من دون تغيير توقعات حسابية أو تخفيف تغطية الاختبارات.

