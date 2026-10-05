# Stage 7 ↔ Stage 11 Resume Policy

## القرار المعتمد

القرار المعتمد هو **الخيار C**:

> **Stage 7 = التشغيل الرسمي، وStage 11 = استئناف اختياري.**

Stage 7 تشغّل التشغيل الرسمي لجميع السيناريوهات وفق العدد والسياسات
المعتمدة، وتنتج checkpoints رسمية قابلة للاستئناف.

Stage 11 لا تنشئ Dataset جديداً عند الاستئناف؛ بل تستهلك checkpoint
صالحاً من Stage 7 وتتابع من `next_trial_id`.

## تعريف Stage 7

Stage 7 هي **منتج البيانات الرسمي**.

لكل سيناريو تنتج Stage 7:

- `state.json`
- Parquet trial blocks
- artifact fingerprints
- `stability_history`

هذه المخرجات تمثل نقطة الاستئناف الرسمية للسيناريو، وليست مجرد
مخرجات تشخيصية.

## تعريف Stage 11

Stage 11 هي **مستهلك بيانات الاستئناف**.

عند الحاجة إلى متابعة تشغيل توقف قبل اكتماله، تقرأ Stage 11 checkpoint
الخاص بالسيناريو من Stage 7، تتحقق من هويته، ثم تستأنف من
`next_trial_id` دون إعادة تنفيذ التجارب المكتملة.

## عناصر الهوية الإلزامية للاستئناف

لا يجوز الاستئناف إلا عند تطابق العناصر التسعة التالية بالكامل:

1. `SOURCE_SHA`
2. `master_seed`
3. RNG policy
4. sampling policy
5. stability policy
6. trial-id policy
7. state schema
8. scenario
9. artifact fingerprint

أي اختلاف في عنصر واحد يعني أن البيانات تمثل **Dataset مختلفاً**.

## آلية عمل Stage 11

التسلسل الإلزامي هو:

1. قراءة `state.json` من فرع `stage7-state/<scenario>`.
2. قراءة هوية checkpoint.
3. التحقق من العناصر التسعة للهوية.
4. عند نجاح التحقق، قراءة `next_trial_id`.
5. استئناف التشغيل من `next_trial_id`.
6. عدم إعادة تنفيذ trials المكتملة.

مثال: إذا كان checkpoint يثبت أن
`completed_trials = N` وأن `next_trial_id = N + 1`، يبدأ الاستئناف
من `N + 1`.

## التنفيذ

التنفيذ الفعلي لسياسة Stage 7 ↔ Stage 11 يقع في:

- `scripts/stage7_state.py` — لإدارة state وcheckpoint وartifact identity.
- `.github/workflows/stage7-full-run.yml` — لقرار التوقف والاستئناف.
- `.github/workflows/stage11-resume.yml` (مستقبلي) — لاستهلاك
  checkpoint Stage 7.

هذه السياسة لا تغيّر أي منطق إنتاجي بنفسها؛ إنها تحدد العقد المعماري
الذي يجب أن يلتزم به التنفيذ.

## متى تُشغّل Stage 11؟

Stage 11 تُشغّل عند تحقق أحد الشرطين:

1. Stage 7 توقفت بحالة `final_status = "timeout"`، أي لم تستقر السيناريوهات
   ضمن الحد التشغيلي البالغ 45 دقيقة؛ أو
2. Stage 7 اكتملت بنجاح، لكن المالك يريد توسيع Dataset لاحقاً على نفس
   `SOURCE_SHA`.

Stage 11 **لا تُشغّل تلقائياً**.

تحتاج Stage 11 إلى إذن المستخدم المنفصل.

## الإحصاءات النهائية

Stage 11 تعيد حساب الإحصاءات النهائية من **كل** الـblocks المتاحة:

- P10
- P50
- P90
- Mean
- Std
- Min
- Max
- `Probability_of_Accounting_Loss`
- `final_fingerprint` للسلسلة الكاملة من `1..N`

لا تقرأ Stage 11 الإحصاءات المحفوظة في `state.json` باعتبارها المصدر
النهائي للإحصاء؛ بل تعيد الحساب من:

- Parquet blocks المحفوظة في Stage 7.
- Parquet blocks الجديدة التي تنتجها Stage 11.

وبذلك تُحسب الإحصاءات من Dataset الكامل الفعلي، دون الاعتماد على
إحصاءات جزئية محفوظة من تشغيلات مختلفة.

## قاعدة التحقق قبل أي استئناف

قبل استئناف أي سيناريو في Stage 11:

1. اقرأ `state.json` من فرع `stage7-state/<scenario>`.
2. تحقق من أن `source_sha == SOURCE_SHA` الحالي.
3. تحقق من أن `master_seed == MASTER_SEED` الحالي.
4. أعد حساب fingerprint محلياً من Parquet blocks وتحقق من مطابقته
   للـfingerprint المحفوظ للسلسلة.
5. تحقق من أن `stability_history` متسق ولا توجد فجوات زمنية غير مبررة.
6. تحقق من أن `artifact_identity.scenario` يساوي السيناريو الحالي.
7. تحقق من أن schema الخاص بالـstate هو Stage 7، أي `stage == "7"`.

إذا فشل أي تحقق:

- يُرفض الاستئناف.
- يُعتبر الـcheckpoint Dataset مختلفاً.
- يبدأ التشغيل من `trial_id = 1` على `SOURCE_SHA` الحالي.
- لا تُخلط النتيجتان في نفس الإحصاءات.

## سلوك فشل التحقق

قاعدة القرار هي:

> **Dataset مختلف → لا استئناف.**

لا يجوز استخدام `next_trial_id` من checkpoint لم ينجح في تحقق الهوية.

## عدم التأثير على Stage 7 الجارية

هذه السياسة لا تغيّر Stage 7 الجارية ولا توقفها ولا تعيد تشغيلها.

Stage 7 تستمر وفق كودها وسياساتها الحالية.

دور Stage 11 يبدأ فقط عند طلب الاستئناف وبعد التحقق الكامل من checkpoint.
