# U3 v2.3 Acceptance Report

Status: PASS_SCOPED for this tested candidate SHA; not production-release acceptance.
Tested commit SHA: adbb528f5f44e21425ce6210148eac41ff4401fb
GitHub Actions Run: 40260476507 (https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40260476507)
Command: python -m pytest -q tests --junitxml=/tmp/u3-junit.xml
Actual pytest exit code: 0
Full-suite log SHA-256: d7df9a44f43cb3a7a5317792f88c7d00c368a555b2ce9dea2e81d4a97c4f8758
JUnit XML SHA-256: 9e5957c459f0e0425bb4cf2a9e644c24dc668df15cd2d1b33f9688a2487b5c97
Register: 193 rows = 177 UNIQUE + 15 ALIAS + 1 DOC/K_TEST (Test 158)
Logic results: 177 PASS from 177 UNIQUE; 0 FAIL; 0 NOT_EXECUTED; 15/15 ALIAS pass; 1 DOC
Undefined test definitions: []
The historic U2 Run 40210753738 remains recorded as failed on its own tested SHA; it is not overwritten by this candidate result.
Production Gate A, new-source Golden, cohort generation and actual S4-S9 output artifacts remain distinct gates.
Owner-approved Appendix E is the normative override for §14.11.4 and specifies the sequential alpha-spending procedure; this candidate therefore implements that method. The live state.json on main still carries the earlier K_SPEC text and was not modified. This run proves executable tests only: no new-source Golden/cohort, production Gate A/B, CONVERGED, or FINAL_ACCEPTED is claimed.

## Full mapping 1-193

| ID | Type | Canonical pytest name | Test file | Alias target | Logic result | Production status | Stage / reason |
|---:|---|---|---|---:|---|---|---|
| 1 | UNIQUE | رأس_المال_الكلي | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 2 | UNIQUE | عدد_الدراجات_التأسيسية | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 3 | UNIQUE | إجمالي_أصول_الدراجات_الافتتاحية | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 4 | UNIQUE | الخسارة_الافتتاحية | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 5 | UNIQUE | النقدية_الافتتاحية | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 6 | UNIQUE | الميزانية_الافتتاحية_متوازنة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 7 | UNIQUE | لا_دراجة_أخرى_غير_العشرة_في_اليوم_الأول | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 8 | UNIQUE | شراء_توسع_بـ350000_يخصم_من_cash_و_partner1_rb_معا | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 9 | UNIQUE | الدراجة_تدخل_PREP_عند_الشراء | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 10 | UNIQUE | لا_استهلاك_في_PREP | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 11 | UNIQUE | لا_عقد_في_PREP | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 12 | UNIQUE | دفع_4000_ينشئ_مصروفا_فقط | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 13 | UNIQUE | دفع_10000_يزيد_gross_cost | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 14 | UNIQUE | لا_جاهزية_قبل_اكتمال_كامل_14000 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 15 | UNIQUE | FIFO_في_تجهيز_دراجات_متعددة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 16 | UNIQUE | لا_شراء_توسع_جديد_قبل_تمويل_PREP_القائمة_بالكامل | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 17 | UNIQUE | استمرار_تمويل_PREP_بعد_2030_12_31 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 18 | UNIQUE | عدم_التسليم_يوم_الجمعة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 19 | UNIQUE | تسليم_السبت_اول_جمعة_بعد_6_ايام | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 20 | UNIQUE | تسليم_الاحد_اول_جمعة_بعد_5_ايام | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 21 | UNIQUE | تسليم_الاثنين_اول_جمعة_بعد_4_ايام | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 22 | UNIQUE | تسليم_الثلاثاء_اول_جمعة_معفاة_والتي_تليها | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 23 | UNIQUE | تسليم_الاربعاء_اول_جمعة_معفاة_والتي_تليها | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 24 | UNIQUE | تسليم_الخميس_اول_جمعة_معفاة_والتي_تليها | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 25 | UNIQUE | لا_استهلاك_قبل_التسليم_ويبدأ_من_يوم_التسليم | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 26 | UNIQUE | تحصيل_100_لا_ينتج_فسخا | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 27 | UNIQUE | تحصيل_0_فسخ_اساسي_اليوم_30_وثانوي_اليوم_10 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 28 | UNIQUE | لا_متأخرات_دفعة_يوم_واحد | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 29 | UNIQUE | متأخر_يوم_دفعة_يومين | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 30 | UNIQUE | متأخر_800 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 31 | UNIQUE | منع_تجاوز_total_paid_total_due | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 32 | UNIQUE | FIFO_ضمني_في_تسوية_المتأخرات | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 33 | UNIQUE | لا_تحصيل_ولا_استحقاق_إيجار_الجمعة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 34 | UNIQUE | اليوم_20_انتظار | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 35 | UNIQUE | اليوم_21_انذار | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 36 | UNIQUE | اليوم_27_انذار | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 37 | UNIQUE | اليوم_28_مهلة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 38 | UNIQUE | اليوم_30_قبل_الفسخ_مهلة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 39 | UNIQUE | نجاح_تحصيل_اليوم_الحرج_يلغي_الفسخ | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 40 | UNIQUE | فشل_التحصيل_في_اليوم_الحرج_ينتج_فسخا | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 41 | UNIQUE | انخفاض_الدين_يعيد_تصنيف_الحالة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 42 | UNIQUE | لا_تواريخ_انذار_محفوظة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 43 | UNIQUE | الثانوي_يفسخ_عند_10000 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 44 | UNIQUE | لا_عداد_ايام_منفصل | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 45 | UNIQUE | يوم_النضج_يستحق_ايجارا_عاديا | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 46 | UNIQUE | ضبط_بداية_التسوية_يتم_في_M12 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 47 | UNIQUE | اول_يوم_عمل_بعد_النضج_هو_يوم_التسوية_الاول | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 48 | UNIQUE | ايجار_التسوية_حتمي | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 49 | UNIQUE | سداد_الدين_القديم_ذو_رمية_مستقلة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 50 | UNIQUE | اكتمال_السداد_في_اليوم_1_تمليك_فوري | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 51 | UNIQUE | اكتمال_السداد_في_اليوم_3 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 52 | UNIQUE | اكتمال_السداد_في_اليوم_29 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 53 | UNIQUE | اكتمال_السداد_في_اليوم_30 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 54 | UNIQUE | فشل_التسوية_في_نهاية_اليوم_30 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 55 | UNIQUE | سقوط_حق_التمليك_نهائيا_بعد_الفشل | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 56 | UNIQUE | استمرار_عداد_الجمعة_اثناء_التسوية | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 57 | UNIQUE | استمرار_الاستهلاك_اثناء_التسوية_والجمعة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 58 | UNIQUE | فسخ_اساسي_30_يوما | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 59 | UNIQUE | فسخ_ثانوي_20_يوما | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 60 | UNIQUE | فشل_تسوية_60_يوما | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 61 | UNIQUE | المطالبة_تاريخ_انشائها_هو_تاريخ_الحدث | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 62 | UNIQUE | موعد_التسوية_يحفظ_عند_الانشاء | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 63 | UNIQUE | انتظار_صفر_فوري | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 64 | UNIQUE | عد_الانتظار_تقويمي_لا_عملي | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 65 | UNIQUE | استرداد_100 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 66 | UNIQUE | استرداد_70 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 67 | UNIQUE | استرداد_50 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 68 | UNIQUE | استرداد_30 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 69 | UNIQUE | استرداد_0 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 70 | UNIQUE | اول_عقد_ثانوي | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 71 | UNIQUE | فسخ_ثانوي | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 72 | UNIQUE | مطالبة_فسخ_ثانوي_20_يوما | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 73 | UNIQUE | عقد_ثانوي_ثان_مستاجر_جديد | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 74 | UNIQUE | عقد_ثانوي_ثالث | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 75 | UNIQUE | عقد_ثانوي_رابع | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 76 | UNIQUE | تكرار_الدورات_بلا_حد_اقصى_مبرمج | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 77 | UNIQUE | عداد_الجمعة_يبدأ_من_صفر_مع_كل_عقد_ثانوي | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 78 | UNIQUE | لا_حق_تمليك_للعقد_الثانوي | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 79 | UNIQUE | توقف_الشراء_الجديد_بعد_2030_12_31 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 80 | UNIQUE | السماح_بالشراء_في_2030_12_31 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 81 | UNIQUE | لا_اغلاق_قبل_2031_01_01 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 82 | ALIAS | استمرار_الدراجة_المشتراة_في_2030_12_31 | tests/test_acceptance_16_v2.py | 17 | PASS | NOT_REQUIRED |  |
| 83 | UNIQUE | استمرار_العقود_الاساسية_بعد_القطع | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 84 | UNIQUE | استمرار_فترة_التسوية_بعد_القطع | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 85 | UNIQUE | لا_اغلاق_مع_PREP_غير_مكتملة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 86 | UNIQUE | لا_اغلاق_مع_عقد_اساسي_نشط | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 87 | UNIQUE | لا_اغلاق_مع_تسوية_نشطة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 88 | UNIQUE | اغلاق_لا_يشترط_خلو_المطالبات_او_AR_او_GCR | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 89 | UNIQUE | تحقق_الشروط_الاربعة_يشغل_الاغلاق | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 90 | UNIQUE | تحصيل_الثانوي_قبل_الاغلاق_في_نفس_اليوم | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 91 | UNIQUE | رسم_الجمعة_في_يوم_الاغلاق | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 92 | UNIQUE | الاستهلاك_في_يوم_الاغلاق | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 93 | UNIQUE | انهاء_العقود_الثانوية_في_نهاية_الاغلاق | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 94 | UNIQUE | انشاء_مطالبة_ADMINISTRATIVE_CLOSURE_للمتأخرات | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 95 | UNIQUE | تسوية_فورية_قسرية_لكل_المطالبات_عند_الاغلاق | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 96 | UNIQUE | AR_صفر_بعد_الاغلاق | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 97 | UNIQUE | لا_مطالبات_pending_بعد_الاغلاق | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 98 | UNIQUE | لا_عقود_مفتوحة_بعد_الاغلاق | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 99 | UNIQUE | لا_شراء_بعد_الاغلاق | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 100 | UNIQUE | الجرد_النهائي_دقيق | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 101 | UNIQUE | التسوية_الختامية_تطابق_حقوق_الملكية | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 102 | ALIAS | توازن_الميزانية_الافتتاحية_محاسبيا | tests/test_acceptance_16_v2.py | 6 | PASS | NOT_REQUIRED |  |
| 103 | UNIQUE | توازن_يومي_فعلي_في_كل_يوم | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 104 | UNIQUE | توازن_سنوي | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 105 | UNIQUE | توازن_نهائي_بعد_الاغلاق | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 106 | UNIQUE | rollforward_النقدية | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 107 | UNIQUE | rollforward_الذمم_المدينة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 108 | UNIQUE | rollforward_الأصول_الإجمالية | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 109 | UNIQUE | rollforward_مجمع_الاستهلاك | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 110 | UNIQUE | rollforward_حقوق_الملكية | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 111 | UNIQUE | منع_ازدواج_ايراد_التحصيل | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 112 | UNIQUE | عدم_دخول_استرداد_الكفالة_في_الربح | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 113 | UNIQUE | marketing_ليس_تشغيليا_بعد_البداية | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 114 | UNIQUE | منع_ازدواج_مصروف_التجهيز | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 115 | UNIQUE | استخدام_bike_gross_cost_حصرا | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 116 | UNIQUE | تحديث_accumulated_المحلي_لا_يغير_حساب_المشروع_مرة_ثانية | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 117 | UNIQUE | لا_توزيعات_نقدية_فعلية | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 118 | UNIQUE | المشروع_كيان_اقتصادي_واحد | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 119 | UNIQUE | الأصول_التوسعية_موحدة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 120 | UNIQUE | الشريك_الأول_70_عند_الاغلاق | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 121 | UNIQUE | الشريك_الثاني_30_عند_الاغلاق | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 122 | UNIQUE | لا_فرض_تطابق_الرصيد_مع_الحصة_النهائية | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 123 | UNIQUE | لا_ازدواج_للنقد_مع_رصيد_المذكرة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 124 | UNIQUE | التوزيع_النهائي_يساوي_صافي_الحقوق | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 125 | UNIQUE | رأس_المال_لا_يضاف_مرتين | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 126 | UNIQUE | إعادة_التشغيل_بنفس_البذرة_حرفيا | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 127 | UNIQUE | تطابق_التسلسلي_والمتوازي | tests/test_acceptance_16_v2.py |  | PASS | DEFERRED | S5: production worker-equivalence manifest has not been generated |
| 128 | UNIQUE | استقلال_السيناريوهات | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 129 | UNIQUE | استقلال_النتائج_عن_ترتيب_التنفيذ | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 130 | UNIQUE | لا_RNG_لرسوم_الجمعة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 131 | UNIQUE | لا_RNG_للكفالة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 132 | UNIQUE | رمية_الدين_القديم_مستقلة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 133 | ALIAS | اولوية_التحصيل_على_الفسخ | tests/test_acceptance_16_v2.py | 39 | PASS | NOT_REQUIRED |  |
| 134 | ALIAS | دراجة_في_اول_يوم_تجهيز | tests/test_acceptance_16_v2.py | 9 | PASS | NOT_REQUIRED |  |
| 135 | ALIAS | الجمعة_ليست_يوم_عمل_ولا_استحقاق_ايجار | tests/test_acceptance_16_v2.py | 33 | PASS | NOT_REQUIRED |  |
| 136 | ALIAS | اختبار_p0_الحدي | tests/test_acceptance_16_v2.py | 27 | PASS | NOT_REQUIRED |  |
| 137 | UNIQUE | تأخر_جزئي_ثم_سداد_بلا_فسخ | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 138 | UNIQUE | دورة_الفسخ_والتأجير_الثانوي | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 139 | ALIAS | كفالة_0_دين_معدوم_كامل | tests/test_acceptance_16_v2.py | 69 | PASS | NOT_REQUIRED |  |
| 140 | ALIAS | كفالة_100_استرداد_كامل | tests/test_acceptance_16_v2.py | 65 | PASS | NOT_REQUIRED |  |
| 141 | UNIQUE | دورات_ثانوية_متكررة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 142 | UNIQUE | نهاية_عقد_بلا_دين_تمليك_فوري | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 143 | UNIQUE | نهاية_عقد_بدين_نجاح_التسوية | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 144 | UNIQUE | السداد_القديم_min_1500 | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 145 | ALIAS | فشل_التسوية_وسقوط_التمليك | tests/test_acceptance_16_v2.py | 55 | PASS | NOT_REQUIRED |  |
| 146 | UNIQUE | الاغلاق_ديناميكي_وليس_تاريخا_ثابتا | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 147 | ALIAS | شراء_في_آخر_يوم_مسموح | tests/test_acceptance_16_v2.py | 80 | PASS | NOT_REQUIRED |  |
| 148 | UNIQUE | رسم_جمعة_وتغيير_زيت_معا | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 149 | UNIQUE | الاستهلاك_فقط_في_حالات_الحيازة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 150 | UNIQUE | منع_ازدواج_تسوية_المطالبة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 151 | ALIAS | اعادة_تشغيل_نفس_seed | tests/test_acceptance_16_v2.py | 126 | PASS | NOT_REQUIRED |  |
| 152 | UNIQUE | recovery_rate_عدد_صحيح | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 153 | ALIAS | لا_حسابات_جارية_للشركاء | tests/test_acceptance_16_v2.py | 118 | PASS | NOT_REQUIRED |  |
| 154 | UNIQUE | الثانوي_لا_يمنع_الاغلاق | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 155 | ALIAS | gross_cost_هو_المصدر_الوحيد_للشطب_والاستهلاك | tests/test_acceptance_16_v2.py | 115 | PASS | NOT_REQUIRED |  |
| 156 | UNIQUE | لا_PROJECT_END_DATE_يوقف_الحلقة | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 157 | UNIQUE | لا_سقف_زمني_تشخيصي_في_المحرك | tests/test_acceptance_16_v2.py |  | PASS | NOT_REQUIRED |  |
| 158 | DOC | الاحدث_يلغي_الاقدم_توثيقيا | tests/test_acceptance_16_v2.py |  | ADJUDICATION | NOT_REQUIRED |  |
| 159 | UNIQUE | اختيار_التكرار_التمثيلي_حسب_Final_Net_Project_Equity_فقط | tests/test_acceptance_16_v2.py |  | PASS | DEFERRED | S5: production trials_summary.parquet has not been generated; the selector is tested on in-memory data |
| 160 | UNIQUE | التكرارات_التوضيحية_الاربعة_تنتج_فعليا | tests/test_acceptance_16_v2.py |  | PASS | DEFERRED | S5: production selection.parquet and representative DAILY files have not been generated; the selection contract is tested in memory |
| 161 | UNIQUE | DAILY_DISTRIBUTION_لكل_يوم_تقويمي_بلا_فجوات | tests/test_acceptance_16_v2.py |  | PASS | DEFERRED | S5: production daily_distribution.parquet has not been generated; the calendar-date gap validator is tested in memory |
| 162 | ALIAS | شروط_الاغلاق_لا_تشترط_المطالبات_او_الذمم | tests/test_acceptance_16_v2.py | 88 | PASS | NOT_REQUIRED |  |
| 163 | ALIAS | تسوية_المطالبات_فورا_عند_الاغلاق | tests/test_acceptance_16_v2.py | 95 | PASS | NOT_REQUIRED |  |
| 164 | UNIQUE | settlement_failure_occurs_on_business_day_30 | tests/test_u2_reference_corrections.py |  | PASS | NOT_REQUIRED |  |
| 165 | UNIQUE | settlement_start_date_is_set_in_m12_for_maturity_weekdays | tests/test_u2_reference_corrections.py |  | PASS | NOT_REQUIRED |  |
| 166 | UNIQUE | m2_purchases_at_most_one_expansion_bike_per_day | tests/test_u2_reference_corrections.py |  | PASS | NOT_REQUIRED |  |
| 167 | UNIQUE | customs_are_in_investing_cash_outflows_and_cash_rollforward | tests/test_u2_reference_corrections.py |  | PASS | NOT_REQUIRED |  |
| 168 | UNIQUE | first_eligible_friday_is_stored_per_secondary_contract | tests/test_u2_reference_corrections.py |  | PASS | NOT_REQUIRED |  |
| 169 | UNIQUE | C100_golden_must_match_source_and_cohort_identity | tests/test_v23_acceptance.py |  | PASS | DEFERRED | S4: a reviewed C100 Golden for this new source/cohort is not yet approved |
| 170 | UNIQUE | checksum_uniqueness_uses_draw_count_and_allows_zero | tests/test_v23_acceptance.py |  | PASS | DEFERRED | S5: production checksum uniqueness requires the authorized cohort |
| 171 | UNIQUE | rng_stream_pairing_and_integer_success_threshold | tests/test_u2_reference_corrections.py |  | PASS | NOT_REQUIRED |  |
| 172 | UNIQUE | sequential_alpha_spending_is_exact_and_applied_to_gate_intervals | tests/test_v23_acceptance.py |  | PASS | DEFERRED | S5: production inference coverage is separate from the pure alpha-spending rule |
| 173 | UNIQUE | stall_detector_requires_all_reference_conditions | tests/test_u2_reference_corrections.py |  | PASS | NOT_REQUIRED |  |
| 174 | UNIQUE | financial_fingerprint_is_identical_after_sharding_and_merge | tests/test_v23_acceptance.py |  | PASS | DEFERRED | S5: production complete-pass/sharding replay is not generated |
| 175 | UNIQUE | arabic_english_numeric_mappings_match_exactly | tests/test_v23_acceptance.py |  | PASS | DEFERRED | S7: the two production 185-sheet workbooks have not been generated |
| 176 | UNIQUE | number_registry_requires_every_reported_number_and_source | tests/test_v23_acceptance.py |  | PASS | DEFERRED | S8: number_registry has not been reconciled to actual deliverables |
| 177 | UNIQUE | no_integer_magic_numbers_outside_constants_py | tests/test_u2_reference_corrections.py |  | PASS | NOT_REQUIRED |  |
| 178 | UNIQUE | unified_names_only_in_engine_and_active_output_builder | tests/test_u2_reference_corrections.py |  | PASS | NOT_REQUIRED |  |
| 179 | UNIQUE | manifest_hashes_and_provenance_are_verified | tests/test_v23_acceptance.py |  | PASS | DEFERRED | S6: production run manifest has not been generated |
| 180 | UNIQUE | daily_mapping_round_trip_preserves_header_order_and_values | tests/test_v23_acceptance.py |  | PASS | DEFERRED | S7: production DAILY workbook round-trip requires the generated workbook |
| 181 | UNIQUE | daily_snapshot_emits_partner_balances_as_integer_evidence | tests/test_v23_acceptance.py |  | PASS | DEFERRED | S7: historical representative daily balances are absent; new-source output needs validation |
| 182 | UNIQUE | financial_fraction_uses_exact_integer_or_round_half_even | tests/test_v23_acceptance.py |  | PASS | DEFERRED | S8: production Excel/report numbers have not been reconciled against number_registry |
| 183 | UNIQUE | cohort_identity_rejects_mixed_source_or_cohort | tests/test_v23_acceptance.py |  | PASS | DEFERRED | S6: production cohort identity manifest has not been generated |
| 184 | UNIQUE | checksum_zero_with_real_draw_is_valid_but_duplicate_is_not | tests/test_v23_acceptance.py |  | PASS | DEFERRED | S5: production RNG audit records have not been generated for the new cohort |
| 185 | UNIQUE | cumulative_checkpoints_and_c100_start_at_300 | tests/test_v23_acceptance.py |  | PASS | NOT_REQUIRED |  |
| 186 | UNIQUE | manifest_contract_accepts_seven_deliverables_plus_manifest | tests/test_v23_acceptance.py |  | PASS | DEFERRED | S8: the seven production deliverables and eight-member archive have not been generated |
| 187 | UNIQUE | bike_ids_are_strictly_four_decimal_digits | tests/test_v23_acceptance.py |  | PASS | NOT_REQUIRED |  |
| 188 | UNIQUE | canonical_rng_key_vector_matches_sha256_u64_checksum_and_threshold | tests/test_v23_acceptance.py |  | PASS | NOT_REQUIRED |  |
| 189 | UNIQUE | financial_fingerprint_is_independent_from_rng_audit_fingerprint | tests/test_v23_acceptance.py |  | PASS | NOT_REQUIRED |  |
| 190 | UNIQUE | c100_repeated_ids_are_degenerate_not_independent | tests/test_v23_acceptance.py |  | PASS | NOT_REQUIRED |  |
| 191 | UNIQUE | five_representative_roles_use_equity_extrema_and_trial_id_ties | tests/test_v23_acceptance.py |  | PASS | DEFERRED | S5: production representative roles must be reselected on the approved cohort |
| 192 | UNIQUE | owner_approved_appendix_e_alpha_spending_is_applied_to_gate_b | tests/test_v23_acceptance.py |  | PASS | DEFERRED | S5: production Gate B interval coverage and stability need the approved full cohort; logic method is tested in memory |
| 193 | UNIQUE | historical_and_new_rng_cohorts_cannot_be_mixed | tests/test_v23_acceptance.py |  | PASS | DEFERRED | S6: new source/cohort/Golden evidence requires separately approved production work |

## Deferred production evidence

A PASS in the logic column means only that the specified in-memory test ran. Artifact checks are DEFERRED only where production outputs have not been generated or approved; no production results files are fabricated.

- S4: Test IDs 169; the table above names each exact dependency.
- S5: Test IDs 127, 159, 160, 161, 170, 172, 174, 184, 191, 192; the table above names each exact dependency.
- S6: Test IDs 179, 183, 193; the table above names each exact dependency.
- S7: Test IDs 175, 180, 181; the table above names each exact dependency.
- S8: Test IDs 176, 182, 186; the table above names each exact dependency.

## Gate judgement

Executable logic gate: PASS.
Production statistical gate: NOT ACCEPTED on this run because production source/cohort/Golden and Gate A/B acceptance evidence are not part of this pytest run. Appendix E formula-level unit tests do not prove the production cohort converged.
A bike-ID/RNG behavior change requires a new source identity, cohort and Golden. Historical data and Golden fingerprints were not rewritten.
C100 repetitions are DEGENERATE_DETERMINISTIC with N_unique_paths=1 when paths match; repeated paths are not independent observations.
Test 158 remains DOC/K_TEST / ADJUDICATION and is not counted in 177 UNIQUE tests.
Pytest log digest: d7df9a44f43cb3a7a5317792f88c7d00c368a555b2ce9dea2e81d4a97c4f8758
