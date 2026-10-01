# تدقيق واجهات Stage 2 — R4/R6 بأثر رجعي

**الأساس:** المرجع النهائي المعتمد، الأبواب 3.1–3.8 و4.1–4.4، وواجهات `tests/test_stage1.py` و`tests/test_stage2.py` على `main`، مع `stage3b-preserved` كدليل واجهة فقط.

**قاعدة البناء:** لم يُنسخ أي كود من `stage3b-preserved`. استخدم للمقارنة الاسمية/التوقيعية فقط. لا يدخل هذا الملف في الكود التنفيذي ولا في الاختبارات.

**تفسير R6 في هذا التدقيق:** 1 = قيمة/حالة بدائية مخزنة مباشرة؛ 2 = قيمة مشتقة/محسوبة؛ 3 = مجموعة/سجل/حاوية؛ 4 = اسم تشغيلي/Enum/State/API. بالنسبة لواجهات الدوال والكلاسات يُستخدم النوع 4.

| الاسم | موجود في stage3b | مستخدم في اختبارات main | مطابق للمرجع | انحراف معتمد | القرار | النوع (1/2/3/4) |
|---|---|---|---|---|---|---|
| Project | project_cash | نعم | نعم | نعم؛ 3.1 نقدية موحّدة | — | مرجع | 1 |
| Project | partner1_reinvestment_balance | نعم | نعم | نعم؛ 3.1 Memo داخلي | — | مرجع | 1 |
| Project | partner2_reinvestment_balance | نعم | نعم | نعم؛ 3.1 Memo داخلي | — | مرجع | 1 |
| Project | accounts_receivable | نعم | لا في Stage2 مباشرة | نعم؛ رصيد موحّد يدعم 3.7 والمحاسبة اللاحقة | — | مرجع تشغيلي لاحق | 1 |
| Project | guarantee_claim_receivable | نعم | لا | نعم؛ رصيد مطالبات الكفالة في المحاسبة اللاحقة | — | مرجع تشغيلي لاحق | 1 |
| Project | gross_bike_assets | نعم | لا | نعم؛ أصول المشروع/roll-forward | — | مرجع تشغيلي | 1 |
| Project | accumulated_depreciation | نعم | لا | نعم؛ roll-forward الإهلاك اللاحق | — | مرجع تشغيلي | 1 |
| Project | capital | نعم | لا | نعم؛ رأس المال الافتتاحي | — | مرجع تشغيلي | 1 |
| Project | retained_earnings | نعم | لا | نعم؛ حقوق/أرباح محاسبية لاحقة | — | مرجع تشغيلي | 1 |
| Project | opening_loss | نعم | لا | نعم؛ الخسارة الافتتاحية | — | مرجع تشغيلي | 1 |
| Project | revenue_primary | نعم | لا | نعم لاحقاً؛ إيراد الأساسي | — | مرجع تشغيلي لاحق | 1 |
| Project | revenue_secondary | نعم | لا | نعم لاحقاً؛ إيراد الثانوي | — | مرجع تشغيلي لاحق | 1 |
| Project | revenue_settlement | نعم | لا | نعم لاحقاً؛ إيراد التسوية | — | مرجع تشغيلي لاحق | 1 |
| Project | revenue_friday_fee | نعم | لا | نعم لاحقاً؛ رسم الجمعة | — | مرجع تشغيلي لاحق | 1 |
| Project | expense_depreciation | نعم | لا | نعم لاحقاً؛ مصروف الإهلاك | — | مرجع تشغيلي لاحق | 1 |
| Project | expense_oil_service | نعم | لا | نعم لاحقاً؛ مصروف الزيت | — | مرجع تشغيلي لاحق | 1 |
| Project | expense_prep | نعم | لا | نعم لاحقاً؛ مصروف التجهيز | — | مرجع تشغيلي لاحق | 1 |
| Project | expense_marketing | نعم | لا | نعم لاحقاً؛ مصروف التسويق الافتتاحي | — | مرجع تشغيلي لاحق | 1 |
| Project | bad_debt_expense | نعم | لا | نعم لاحقاً؛ الديون المعدومة | — | مرجع تشغيلي لاحق | 1 |
| Project | asset_writeoff_expense | نعم | لا | نعم لاحقاً؛ شطب الأصول | — | مرجع تشغيلي لاحق | 1 |
| Project | operating_revenue | لا | لا | نعم لاحقاً؛ تجميع تشغيلي 10.x | — | مقبول؛ حقل مشتق لاحق | 2 |
| Project | operating_expenses | لا | لا | نعم لاحقاً؛ تجميع تشغيلي 10.x | — | مقبول؛ حقل مشتق لاحق | 2 |
| Project | operating_net_profit | لا | لا | نعم لاحقاً؛ 10.x | — | مقبول؛ حقل مشتق لاحق | 2 |
| Project | cumulative_project_profit | لا | لا | نعم لاحقاً؛ 10.10 | — | مقبول؛ حقل مشتق لاحق | 2 |
| Project | final_close_date | نعم | لا | نعم؛ الإغلاق ديناميكي ولا تاريخ ثابت | — | مرجع | 2 |
| Project | final_net_project_equity | نعم | لا | نعم؛ M15/M17 | — | مرجع | 2 |
| Project | partner1_final_entitlement | نعم | لا | نعم؛ 70% عند الإغلاق | — | مرجع | 2 |
| Project | partner2_final_entitlement | نعم | لا | نعم؛ 30% عند الإغلاق | — | مرجع | 2 |
| Project | simulation_stopped | نعم | لا | مقبول كسجل تشغيل؛ ليس حقل محاسبة مرجعياً | — | تشغيلي | 1 |
| Project | bikes | نعم | لا | نعم؛ مجموعة كيانات المشروع | — | مرجع | 3 |
| Project | contracts | نعم | لا | نعم؛ مجموعة كيانات المشروع | — | مرجع | 3 |
| Project | tenants | نعم | لا | نعم؛ مجموعة كيانات المشروع | — | مرجع | 3 |
| Project | guarantors | نعم | لا | نعم؛ مجموعة كيانات المشروع | — | مرجع | 3 |
| Project | guarantee_claims | نعم | لا | نعم؛ مجموعة مطالبات الكفالة | — | مرجع | 3 |
| Project | receivables | نعم | لا | نعم؛ دفتر ذمم تفصيلي تابع | — | مرجع | 3 |
| Project | event_log | نعم | لا | نعم؛ سجل أحداث | — | مرجع | 3 |
| Project | cash_rollforward | لا | لا | نعم لاحقاً؛ roll-forward النقد | — | مقبول للسجل اللاحق | 3 |
| Project | ar_rollforward | لا | لا | نعم لاحقاً؛ roll-forward الذمم | — | مقبول للسجل اللاحق | 3 |
| Project | gross_asset_rollforward | لا | لا | نعم لاحقاً؛ roll-forward الأصول الإجمالية | — | مقبول للسجل اللاحق | 3 |
| Project | depreciation_rollforward | لا | لا | نعم لاحقاً؛ roll-forward الإهلاك | — | مقبول للسجل اللاحق | 3 |
| Project | daily_snapshots | لا | لا | نعم لاحقاً؛ سجل يومي | — | مقبول للسجل اللاحق | 3 |
| Project | daily_balance_checks | نعم | لا | نعم لاحقاً؛ اختبارات التوازن | — | مقبول | 3 |
| Project | execution_trace | نعم | لا | مقبول كسجل تتبع تنفيذي | — | تشغيلي | 3 |
| Project | error_log | لا | لا | مقبول كسجل أخطاء تنفيذي | — | تشغيلي | 3 |
| Bike | bike_id | نعم | نعم | نعم؛ 3.2 | — | مرجع | 1 |
| Bike | source | نعم | نعم | نعم؛ INITIAL/EXPANSION | — | مرجع | 4 |
| Bike | purchase_date | نعم | نعم | نعم؛ 3.2 | — | مرجع | 1 |
| Bike | scheduled_ready_date | نعم | نعم | نعم؛ purchase_date + 6 days | — | مرجع | 2 |
| Bike | funding_completion_date | نعم | لا | نعم؛ 3.2 | — | مرجع | 1 |
| Bike | actual_ready_date | نعم | لا | نعم؛ max(...) عند اكتمال الدفع ثم تثبيت | — | مرجع | 2 |
| Bike | prep_paid | نعم | نعم | نعم؛ 3.2 | — | مرجع | 1 |
| Bike | customs_paid | نعم | نعم | نعم؛ 3.2 | — | مرجع | 1 |
| Bike | delivery_date | نعم | لا | نعم؛ أول يوم عمل في/بعد الجاهزية | — | مرجع | 2 |
| Bike | gross_cost | نعم | نعم | نعم؛ مصدر الحقيقة لتكلفة الأصل | — | مرجع | 1 |
| Bike | accumulated_depreciation | نعم | لا | نعم؛ حد أقصى 360,000 | — | مرجع | 2 |
| Bike | net_book_value | نعم | نعم | نعم؛ max(0,gross_cost-AD) | — | مرجع | 2 |
| Bike | current_state | نعم | نعم | نعم؛ Enum من 11 حالة | النسخة النهائية تجعل `BikeState` في entities كمصدر واحد ويُعاد تصديره عبر state_machine بدل تكراره | انحراف بنيوي معتمد؛ يحافظ على واجهة الاختبارات | 4 |
| Bike | current_contract_id | نعم | لا | نعم؛ رابط فقط | — | مرجع | 1 |
| Bike | current_tenant_id | نعم | لا | نعم؛ رابط فقط | — | مرجع | 1 |
| Bike | settlement_start_date | نعم | لا | نعم؛ أول يوم عمل بعد النضج | — | مرجع | 1 |
| Bike | settlement_legacy_debt_original | نعم | لا | نعم؛ 3.2 | — | مرجع | 1 |
| Bike | settlement_legacy_debt_remaining | نعم | لا | نعم؛ 3.2 | — | مرجع | 2 |
| Bike | settlement_business_days_elapsed | نعم | لا | نعم؛ عدّاد التسوية | — | مرجع | 1 |
| Bike | settlement_rent_due_total | نعم | لا | نعم؛ حقل مستقل لإيجار التسوية | — | مرجع | 1 |
| Bike | settlement_rent_collected_total | نعم | لا | نعم؛ حقل مستقل والتحصيل حتمي | — | مرجع | 1 |
| Bike | termination_count | نعم | نعم | نعم؛ 3.2 | — | مرجع | 1 |
| Bike | secondary_cycle_count | نعم | نعم | نعم؛ بلا حد أقصى | — | مرجع | 1 |
| Bike | usage_days | نعم | نعم | نعم؛ يشمل الجمعة | — | مرجع | 1 |
| Bike | lifecycle_cycle_number | نعم | لا | نعم؛ يبدأ 1 ويزيد مع عقد جديد | — | مرجع | 1 |
| Bike | lifecycle_history | نعم | لا | نعم؛ سجل لا يحذف | — | مرجع | 3 |
| Bike | receivables_ledger | نعم | لا | نعم؛ سجل تابع لـ Accounts_Receivable | — | مرجع | 3 |
| Bike | total_due | لا | نعم (سلباً؛ الاختبار يتحقق من غيابه) | نعم؛ ممنوع على Bike ومصدره Contract | — | مرجع؛ حذف إلزامي | — |
| Bike | total_paid | لا | نعم (سلباً؛ الاختبار يتحقق من غيابه) | نعم؛ ممنوع على Bike ومصدره Contract | — | مرجع؛ حذف إلزامي | — |
| Bike | friday_counter | لا | نعم (سلباً؛ الاختبار يتحقق من غيابه) | نعم؛ ممنوع على Bike ومصدره Contract | — | مرجع؛ حذف إلزامي | — |
| Bike | active_settlement_receivable_id | نعم | لا | لا؛ ليس حقلاً في 3.2 | — | يُستبعد | — |
| Bike | pending_writeoff_today | نعم | لا | لا؛ ليس حقلاً في 3.2 | — | يُستبعد | — |
| Contract | contract_id | نعم | نعم | نعم؛ 3.3 | — | مرجع | 1 |
| Contract | bike_id | نعم | نعم | نعم؛ 3.3 | — | مرجع | 1 |
| Contract | tenant_id | نعم | نعم | نعم؛ 3.3 | — | مرجع | 1 |
| Contract | guarantor_id | نعم | نعم | نعم؛ 3.3 | — | مرجع | 1 |
| Contract | contract_type | نعم | نعم | نعم؛ PRIMARY/SECONDARY | — | مرجع | 4 |
| Contract | daily_rate | نعم | نعم | نعم؛ 1,500 أو 1,000 | — | مرجع | 1 |
| Contract | start_date | نعم | نعم | نعم؛ 3.3 | — | مرجع | 1 |
| Contract | maturity_date | نعم | نعم | نعم؛ للأساسي فقط | — | مرجع | 2 |
| Contract | status | نعم | لا | نعم؛ ACTIVE/MATURED/TERMINATED/SETTLED | — | مرجع | 4 |
| Contract | total_due | نعم | نعم | نعم؛ مصدر الحقيقة الوحيد | — | مرجع | 1 |
| Contract | total_paid | نعم | نعم | نعم؛ مصدر الحقيقة الوحيد | — | مرجع | 1 |
| Contract | friday_counter | نعم | نعم | نعم؛ مصدر الحقيقة الوحيد | — | مرجع | 1 |
| Tenant | tenant_id | نعم | لا | نعم؛ 3.4 | — | مرجع | 1 |
| Tenant | tenant_type | نعم | نعم | نعم؛ ORIGINAL/SECONDARY | — | مرجع | 4 |
| Tenant | contract_id | نعم | نعم | نعم؛ رابط | — | مرجع | 1 |
| Tenant | guarantor_id | نعم | لا | نعم؛ رابط | — | مرجع | 1 |
| Tenant | start_date | نعم | نعم | نعم؛ 3.4 | — | مرجع | 1 |
| Tenant | end_date | نعم | لا | نعم؛ date\|None | — | مرجع | 1 |
| Guarantor | guarantor_id | نعم | نعم | نعم؛ 3.5 | — | مرجع | 1 |
| Guarantor | related_contract_id | نعم | نعم | نعم؛ 3.5 | — | مرجع | 1 |
| Guarantor | related_tenant_id | نعم | نعم | نعم؛ 3.5 | — | مرجع | 1 |
| GuaranteeClaim | claim_id | نعم | لا | نعم؛ 3.6 | — | مرجع | 1 |
| GuaranteeClaim | bike_id | نعم | لا | نعم؛ رابط | — | مرجع | 1 |
| GuaranteeClaim | contract_id | نعم | لا | نعم؛ رابط | — | مرجع | 1 |
| GuaranteeClaim | tenant_id | نعم | لا | نعم؛ رابط | — | مرجع | 1 |
| GuaranteeClaim | guarantor_id | نعم | لا | نعم؛ رابط | — | مرجع | 1 |
| GuaranteeClaim | claim_source | نعم | لا | نعم؛ أحد المصادر الخمسة | — | مرجع | 4 |
| GuaranteeClaim | claim_amount | نعم | لا | نعم؛ المتأخرات وقت الحدث | — | مرجع | 1 |
| GuaranteeClaim | created_date | نعم | لا | نعم؛ نهاية يوم الحدث D | — | مرجع | 1 |
| GuaranteeClaim | waiting_period_days | نعم | لا | نعم؛ حسب المصدر | — | مرجع | 1 |
| GuaranteeClaim | settlement_due_date | نعم | لا | نعم؛ محسوب ومخزّن عند الإنشاء | — | مرجع | 2 |
| GuaranteeClaim | recovery_rate_pct | نعم | لا | نعم؛ 100/70/50/30/0 | — | مرجع | 1 |
| GuaranteeClaim | settlement_date | نعم | لا | نعم؛ date\|None | — | مرجع | 1 |
| GuaranteeClaim | recovered_amount | نعم | لا | نعم؛ حاصل recovery_rate | — | مرجع | 2 |
| GuaranteeClaim | bad_debt_amount | نعم | لا | نعم؛ claim - recovered | — | مرجع | 2 |
| GuaranteeClaim | status | نعم | نعم | نعم؛ PENDING/SETTLED | — | مرجع | 4 |
| ReceivableEntry | receivable_id | نعم | نعم | نعم؛ 3.7 | — | مرجع | 1 |
| ReceivableEntry | bike_id | نعم | نعم | نعم؛ رابط | — | مرجع | 1 |
| ReceivableEntry | contract_id | نعم | نعم | نعم؛ رابط | — | مرجع | 1 |
| ReceivableEntry | tenant_id | نعم | نعم | نعم؛ رابط | — | مرجع | 1 |
| ReceivableEntry | source | نعم | نعم | نعم؛ SETTLEMENT_LEGACY_DEBT | — | مرجع | 4 |
| ReceivableEntry | original_amount | نعم | نعم | نعم؛ 3.7 | — | مرجع | 1 |
| ReceivableEntry | collected_amount | نعم | نعم | نعم؛ 3.7 | — | مرجع | 1 |
| ReceivableEntry | remaining_amount | نعم | نعم | نعم؛ 3.7 | — | مرجع | 2 |
| ReceivableEntry | status | نعم | نعم | نعم؛ 3 قيم | — | مرجع | 4 |
| ReceivableEntry | created_date | نعم | نعم | نعم؛ date | — | مرجع | 1 |
| ReceivableEntry | settlement_date | نعم | لا | نعم؛ date\|None | — | مرجع | 1 |
| EventLogEntry | event_id | نعم | لا | نعم؛ 3.8 | — | مرجع | 1 |
| EventLogEntry | date | نعم | لا | نعم؛ 3.8 | — | مرجع | 1 |
| EventLogEntry | bike_id | نعم | لا | نعم؛ 3.8 | — | مرجع | 1 |
| EventLogEntry | event_type | نعم | نعم | نعم؛ EventType | — | مرجع | 4 |
| EventLogEntry | previous_state | نعم | لا | نعم؛ str\|None في المرجع؛ Enum-string في التنفيذ | تحويل نوعي داخلي آمن مع نفس القيم النصية | مقبول مع واجهة اختبارات مطابقة | 4 |
| EventLogEntry | new_state | نعم | لا | نعم؛ str\|None في المرجع؛ Enum-string في التنفيذ | تحويل نوعي داخلي آمن مع نفس القيم النصية | مقبول مع واجهة اختبارات مطابقة | 4 |
| EventLogEntry | contract_id | نعم | لا | نعم؛ اختياري | — | مرجع | 1 |
| EventLogEntry | tenant_id | نعم | لا | نعم؛ اختياري | — | مرجع | 1 |
| EventLogEntry | guarantor_id | نعم | لا | نعم؛ اختياري | — | مرجع | 1 |
| EventLogEntry | receivable_id | نعم | لا | نعم؛ اختياري | — | مرجع | 1 |
| EventLogEntry | claim_id | نعم | لا | نعم؛ اختياري | — | مرجع | 1 |
| EventLogEntry | amount_if_applicable | نعم | لا | نعم؛ int\|None | — | مرجع | 1 |
| EventLogEntry | balance_before | نعم | لا | نعم؛ int\|None | — | مرجع | 1 |
| EventLogEntry | balance_after | نعم | لا | نعم؛ int\|None | — | مرجع | 1 |
| EventLogEntry | trigger_reason | نعم | لا | نعم؛ str | — | مرجع | 1 |
| EventLogEntry | notes | نعم | لا | نعم؛ str | — | مرجع | 1 |
| Enum | BikeSource: INITIAL, EXPANSION | نعم | نعم | نعم؛ 3.2 | — | مرجع | 4 |
| Enum | ContractType: PRIMARY, SECONDARY | نعم | نعم | نعم؛ 3.3 | — | مرجع | 4 |
| Enum | ContractStatus: ACTIVE, MATURED, TERMINATED, SETTLED | نعم | لا | نعم؛ 3.3 | — | مرجع | 4 |
| Enum | TenantType: ORIGINAL, SECONDARY | نعم | نعم | نعم؛ 3.4 | — | مرجع | 4 |
| Enum | ClaimSource: 5 مصادر المطالبات | نعم | نعم | نعم؛ 3.6/2.4 | — | مرجع | 4 |
| Enum | ClaimStatus: PENDING, SETTLED | نعم | لا | نعم؛ 3.6 | — | مرجع | 4 |
| Enum | ReceivableSource: SETTLEMENT_LEGACY_DEBT | نعم | نعم | نعم؛ 3.7 | — | مرجع | 4 |
| Enum | ReceivableStatus: OUTSTANDING, SETTLED, TRANSFERRED_TO_GUARANTEE | نعم | نعم | نعم؛ 3.7 | — | مرجع | 4 |
| Enum | EventType: 24 قيمة موحدة | نعم | نعم | نعم؛ 3.8 | — | مرجع | 4 |
| Enum | BikeState: 11 حالة | لا في entities؛ موجود في state_machine | نعم | نعم؛ الباب 4.1 | نقل المصدر الوحيد إلى entities وإعادة تصديره من state_machine | انحراف بنيوي معتمد | 4 |
| state_machine | BikeState (11) | نعم في state_machine؛ stage3b كان يعرفها محلياً | نعم | نعم؛ 4.1 | مصدر واحد في entities لتفادي التكرار | مرجع وظيفي مع توحيد داخلي | 4 |
| state_machine | STATE_COUNT | نعم | نعم | نعم؛ عدد الحالات = 11 | اشتقاق تعبيرياً من len(BikeState) وفق R7 | مرجع + R7 | 2 |
| state_machine | FORBIDDEN_STATE_NAMES | نعم | نعم | نعم؛ الحالات الملغاة الأربعة | — | مرجع | 3 |
| state_machine | TransitionRule | نعم | لا | تمثيل هيكلي لجدول 4.3 | — | مقبول كواجهة دعم | 4 |
| state_machine | TRANSITION_TABLE: 18 قاعدة | نعم | نعم | نعم؛ 4.3 | — | مرجع | 3 |
| state_machine | derive_state_from_balance(...) | نعم | نعم | نعم؛ 4.2 وذاكرة صفرية | — | مرجع | 4 |
| state_machine | is_declared_transition(...) | نعم | غير مباشر عبر run_reference_path | مساعد لتنفيذ 4.4؛ ليس دالة مرجعية مستقلة | — | مقبول كواجهة مساعدة | 4 |
| state_machine | run_reference_path(...) | نعم | نعم | نعم؛ تحقق المسارات الستة 4.4 | — | مرجع تشغيلي للاختبار | 4 |
| state_machine | legal_next_state(...) | نعم | نعم | متسق مع قاعدة أن M11 وحدها تنفذ الفسخ | — | مقبول؛ واجهة اختبارية | 4 |
| state_machine | validate_transition_table(...) | نعم في نسخة سابقة؛ ليست في النسخة النهائية | لا | ليست جزءاً لازماً من 4.4 ولا من الاختبار النهائي | — | غير مطلوب؛ لم يُنقل | — |

## ملاحظات تدقيق حاسمة

1. `Bike.total_due`, `Bike.total_paid`, `Bike.friday_counter` مستبعدة عمداً؛ المرجع يجعل `Contract` المصدر الوحيد للحقيقة، واختبار Stage 2 يتحقق من غيابها.
2. الحالتان `active_settlement_receivable_id` و`pending_writeoff_today` موجودتان في `stage3b-preserved` لكنهما غير موجودتين في النسخة النهائية لأنهما غير منصوص عليهما في الباب 3.2.
3. `BikeState` موحّدة في `entities.py`، بينما `state_machine.py` يستوردها ويعيد تصديرها عبر مساحة الاسم. هذا يمنع تعريف الحالات مرتين.
4. الحقول المحاسبية والتتبعية الإضافية في `Project` التي لا تظهر في 3.1 هي دعم تشغيلي لأبواب لاحقة في المرجع، وليست تغييراً في حقيقة كيان Project الموحد.
5. `STATE_COUNT` مشتق تعبيرياً من `len(BikeState)`، ولا يُعرَّف كنص/رقم مستقل وفق R7.

## مصادر التدقيق المستخدمة

- المرجع النهائي: الباب 3.1–3.8 والباب 4.1–4.4.
- `main@d19ca51b8337a475ddd28cce6d661277930f3e48`: النسخة المقبولة لـ Stage 2.
- `stage3b-preserved`: دليل الواجهات التاريخي فقط.
- `tests/test_stage1.py`: SHA في `main` و`stage3b-preserved` مطابق.
- `tests/test_stage2.py`: SHA في `main` و`stage3b-preserved` مطابق.