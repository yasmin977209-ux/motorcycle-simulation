# PROJECT STATE

**تاريخ الحالة:** 2026-10-06  
**المستودع:** `yasmin977209-ux/motorcycle-simulation`  
**الفرع الحاكم:** `main`  
**تصنيف الوثيقة:** **CURRENT**  
**آخر SHA لتوثيق هذه الحالة:** ff3c8766f2e5252d8c2c5ab36378c0ef3702b48e  

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
الحالة: **PASS** — Run **115** — GitHub run id `37060162170`.

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
- **158: ADJUDICATION_REQUIRED**.
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
**v2:** `162 passed / 0 failed / 0 deferred / 1 adjudication`، وملف `results/v2_output.txt` سجل `162 passed, 1 skipped in 9.03s`.  
**اختبارات 127/159/160/161:** لا DEFERRED.  
**اختبار 158:** ADJUDICATION_REQUIRED.  
**Stage 3A:** PASS — Run `115` — GitHub run id `37060162170`.  
**Stage 5 Round 1:** PASS — Run `37062820926` — C100_G100 مطابق للقيم الذهبية.
**Stage 5 Round 2:** PASS — Run `37064457223` — التسلسلي/التوازي والبصمات الثلاث متطابقة، `all_match=true`.
**Stage 5 Round 3:** PASS للقياس الفعلي — Run `37068980072`.
**Round 4 المؤقت:** PASS — Run `37077181116` — SHA `c4aa99dcaf452e5a9d3923079437a12990943bc1`.
**Round 4 على main:** PASS — Run `37129605565` — commit `b40cd888fe1287085f9b67a5f3356c9695785ab7`.
**Round 5 على الفرع:** PASS — Run `37086194110` — SHA `825b7cd5024c2ec3e5ccda2e930552d4dcd98b40`.
**Round 5 على main:** PASS — Run `37129844454` — commit `a64bdc03c484f0979a29a4a1054eb33c9d6ee4d0`.
**main الحالي:** `25e0d677996bc3746ea7aadda5b99847a8c58271`.
**Stage 4 v2 على main:** Run `37129844454` — commit `a64bdc03c484f0979a29a4a1054eb33c9d6ee4d0` — `162/0/0/1`.
**fixtures المؤقتة لـ Stage 5:** `du -sb results_stage5 = 821261` بايت.

### تنويهات Stage 5 المعتمدة
- `6005/7005/8005` أعداد تكرارات، وليست أحجام bytes مؤكدة.
- أرقام Round 3 هي شرائح كل تكرار، وليست جدول `DAILY_DISTRIBUTION`.
- `C085` و`C050` لم تُقَسا بعد.
- التقدير نطاق، وليس قيمة واحدة.
- `du -sb` لا يُستعمل للتقدير الكلي.

### قياسات Round 3 الفعلية
- `C070_G100`: 300 تكرار، `1331.188912015s` إجمالي، `4.437296373383333s/تكرار`، 4 أنوية، Parquet `7233257` بايت، JSONL.gz `11379674` بايت، أطول تكرار `2214` يوماً، `active_trial_count_series_ok=true`.
- `C030_G000`: 300 تكرار، `272.3369119959998s` إجمالي، `0.9077897066533327s/تكرار`، 4 أنوية، Parquet `4899612` بايت، JSONL.gz `7256742` بايت، أطول تكرار `1655` يوماً، `active_trial_count_series_ok=true`.
- `per_g_level_totals=1201`، `all_25_total=6005`.
- الإسقاطات: `6005` عند البداية، `7005` بعد +50، `8005` بعد +100.

### قياس A/B لـ`on_day_end`
- بلا `on_day_end`: `4.496737711000009`، `4.634696636000001`، `4.575441477000027` ثانية؛ المتوسط `4.568958608333337`.
- مع `on_day_end`: `4.7545812699999885`، `4.661814155000002`، `4.698626410999992` ثانية؛ المتوسط `4.705007278333327`.
- الفرق بين المتوسطين: `0.13604866999999003` ثانية.
- القرار: لا تسريع في الجولات 2–5؛ قرار التسريع مؤجل إلى المرحلة 6.

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

الحالة: **PASS**.


---

## 13. Stage 7 F4 Completion

**الحالة:** **CURRENT / COMPLETED**

مرجع الإثبات الكامل: `docs/STAGE7_FINAL_EVIDENCE.md`.

- F4 Run: `37482745008`
- Branch: `tmp/wf-002f6-f4safe-20261006`
- Commit: `9fa357e83a07544d070eb717a945257ce9954d6f`
- Simulation jobs: **25/25 success**
- Restore evidence: **25/25** مع `COUNT>0`
- `derived == stored`: **25/25**
- Official fingerprint match: **25/25**
- C100 golden match: **true**
- State branches: **25/25 v2 unchanged**
- State integrity errors: **0**

الـofficial Stage 7 artifact set مصدره Run `37225915321`، وهو المرجع التشغيلي السابق للـ25 توليفة.

## 14. Stage 8 Closure

**الحالة:** **CLOSED**

- Smoke Run: `37234010912`
- Scenario: `C070_G100`
- Final N: **500**
- Smoke/closure evidence بقي ضمن نطاق Stage 8، ولم تُعاد التكرارات `1–450`.
- Stage 8 ليس منتج بيانات جديداً مستقلاً؛ دوره كان التحقق من الاستئناف/الاستقرار وإغلاق المرحلة.

## 15. Current Stage: Pre-Stage9

الحالة الحالية هي **Pre-Stage9**. لا يبدأ تنفيذ Stage 9 ضمن هذا التحديث.

Stage 9 مخصص للمراجعة المالية النهائية الشاملة وفق المرجع، بما في ذلك اختبارات Roll-forward الخمسة، توازن الميزانية بفارق صفر لكل التكرارات والتوليفات المطلوبة، وفحص Excel الناتج من خلايا الخطأ. المرجع يحدد ذلك في الباب 19، ولا يجيز إدخال سقف زمني في منطق المحرك.

### Known-safe workflow exceptions

- `stage3a-verification.yml`
- `stage3b-verification.yml`
- `stage5-main-postround2-validation.yml`

هذه الـworkflows لا تكتب إلى `main` وفق المراجعة الحالية؛ مراجعة الحوكمة الخاصة بالـpush triggers مؤجلة ولا تدخل في تعديل Phase A.
