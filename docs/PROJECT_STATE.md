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
- أحدث تحقق GitHub: `stage1-verification` Run **146**، GitHub run id **37060161854**، النتيجة **success**، وعلى SHA التشغيلي `de72533819ba4b8e09e96b3af54999dd3f3e4225`.
- Run سابق موثق في سجل README: Run **4** على commit `433a944974a1646e83f9be3122bbb45e5aeffa89` بنجاح.

### المرحلة 2 — entities.py وstate_machine.py
الحالة: **ACCEPTED**

- commit المرحلة 2 الحاكم: `d19ca51b8337a475ddd28cce6d661277930f3e48`.
- أحدث تحقق GitHub: `stage2-verification` Run **136**، GitHub run id **37060161892**، النتيجة **success**، وعلى SHA التشغيلي `de72533819ba4b8e09e96b3af54999dd3f3e4225`.
- تدقيق واجهات R4/R6 موجود في `docs/stage2_interface_audit.md`.

### توضيح مهم حول commit ملف التدقيق
الـcommit الذي **أضاف فعلياً** `docs/stage2_interface_audit.md` هو:

`63c65f7f4fe6121a4d8a797658a1d06ea6176342`

أما `67e9168c5786f5207408252ef1f5c45f8a467466` فهو **SHA للـblob/محتوى الملف** كما أعاده GitHub عند قراءة الملف، وليس commit. لذلك المرجع الصحيح لإضافة الملف هو `63c65f7f…`.

### المرحلة 3ب — مسار 4.4 (PATH_1)
الحالة: **PASS** للاختبار المضاف، مع بقاء المرحلة الفرعية نفسها ضمن نطاق التحقق الحالي.

- اختبار جديد: `tests/test_stage3b_path1.py`.
- commit الاختبار: `eb97d02b14f950d38bafe9cceedc16e868a17b83`.
- تعديل Workflow المعتمد لإدخال PATH_1: `de72533819ba4b8e09e96b3af54999dd3f3e4225`.
- `stage3b-verification` Run **94**، GitHub run id **37060161894**.
- نتيجة pytest الحرفية لمسار 1: `1 passed in 0.20s`.
- جدول Workflow أظهر: `Chapter 4.4 path 1 | PASS | 1 passed in 0.20s`.
- المجموعات الأخرى في Run 94 بقيت PASS: Chapter 10 = `2 passed in 0.02s`، Chapter 11 = `3 passed in 0.01s`، Chapter 12 M1-M17 = `3 passed in 0.02s`، Chapter 13 = `6 passed in 0.02s`، paths 2-6 = `5 passed in 0.03s`، no-time-cap = `1 passed in 1.49s`، roll-forward + C100 = `1 passed in 35.03s`.
- الشرط الحسابي المتعلق بالـroll-forward لم يفشل مستقلاً؛ الاختبار والتدفق الخاصان بالمسار 1 نجحا.
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

**SHA التشغيلي الذي اختُبرت عليه التغييرات:** `de72533819ba4b8e09e96b3af54999dd3f3e4225`  
**آخر SHA على main قبل تحديث ملف الحالة:** `6a9648c7bd8a51472dbc889824f9fd3e4bbe3387`  
**stage1-verification:** Run **146** — success — GitHub run id `37060161854`  
**stage2-verification:** Run **136** — success — GitHub run id `37060161892`  
**stage3a-verification:** Run **115** — success — GitHub run id `37060162170`  
**stage3b-verification:** Run **94** — success — GitHub run id `37060161894`  
**Stage 4 Acceptance Port:** Run **43** — success — GitHub run id `37060161884`  
**v2:** `158 passed / 0 failed / 4 deferred / 1 adjudication`، وملف `results/v2_output.txt` سجل `158 passed, 5 skipped in 8.77s`.  
**اختبارات 127/159/160/161:** DEFERRED.  
**اختبار 158:** ADJUDICATION_REQUIRED.  
**Stage 3A:** NOT STARTED / NOT APPROVED.  
**Stage 5:** لم يبدأ.

### تصحيح M8 وحالته
- الإصلاح المعتمد لصيغة التحصيل في M8: commit `e174ac69e5b5f28733671ebebead2ee05378b17b`.
- أصلح الصيغة المخالفة للمرجع في البند 6.2 باستخدام مسار التحصيل/AR الصحيح، دون تغيير اختبارات القبول لتناسب الكود.
- الدليل المحفوظ على فرع `tmp/verify-m8` هو commit `2e389337dd3848e93b6a83a0d88edb98e0e0ca2c`.

### قرار event_log
- بسبب حجم `event_log` الخام الكبير (نحو 95 MB لكل repetition في القياسات المعتمدة)، يُحفظ الخام كاملاً **فقط لأربع repetitions تمثيلية** لأغراض التدقيق.
- بقية repetitions لا تُحفظ لها نسخ event_log خام؛ يُحفظ لها فقط شرائح `DAILY_DISTRIBUTION` اللازمة للاستئناف والتحليل.
- هذا القرار تشغيلي موثق ولا يغيّر منطق المحاكاة أو حقول `TrialResult`.
## 10. حسم K_SPEC في entities.py بقرارات R4 المحدثة

تم إغلاق بنود K_SPEC الثلاثة وفق قرارات المستخدم:

1. **`pending_writeoff_today`**
   - حقل `bool` في `Bike`.
   - القيمة الافتراضية: `False`.
   - قرار التثبيت الأصلي: `a13bb24b80678548bbc04a1ae8f6ddcd17a488fc`.

2. **`active_settlement_receivable`**
   - لا يوجد كائن مستقل جديد.
   - الحقل المعتمد: `active_settlement_receivable_id` في `Bike`.
   - قرار التثبيت الأصلي: `a13bb24b80678548bbc04a1ae8f6ddcd17a488fc`.

3. **`current_contract`**
   - لا يوجد حقل كائني جديد في `Bike`.
   - الاشتقاق عبر `current_contract_id` ثم `Project.contracts[contract_id]`.
   - `Project.contracts` أصبح الآن **`dict[str, Contract]` عاديًا**.
   - أُزيل `ContractIndex` نهائيًا؛ لا يوجد `__iter__` مخصص ولا `append`.
   - أضيفت في `entities.py`:
     - `add_contract(project, contract)` — ترفع `ValueError` عند تكرار `contract_id`.
     - `contract_of(project, bike)` — تعيد العقد بواسطة المفتاح أو `None` عند عدم وجوده.
   - تنفيذ القرار المحدث: `58e321e1f6153df3307fe95c184525939d0612a0`.

**حالة K_SPEC الثلاثة: CLOSED / RESOLVED.**

### اختبار الكيان والفهرس
أُنشئ الملف الجديد `tests/test_stage2_entities_additions.py` دون تعديل أي اختبار قائم.

بعد التحديث:
- الاختبار الجديد يتأكد من القيم الافتراضية، source-of-truth، وفهرس dict كبير، وسلوك التكرار عبر `add_contract`، و`contract_of`، وبنية سجلات Roll-forward.
- تشغيل Stage 2: Run **84** — **success** — `19 passed in 0.26s`.

لا يوجد كسر في اختبارات Stage 1 أو Stage 2 القائمة أو انحدار Stage 3A بعد إزالة `ContractIndex`.

## 10.1 Roll-forward
- `cash_rollforward`
- `ar_rollforward`
- `asset_rollforward`
- `equity_rollforward`

سجل الأصول يفصل Gross وAccumulated، بينما Net مشتق وليس حقلاً مخزناً مستقلاً، وفق 10.6.

## 11. اعتماديات 3A المتعطلة بالتبعية حتى 3B

الملفات القديمة `daily_engine.py` و`accounting.py` و`closure.py` و`partner_equity.py` تبقى مصنفة **معطّلة بالتبعية حتى 3ب**، ولا تُعد جزءاً من تنفيذ 3أ المعزول.

التحقق النصي الفعلي من imports على `main` يثبت:

| الملف | imports المرتبطة بأبواب 5–9 | الحالة بعد إعادة كتابة 3A |
|---|---|---|
| `daily_engine.py` | `apply_ordinary_collection`، `apply_daily_depreciation`، `apply_ownership_writeoff`، `apply_friday_fee_and_oil`، `create_guarantee_claim`، `settle_guarantee_claim`، `apply_legacy_debt_collection`، `apply_settlement_rent` | الاستيرادات نفسها ليست مكسورة نصياً؛ التعطل التشغيلي بالتبعية من فجوة `entities.py` في 3B، وخاصة `pending_writeoff_today` |
| `accounting.py` | لا يستورد دوال أبواب 5–9 | لا يوجد import مكسور نصياً؛ يبقى معطلاً بالتبعية حتى 3B |
| `closure.py` | `create_guarantee_claim` | import صالح نصياً؛ يبقى معطلاً بالتبعية حتى 3B |
| `partner_equity.py` | لا يستورد دوال أبواب 5–9 | لا يوجد import مكسور نصياً؛ يبقى معطلاً بالتبعية حتى 3B |

**تصحيح للتقرير السابق:** لا يجوز وصف هذه الحالة بأنها مجموعة imports مكسورة. ما ثبت فعلياً هو أن `daily_engine.py` ينفذ استدعاءات أبواب 5–9، وأن مساره التشغيلي القديم ينكسر عند الوصول إلى حقل `pending_writeoff_today` غير الموجود في `Bike`. أما `accounting.py` و`partner_equity.py` فلا تحتويان أصلاً على imports لهذه الدوال، و`closure.py` importه للكفالة صالح نصياً.

## 12. بنود مؤجلة إلى منطق 3ب

تم حسم K_SPEC الخاصة بالكيانات أعلاه. تبقى البنود التالية مؤجلة إلى منطق 3ب:

- **Final equity:** يُطبق في 3ب وفق صيغة M15 المرجعية: `Cash + مجموع NBV للدراجات HELD_AS_ASSET`، ثم يؤكد M17 مساواتها مع `Total_Equity`. أي اختلاف يُعامل كخلل ويُبلّغ.
- **master_seed:** يُمرر في سلسلة اشتقاق الرميات باستخدام SHA-256.
- **execution_trace:** اختياري ويُفعّل في الاختبار فقط.

الحالة: **DEFERRED TO STAGE 3B**.
