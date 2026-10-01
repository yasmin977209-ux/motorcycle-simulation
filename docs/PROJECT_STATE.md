# PROJECT STATE

**تاريخ الحالة:** 2026-10-01  
**المستودع:** `yasmin977209-ux/motorcycle-simulation`  
**الفرع الحاكم:** `main`  
**آخر SHA على main:** `63c65f7f4fe6121a4d8a797658a1d06ea6176342`

## 1. حالة البناء

### المرحلة 1 — constants.py
الحالة: **ACCEPTED**

- ملف الثوابت أُعيد بناؤه من المرجع، مع تطبيق R7 للثوابت المشتقة.
- commit إعادة بناء الثوابت الأخير: `8b5054ddb6a7d6aa91634af6bad7eb9c74929041`.
- أحدث تحقق GitHub ظاهر في هذا السجل: `stage1-verification` Run **65**، GitHub run id **36911530602**، النتيجة **success**، وعلى SHA `63c65f7f4fe6121a4d8a797658a1d06ea6176342`.
- Run سابق موثق في سجل README: Run **4** على commit `433a944974a1646e83f9be3122bbb45e5aeffa89` بنجاح.

### المرحلة 2 — entities.py وstate_machine.py
الحالة: **ACCEPTED**

- commit المرحلة 2 الحاكم: `d19ca51b8337a475ddd28cce6d661277930f3e48`.
- أحدث تحقق GitHub ظاهر في هذا السجل: `stage2-verification` Run **55**، GitHub run id **36911530116**، النتيجة **success**، وعلى SHA `63c65f7f4fe6121a4d8a797658a1d06ea6176342`.
- تدقيق واجهات R4/R6 موجود في `docs/stage2_interface_audit.md`.

### توضيح مهم حول commit ملف التدقيق
الـcommit الذي **أضاف فعلياً** `docs/stage2_interface_audit.md` هو:

`63c65f7f4fe6121a4d8a797658a1d06ea6176342`

أما `67e9168c5786f5207408252ef1f5c45f8a467466` فهو **SHA للـblob/محتوى الملف** كما أعاده GitHub عند قراءة الملف، وليس commit. لذلك المرجع الصحيح لإضافة الملف هو `63c65f7f…`.

### المرحلة 3أ
الحالة: **NOT STARTED / NOT APPROVED**

وجود ملفات تجريبية مرتبطة بـ3أ في `main` لا يُعد بدءاً أو قبولاً للمرحلة. هذه الملفات تدخل في الجرد بوصفها `STALE_PENDING_REBUILD` إلى أن يعاد بناؤها من الصفر وفق المرجع وقرارات المشروع.

---

## 2. قواعد R1–R7

1. **R1 — WORKFLOW_DEFECT:** أي `ModuleNotFoundError` أو فشل استيراد هو `WORKFLOW_DEFECT` وليس `DEFERRED`. التأجيل مسموح فقط عند غياب مدخل بيانات.
2. **R2 — لا انتقال دون إذن:** لا انتقال إلى أي مرحلة أو مرحلة فرعية دون إذن صريح.
3. **R3 — عدم تعديل الاختبارات لتناسب الكود:** لا يُعدّل الاختبار لتطابق التنفيذ؛ يُحسم هل الخطأ في الكود أم في فهم المرجع.
4. **R4 — تدقيق الواجهات قبل كتابة كود جديد:** استخراج أسماء/توقيعات/حقول اختبارات main، ثم استخراج الأسماء نفسها من `stage3b-preserved` كدليل واجهة فقط، ثم مقارنتها بالمرجع وتصنيفها مطابق/انحراف معتمد/مخالفة.
5. **R5 — فشل اسم/توقيع في main:** أي فشل في اختبار main بسبب غياب اسم أو توقيع هو `WORKFLOW_DEFECT` وليس `K_TEST`.
6. **R6 — تصنيف الثوابت:** نوع-1 قيمة أولية، نوع-2 مشتق، نوع-3 مجموعة/قاموس يُعرّف مرة واحدة، نوع-4 اسم/مفتاح تشغيلي مطابق حرفياً لاسم الحقل في `TrialResult` أو Excel.
7. **R7 — المشتقات سطرياً:** كل ثابت من نوع-2 يُحسب تعبيرياً في سطر تعريفه نفسه، ولا يُستخرج من دوال في ملفات أخرى.

---

## 3. القرارات المحسومة

- **M9** هي مرحلة اشتقاق الحالة، و**M10** محجوزة. كل إحالة إلى M10 في جدول 4.3 تُقرأ M9.
- `DAILY_DISTRIBUTION` لكل **يوم تقويمي** ابتداءً من `2027-01-01`.
- **P1** = `Partner1_Final_Entitlement`.
- **P2** = `Partner2_Final_Entitlement`.
- التخزين: **Parquet** للنتائج التفصيلية، و**JSONL مضغوط** لشرائح الاستئناف، ولا يُستخدم pickle.
- بوابة المرجع (أ) تقارن نقطتي فحص متتاليتين: `n` و`n+50`.
- مؤشر الاستقرار الأول: `Final_Net_Project_Equity`.
- احتمال الخسارة: `Probability_of_Accounting_Loss`.
- في 3ب: Final equity بعد **M17** وليس M15، مع سجلات Roll-forward الأربعة، وتنفيذ M1–M17 بالترتيب الإلزامي.

### التكرارات الإحصائية المعتمدة
- `C100`: تكرار إحصائي واحد فقط.
- `C085/C070/C050/C030`: 300 تكرار لكل توليفة.
- التصعيد: +50 في كل مرة: 350 ثم 400 ثم 450 ... بلا سقف مسبق.
- نقاط الفحص: 300 و350 و400 ... فقط.
- أقرب توقف ممكن: 400.
- لا توقف قبل إتمام الزيادة الجارية.
- لغير C100 يلزم تحقق بوابتَي الاستقرار معاً عبر ثلاث نقاط فحص متتالية.
- بوابة CI تستخدم توزيع t ونصف عرض 95% أقل من 1% من |المتوسط|، مع حماية المتوسط القريب من الصفر.
- `C100` لا يخضع لبوابة CI عند `n=1`، مع ضرورة إثبات صفرية التباين فعلياً بإعادة التشغيل بقيم trial_id وبذور مختلفة والمقارنة الحرفية.

### قرارات المستخدم المعتمدة الآن

**(أ) اختبارات الـ163 وعقد الواجهة**
- لا تُدخل اختبارات الـ163 دفعة واحدة.
- تُدخل **كل مجموعة عند اكتمال طبقتها** فقط.
- لا تؤجل إدخالها كلها إلى المرحلة 9.
- `run_day` هو الواجهة العامة للمنسق اليومي.
- لا تُنشأ دوال `_m1` … `_m16` إلا إذا فرضها المرجع صراحة.
- التسلسل M1–M17 يبقى عقد تنفيذ داخلي ويُتحقق منه فعلياً.

**(ب) Workflows**
- Workflow واحد لكل مرحلة هو التصميم المعتمد.
- كل Workflow يعرض جدولاً بحالات **PASS / FAIL / DEFERRED / ADJUDICATION**.
- workflows القديمة ذات trigger على push إلى main ستُعطّل بتحويلها إلى `workflow_dispatch` فقط، مع إبقاء `stage1-verification` و`stage2-verification` على push.

**(ج) الاختبار 158**
- الحالة المعتمدة: **ADJUDICATION_REQUIRED**.
- لا يُعدّل لإجباره على المرور.
- لا يُرفع المرجع إلى المستودع لكسر قاعدة التخزين.

---

## 4. الاختبارات الـ163 والحالة الحالية

**الاختبارات الـ163 غير موجودة في main، وهي داخل الأرشيف فقط.**

الموجود في main حالياً لا يتضمن `tests/test_acceptance_16_full.py` ولا `validation.py`.  
وتوجد في الأرشيف شرائح مصدر مضغوطة `stage7_source/source.b64.*`، بينما `state.json` التاريخي يسجل تشغيلات قبول سابقة منفصلة عن حالة main الحالية.

البنود المؤجلة/المعلقة المعتمدة:
- **127: DEFERRED** — مدخل المرحلة 5؛ مع adjudication لاحق لمسألة artifact.
- **158: ADJUDICATION_REQUIRED**.
- **159: DEFERRED** — مدخل المرحلة 5.
- **160: DEFERRED** — مدخل المرحلة 5.
- **161: DEFERRED** — مدخل المرحلة 5؛ مع adjudication لمسألة صيغة التخزين.
- بوابة الـ163 النهائية: المرحلة 9، لكن إدخال مجموعات الاختبار يتم طبقيّاً كما اعتمد الآن، وليس دفعة واحدة.

---

## 5. الفروع المحفوظة

### archive-preserved
فرع محفوظ للتاريخ التشخيصي للحزم السابقة وشرائح المصدر والأدلة القديمة. لا يُستخدم كمصدر نسخ حرفي للكود الجديد.

### stage3b-preserved
فرع محفوظ كدليل تشخيصي للواجهات والأسماء وبنية التنفيذ التاريخية، وخاصة `run_day` وتسلسل M1–M17. لا يُنسخ الكود منه حرفياً.

---

## 6. جرد main — ملفات تحتاج إعادة بناء

**القاعدة:** جميع الملفات التالية مصنفة `STALE_PENDING_REBUILD` لهذا المسار، حتى لو كانت قابلة للاستيراد حالياً، لأنها تنتمي إلى الجولة السابقة ولا تُعد أساس التنفيذ الجديد. فحص الاستيرادات المقصود هنا هو مقارنة الأسماء المستوردة من `constants.py` و`entities.py` و`state_machine.py` الحالية.

| الملف | الحجم (بايت) | أسماء مفقودة من constants/entities/state_machine | التصنيف |
|---|---:|---|---|
| `accounting.py` | 5211 | لا يوجد | STALE_PENDING_REBUILD |
| `closure.py` | 3779 | لا يوجد | STALE_PENDING_REBUILD |
| `collection.py` | 3133 | لا يوجد | STALE_PENDING_REBUILD |
| `daily_engine.py` | 18582 | لا يوجد | STALE_PENDING_REBUILD |
| `dateutils.py` | 5493 | لا يوجد | STALE_PENDING_REBUILD |
| `depreciation.py` | 3344 | لا يوجد | STALE_PENDING_REBUILD |
| `friday.py` | 2196 | لا يوجد | STALE_PENDING_REBUILD |
| `guarantee.py` | 3641 | لا يوجد | STALE_PENDING_REBUILD |
| `partner_equity.py` | 1449 | لا يوجد | STALE_PENDING_REBUILD |
| `rng.py` | 2550 | لا يوجد | STALE_PENDING_REBUILD |
| `settlement.py` | 4981 | لا يوجد | STALE_PENDING_REBUILD |

### الاختبارات والأدوات الباقية

| الملف | الحجم (بايت) | أسماء مفقودة من constants/entities/state_machine | التصنيف |
|---|---:|---|---|
| `tests/test_c100_determinism.py` | 1649 | لا يوجد | STALE_PENDING_REBUILD |
| `tests/test_stage1_rebuild.py` | 1673 | لا يوجد؛ الاستيرادات النجمية لا تمثل اسماً مفقوداً بحد ذاتها | STALE_PENDING_REBUILD |
| `tests/test_stage3_path_integration.py` | 7474 | لا يوجد | STALE_PENDING_REBUILD |
| `tests/test_stage3a.py` | 7979 | لا يوجد | STALE_PENDING_REBUILD |
| `tests/test_stage3b.py` | 2269 | لا يوجد | STALE_PENDING_REBUILD |
| `tests/run_pause_resume_gate.py` | 2029 | لا يوجد | STALE_PENDING_REBUILD |

### ملفات مطلوبة في الجرد لكنها غير موجودة في main

| الملف | الحالة | التصنيف |
|---|---|---|
| `monte_carlo.py` | غير موجود | STALE_PENDING_REBUILD |
| `run_batch.py` | غير موجود | STALE_PENDING_REBUILD |
| `validation.py` | غير موجود | STALE_PENDING_REBUILD |
| `tests/test_acceptance_16_full.py` | غير موجود | STALE_PENDING_REBUILD |
| `tests/test_stage3.py` | غير موجود | STALE_PENDING_REBUILD |

### ملفات الأساس المقبولة، وليست ضمن stale inventory
- `constants.py` — المرحلة 1 مقبولة.
- `entities.py` — المرحلة 2 مقبولة.
- `state_machine.py` — المرحلة 2 مقبولة.
- `tests/test_stage1.py` — اختبارات المرحلة 1 المعتمدة.
- `tests/test_stage2.py` — اختبارات المرحلة 2 المعتمدة.

---

## 7. Workflows الموجودة في main عند هذه الحالة

الملفات الموجودة تحت `.github/workflows`:
- `stage1-rebuild.yml`
- `stage1-verification.yml`
- `stage10-benchmark.yml`
- `stage2-verification.yml`
- `stage3-c030-timing.yml`
- `stage3-c100-determinism.yml`
- `stage3-path-integration.yml`
- `stage3a-verification.yml`
- `stage3b-verification.yml`
- `stage7-gates.yml`
- `stage9-simulation.yml`

قبل تنفيذ قرار تعطيل triggers القديمة، الملفات ذات push إلى main تشمل workflows القديمة المتعددة، بينما `stage1-verification` و`stage2-verification` هما الاستثناءان اللذان يبقيان على push وفق القرار المعتمد.

---

## 8. قيود التنفيذ الحاكمة

- التكلفة صفر؛ لا خوادم ولا خدمات مدفوعة دون موافقة صريحة.
- لا تُرفع ملفات المرجع أو التقارير أو Excel النهائية إلى المستودع.
- المستودع يحتفظ بالكود و`state.json` وشرائح النتائج المضغوطة اللازمة للاستئناف فقط.
- يجب وضع pytest في `requirements.txt`.
- لا تُعدّل ملفات workflows من داخل workflow نفسه؛ التعديل الحالي يتم مباشرة عبر اتصال GitHub المرتبط.
- قبل أي تشغيل طويل: دفعة صغيرة فعلية على GitHub وقياس الزمن/الأنوية/الحد الزمني/الحجم وتقدير المدة.
- لا تُكتب نتائج اختبار أو أرقام PASS ثابتة يدوياً؛ الحالات التشغيلية يجب أن تأتي من التنفيذ الفعلي.
- أي تعديل يمس منطق التنفيذ يستلزم إعادة اختبارات القبول والمسارات المرجعية ذات الصلة.
- لا يبدأ تشغيل المحاكاة الرئيسية أو مونت كارلو هنا.

## 9. الوضع عند آخر تحديث

**آخر SHA:** `63c65f7f4fe6121a4d8a797658a1d06ea6176342`  
**Stage 1:** ACCEPTED  
**Stage 2:** ACCEPTED  
**Stage 3A:** NOT STARTED / NOT APPROVED  
**آخر stage1-verification:** Run 65 — success  
**آخر stage2-verification:** Run 55 — success  
**الاختبارات 163 في main:** غير موجودة  
**القرار 158:** ADJUDICATION_REQUIRED  
