# CP-P5 — جرد تشخيص pytest وfixtures وsubprocess

**التاريخ:** 2026-10-18 (Asia/Aden)  
**النمط:** جرد قراءة فقط، CP واحدة  
**الحكم:** أربع حالات `WORKFLOW_DEFECT / FAIL` في تشغيل تشخيصي مرشح بسبب fixtures غير مُنشأة؛ حالة subprocess خامسة `WORKFLOW_DEFECT / PENDING` لأن السبب الداخلي لم يُثبت. لم يُشغّل pytest في هذه الـCP.

## 1. ما تغيّر وحدود التنفيذ

لم يتغير أي ملف في المستودع في هذه الـCP، ولم يتم تشغيل pytest أو CLI أو محاكاة أو Trial أو Checkpoint أو Monte Carlo، ولم تُنشأ Run/Job/Artifact جديدة. نُزّل Artifact تاريخي قائم وفُحص محتواه. في محاولة التسجيل الأولى، أداة الكتابة رفضت العملية قبل أن تُرجع نتيجة Commit؛ لذلك لم يكن قد حدث تحديث GitHub وقت إعداد التقرير المحلي. سُجّل هذا التسلسل الزمني كما وقع ولا يعني أن تلك المحاولة نجحت.

## 2. خط الأساس والهوية

- المرجع المحلي `المرجع_النهائي_الموحد_المعتمد.md`: SHA-256 `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`، الحجم `271,496` بايت.
- `main` HEAD وقت الفحص: `647c19826b90d8224ce73ef9b90c306a45e03fb0`.
- `main/state.json` blob: `2178260bb18efeb81437486f13b6d10cf5e85936`; `state.sha=0b083fa472d7a11089a15137cfad16d87785689a`; دلالته `parent_state_commit_pointer`; `source_sha=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`.
- فرع الاستمرارية قبل محاولة التسجيل: `tmp/cp-session-continuity-20261017`، HEAD `4343209847ab2e5ab90d93be9d4c257044099200`. PR #46 مفتوح Draft وغير مدمج عند آخر قراءة قبل محاولة الكتابة؛ base `main` على `647c19826b90d8224ce73ef9b90c306a45e03fb0`.
- شجرة `main`: 223 مسارًا، 33 ملف `tests/test_*.py`، إضافة إلى helper scripts؛ لا يوجد `tests/conftest.py` أو `pytest.ini` أو `pyproject.toml` أو `tox.ini` أو `setup.cfg`، ولا يوجد مجلد `results_stage5/` متعقّب في Git. شجرة المرشح عند SHA الاختبار `a1e7e4a3223218d732fa438ae98edc0ef2408229`: 239 مسارًا، ولا يوجد فيها `results_stage5/` متعقّب.

## 3. تشغيل pytest التاريخي وArtifact

- Run `38656654259`: `Final candidate full pytest (temporary)`, النتيجة `failure`, التاريخ `2026-10-14`, الفرع `tmp/cp-final-candidate-20261015`, **tested SHA** `a1e7e4a3223218d732fa438ae98edc0ef2408229` (ليس `main` ولا رأس فرع المرشح الحالي).
- Job `116167906987`، والملخص الحرفي من سجل الاختبار: `5 failed, 416 passed, 1 skipped, 1 warning in 236.26s (0:03:56)`، `pytest_exit_code=1`.
- Workflow المستخدم في ذلك التشغيل: `.github/workflows/tmp-cp-final-candidate-verify.yml` عند tested SHA، blob `263ff934f68d2934b68cb0e6d247c8a2c64c059b`، الحجم 1,783 بايت. يقوم بـ `python -m pytest -q tests` مباشرة بعد تثبيت الاعتماديات، دون إنشاء `results_stage5/` أولًا ودون تحديد `PYTHONPATH: .`.
- Artifact موجود سابقًا: [Run 38656654259](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/38656654259)، [Artifact API 11936808738](https://api.github.com/repos/yasmin977209-ux/motorcycle-simulation/actions/artifacts/11936808738/zip)، الاسم `final-candidate-pytest-evidence`، الحجم 4,168 بايت، غير منتهي الصلاحية.
- بصمة ZIP: SHA-256 `3f601d264c239fa30a2a54a1fd49036132567ca01e87838ca612910eb80c65d4`.
- `pytest.log`: 19,841 بايت؛ SHA-256 `88d93c479cad254d26835e730a7ebc8982cf73557c1339dc39f9f803f5706455`.
- `pytest-identity.txt`: 190 بايت؛ SHA-256 `e375687a6916248ffeb79cf3c51d350d2b38f0bddac03efcf1c801a52de71cd2`؛ يحتوي على `tested_head_sha=a1e7e4a3223218d732fa438ae98edc0ef2408229`، `source_sha=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`، `master_seed=20270101`، `9886cc963ee7aa5b2b244fcec0ada44c0b200852`، و`pytest_exit_code=1`.

## 4. R4 — الأدلة والتصنيف

الملف الحاكم الموجود على `main`: `docs/stage9c/R4_export_numeric_precision.md`, blob `4ee5e71752fde39e3e09060a348ca5f020908170`. قسم R4 فيه يحدد أن التشغيل الخام الشامل دون fixtures لا يمثل مسار قبول Stage 4/Stage 5. الـWorkflow المعتمد Stage 4 (`.github/workflows/stage4-acceptance-port.yml`, blob `120366c01a7b7624d4dd1d8ff81e75a94c337e69`) يبني fixtures مؤقتة داخل `results_stage5/`، والـWorkflow المعتمد Stage 5 (`.github/workflows/stage5-main-postround2-validation.yml`, blob `abe1f8afdb6fc13a1a44e4811f25c44f70099db8`) يستخدم ترتيبًا يبدأ ببناء تلك fixtures قبل جرد الاختبارات المقبول.

### A. أربع إخفاقات لغياب fixtures

النصوص الفعلية من Artifact:

1. `tests/test_acceptance_16_v2.py::test_127_تطابق_التسلسلي_والمتوازي` — `FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/motorcycle-simulation/motorcycle-simulation/results_stage5/worker_equivalence_manifest.json'`.
2. `tests/test_acceptance_16_v2.py::test_159_اختيار_التكرار_التمثيلي_حسب_Final_Net_Project_Equity_فقط` — `FileNotFoundError: /home/runner/work/motorcycle-simulation/motorcycle-simulation/results_stage5/trials_summary.parquet`.
3. `tests/test_acceptance_16_v2.py::test_160_التكرارات_التوضيحية_الاربعة_تنتج_فعليا` — `FileNotFoundError: /home/runner/work/motorcycle-simulation/motorcycle-simulation/results_stage5/trials_summary.parquet`.
4. `tests/test_acceptance_16_v2.py::test_161_DAILY_DISTRIBUTION_لكل_يوم_تقويمي_بلا_فجوات` — `FileNotFoundError: /home/runner/work/motorcycle-simulation/motorcycle-simulation/results_stage5/daily_distribution.parquet`.

**التصنيف:** `WORKFLOW_DEFECT / FAIL` لتلك الدعوة التشخيصية الخام فقط. السبب مثبت: الاختبارات تقرأ ملفات مولدة مؤقتًا، بينما Workflow المرشح شغّل pytest مباشرة ولم ينفّذ خطوة بناء fixtures التي ينص عليها مسار Stage 4/Stage 5 المقبول. الأثر هو فشل أربعة اختبارات بسبب ملفات مفقودة، وليس دليلًا على أن مصدر الاختبار في `main` معيب. المعالجة المسموحة مستقبلًا: استخدام المسار المعتمد fixture-first وبترتيبه؛ لم يُعدّل شيء هنا. ما يمنع الإغلاق: لا يجوز استبدال دليل القبول الرسمي بتشغيل خام غير مهيأ.

### B. إخفاق subprocess الخامس

النص الفعلي:

`subprocess.CalledProcessError: Command '['/opt/hostedtoolcache/Python/3.11.17/x64/bin/python', '/tmp/pytest-of-runner/pytest-0/test_parallel_fingerprints_mat0/round2_hashseed_probe.py']' returned non-zero exit status 1.`

في `tests/test_monte_carlo_round2.py`، الدالة `_run_hashseed` تستخدم `subprocess.run([sys.executable, str(script_path)], env=env, text=True, capture_output=True, check=True)`، ولا تضبط `cwd` أو تضيف مسار المستودع إلى `PYTHONPATH`؛ والسكريبت المؤقت يستورد `monte_carlo`. في المقابل، مسار Stage 5 المقبول يحدد `PYTHONPATH: .`. لكن Artifact لا يعرض `stderr` أو `stdout` للعملية الفرعية، ولذلك لا يمكن إثبات أن غياب مسار الاستيراد هو السبب الفعلي.

**التصنيف:** `WORKFLOW_DEFECT / PENDING` من جهة مسار البيئة؛ سبب فشل العملية الداخلية غير محسوم. العيب المحتمل في path/environment اشتباه مدعوم بمصدر الكود لكنه ليس سببًا مثبتًا للإخفاق المسجل. الإغلاق يتطلب stderr/stdout الفعلي للعملية الفرعية أو تشخيصًا محددًا مخولًا. لم يُنفّذ إعادة تشغيل أو تعديل للاختبار/Workflow في هذه الـCP.

## 5. فصل الحالة عن النتائج التاريخية

- هذه المراجعة لم تشغّل pytest؛ التشغيل المذكور تاريخي ومختبر على SHA مرشح فقط.
- الحالة الكاملة لـpytest على `main` الحالي **PENDING / لم تُختبر في هذه الـCP**.
- Gate A ما زالت BLOCKED بسبب `GATEA_PROVIDER_MISSING`؛ متطلبات المتوسطات المالية في Gate B ما زالت `K_SPEC / BLOCKED`؛ §2.5/IUT ما زال PENDING من ناحية التنفيذ الإنتاجي؛ `SCENARIO_STABLE` والتسليم النهائي وRelease تبقى BLOCKED دون تغيير.
- لا تُنسب نتيجة أي فرع مرشح إلى `main` ولا يثبت نجاح Workflow وحده محتوى Artifact أو قبول أي بوابة.

## 6. الخطوة التالية المسموحة

بعد حفظ هذا التقرير، الـCP التالية هي **جرد P8 للـCLI والبيئة للقراءة فقط**؛ ثم CP منفصلة لجرد P9 للـWorkflows للقراءة فقط. لا يُشغّل pytest أو CLI ولا تُعدّل الاختبارات أو Workflows ما لم تُستوفَ مراجعة R4 والموافقة الصريحة المنفصلة المطلوبة.
