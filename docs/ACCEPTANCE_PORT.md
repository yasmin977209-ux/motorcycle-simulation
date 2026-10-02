# ACCEPTANCE_PORT.md

- مصدر الاختبارات الأصلي: SHA-256 `7a6d9672ca386f070367382f0117311966fba51ff7f07e9bc7a1561bc902766f` (793 سطراً، 163 اختباراً).
- المرجع البرمجي لواجهات المواءمة: `a2b0a1713cfd9811e5f00e210102abfb3af3e235` (SHA المصدر الذي ثُبّتت عليه أرقام الأسطر).\n- commit main عند اكتمال ملفات v2: يُثبت في تقرير التشغيل بعد التحقق.
- الاختبار 43 هو الاستثناء الوحيد المقصود في نوع الفحص.
- المرجع 4.2: `derive_state_from_balance` تعيد `None` عند بلوغ عتبة الفسخ، وتنفيذ الفسخ نفسه يتم في M11.
- الاختبار 116: `apply_ownership_writeoff` تعيد delta المشروع ولا تحدّث `project.accumulated_depreciation` داخلياً؛ لذلك يطبق v2 الـdelta مرة واحدة فقط.
- الاختبار 144: `apply_legacy_debt_collection` معزولة عن RNG؛ v2 يفحص الصيغة الحتمية مع `remaining_debt=800` ويحافظ على `payment==800`.
- الاختبارات 127/159/160/161 = DEFERRED، والاختبار 158 = ADJUDICATION.

| رقم | الاستدعاء القديم | الاستدعاء الجديد | هل تغيّر المعنى؟ |
|---:|---|---|---|
| 1 | `_new_project` | `_new_project` | لا |
| 2 | `_new_project` | `_new_project` | لا |
| 3 | `_new_project` | `_new_project` | لا |
| 4 | `_new_project` | `_new_project` | لا |
| 5 | `_new_project` | `_new_project` | لا |
| 6 | `_new_project; balance_sheet_snapshot` | `_new_project; balance_sheet_snapshot` | لا |
| 7 | `_new_project` | `_new_project` | لا |
| 8 | `_new_project; daily_engine._m2` | `_new_project; daily_engine._m2(project, current_date)` | لا |
| 9 | `_new_project; daily_engine._m2` | `_new_project; daily_engine._m2(project, current_date)` | لا |
| 10 | `Bike; apply_daily_depreciation` | `Bike; apply_daily_depreciation(gross_cost, accumulated_depreciation, in_tenant_possession)` | لا |
| 11 | `Bike` | `Bike` | لا |
| 12 | `_new_project; Bike; p.bikes.append; daily_engine._m2` | `_new_project; Bike; p.bikes.append; daily_engine._m2(project, current_date)` | لا |
| 13 | `_new_project; Bike; p.bikes.append; daily_engine._m2` | `_new_project; Bike; p.bikes.append; daily_engine._m2(project, current_date)` | لا |
| 14 | `Bike` | `Bike` | لا |
| 15 | `_new_project; Bike; p.bikes.extend; daily_engine._m2` | `_new_project; Bike; p.bikes.extend; daily_engine._m2(project, current_date)` | لا |
| 16 | `_new_project; Bike; p.bikes.append; daily_engine._m2` | `_new_project; Bike; p.bikes.append; daily_engine._m2(project, current_date)` | لا |
| 17 | `_new_project; Bike; p.bikes.append; daily_engine._m2` | `_new_project; Bike; p.bikes.append; daily_engine._m2(project, current_date)` | لا |
| 18 | `_new_project; daily_engine._m3` | `_new_project; daily_engine._m3(project, current_date)` | لا |
| 19 | `eligible_friday_number` | `eligible_friday_number` | لا |
| 20 | `eligible_friday_number` | `eligible_friday_number` | لا |
| 21 | `eligible_friday_number` | `eligible_friday_number` | لا |
| 22 | `eligible_friday_number` | `eligible_friday_number` | لا |
| 23 | `eligible_friday_number` | `eligible_friday_number` | لا |
| 24 | `eligible_friday_number` | `eligible_friday_number` | لا |
| 25 | `daily_engine.create_initial_project; daily_engine.run_day` | `daily_engine.create_initial_project; daily_engine.run_day` | لا |
| 26 | `_deterministic_trial_cached` | `_deterministic_trial_cached` | لا |
| 27 | `_new_project; _add_active_contract; daily_engine.run_day; dd.weekday` | `_new_project; _add_active_contract; daily_engine.run_day; dd.weekday` | لا |
| 28 | `Contract; apply_ordinary_collection` | `Contract; apply_ordinary_collection(total_due, total_paid, daily_rate, success, current_date)` | لا |
| 29 | `Contract; apply_ordinary_collection` | `Contract; apply_ordinary_collection(total_due, total_paid, daily_rate, success, current_date)` | لا |
| 30 | `Contract; apply_ordinary_collection` | `Contract; apply_ordinary_collection(total_due, total_paid, daily_rate, success, current_date)` | لا |
| 31 | `Contract; apply_ordinary_collection` | `Contract; apply_ordinary_collection(total_due, total_paid, daily_rate, success, current_date)` | لا |
| 32 | `Contract; apply_ordinary_collection` | `Contract; apply_ordinary_collection(total_due, total_paid, daily_rate, success, current_date)` | لا |
| 33 | `Contract; apply_ordinary_collection` | `Contract; apply_ordinary_collection(total_due, total_paid, daily_rate, success, current_date)` | لا |
| 34 | `derive_state_from_balance` | `derive_state_from_balance` | لا |
| 35 | `derive_state_from_balance` | `derive_state_from_balance` | لا |
| 36 | `derive_state_from_balance` | `derive_state_from_balance` | لا |
| 37 | `derive_state_from_balance` | `derive_state_from_balance` | لا |
| 38 | `derive_state_from_balance` | `derive_state_from_balance` | لا |
| 39 | `_new_project; _add_active_contract; daily_engine.run_day` | `_new_project; _add_active_contract; daily_engine.run_day` | لا |
| 40 | `_new_project; _add_active_contract; daily_engine.run_day` | `_new_project; _add_active_contract; daily_engine.run_day` | لا |
| 41 | `derive_state_from_balance` | `derive_state_from_balance` | لا |
| 42 | `fields` | `fields` | لا |
| 43 | `daily_engine.terminate_for_default` | `daily_engine._m11(project, current_date, recovery_rate_pct)` | نعم — تغيّر نوع الفحص من قرار خالص إلى تكامل تنفيذ الفسخ عبر M11؛ القيمة المتوقعة بقيت AVAILABLE_FOR_SECONDARY. |
| 44 | `fields` | `fields` | لا |
| 45 | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | لا |
| 46 | `_new_project; _add_active_contract; daily_engine.run_day` | `_new_project; _add_active_contract; daily_engine.run_day` | لا |

| 47 | `_new_project; _add_active_contract; daily_engine.run_day` | `_new_project; _add_active_contract; daily_engine.run_day` | لا |
| 48 | `Contract; apply_settlement_rent` | `Contract; apply_settlement_rent(current_date)` | لا |
| 49 | `derive_seed` | `derive_seed` | لا |
| 50 | `_new_project; _add_active_contract; daily_engine.run_day` | `_new_project; _add_active_contract; daily_engine.run_day` | لا |
| 51 | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | لا |
| 52 | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day; d.weekday` | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day; d.weekday` | لا |
| 53 | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day; d.weekday` | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day; d.weekday` | لا |
| 54 | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | لا |
| 55 | `_new_project; _add_active_contract; daily_engine._m13` | `_new_project; _add_active_contract; daily_engine._m13(project, current_date)` | لا |
| 56 | `Contract; apply_friday_fee_and_oil` | `Contract; apply_friday_fee_and_oil(delivery_date, current_date, friday_counter, in_tenant_possession)` | لا |
| 57 | `Bike; apply_daily_depreciation` | `Bike; apply_daily_depreciation(gross_cost, accumulated_depreciation, in_tenant_possession)` | لا |
| 58 | `waiting_days_for_source` | `_waiting_days_for_source(claim_source)` | لا |
| 59 | `waiting_days_for_source` | `_waiting_days_for_source(claim_source)` | لا |
| 60 | `waiting_days_for_source` | `_waiting_days_for_source(claim_source)` | لا |
| 61 | `_new_project; create_guarantee_claim` | `_new_project; create_guarantee_claim` | لا |
| 62 | `create_guarantee_claim` | `create_guarantee_claim` | لا |
| 63 | `create_guarantee_claim` | `create_guarantee_claim` | لا |
| 64 | `create_guarantee_claim; can_settle_claim` | `create_guarantee_claim; can_settle_claim` | لا |
| 65 | `_claim; settle_guarantee_claim` | `_claim; settle_guarantee_claim` | لا |
| 66 | `_claim; settle_guarantee_claim` | `_claim; settle_guarantee_claim` | لا |
| 67 | `_claim; settle_guarantee_claim` | `_claim; settle_guarantee_claim` | لا |
| 68 | `_claim; settle_guarantee_claim` | `_claim; settle_guarantee_claim` | لا |
| 69 | `_claim; settle_guarantee_claim` | `_claim; settle_guarantee_claim` | لا |
| 70 | `_new_project; _add_active_contract` | `_new_project; _add_active_contract` | لا |
| 71 | `_new_project; _add_active_contract; daily_engine.run_day` | `_new_project; _add_active_contract; daily_engine.run_day` | لا |
| 72 | `_new_project; _add_active_contract; daily_engine.run_day` | `_new_project; _add_active_contract; daily_engine.run_day` | لا |
| 73 | `_new_project; _add_active_contract; daily_engine._m3` | `_new_project; _add_active_contract; daily_engine._m3(project, current_date)` | لا |
| 74 | `_new_project; _add_active_contract; daily_engine._m3` | `_new_project; _add_active_contract; daily_engine._m3(project, current_date)` | لا |
| 75 | `_new_project; _add_active_contract; daily_engine._m3` | `_new_project; _add_active_contract; daily_engine._m3(project, current_date)` | لا |
| 76 | `_source_text` | `_source_text` | لا |
| 77 | `_new_project; _add_active_contract; daily_engine._m3` | `_new_project; _add_active_contract; daily_engine._m3(project, current_date); p.contracts.values` | لا |
| 78 | `_new_project; _add_active_contract; daily_engine.__dict__.get` | `state_machine.TRANSITION_TABLE` | لا |
| 79 | `_new_project; daily_engine._m2` | `_new_project; daily_engine._m2(project, current_date)` | لا |
| 80 | `_new_project; daily_engine._m2` | `_new_project; daily_engine._m2(project, current_date)` | لا |
| 81 | `_new_project; _mark_all_initial_owned; closure_preconditions_met` | `_new_project; _mark_all_initial_owned; closure_preconditions_met` | لا |
| 82 | `_new_project; daily_engine._m2` | `_new_project; daily_engine._m2(project, current_date)` | لا |
| 83 | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | لا |
| 84 | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | لا |
| 85 | `_new_project; _mark_all_initial_owned; closure_preconditions_met` | `_new_project; _mark_all_initial_owned; closure_preconditions_met` | لا |
| 86 | `_new_project; _mark_all_initial_owned; _add_active_contract; closure_preconditions_met` | `_new_project; _mark_all_initial_owned; _add_active_contract; closure_preconditions_met` | لا |
| 87 | `_new_project; _mark_all_initial_owned; _add_active_contract; closure_preconditions_met` | `_new_project; _mark_all_initial_owned; _add_active_contract; closure_preconditions_met` | لا |
| 88 | `_new_project; _mark_all_initial_owned; closure_preconditions_met` | `_new_project; _mark_all_initial_owned; closure_preconditions_met` | لا |
| 89 | `_new_project; _mark_all_initial_owned; execute_dynamic_closure` | `invoke_closure_and_get_state(project, current_date, recovery_rate_pct)` | لا |
| 90 | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | لا |
| 91 | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | لا |
| 92 | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | لا |
| 93 | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | لا |
| 94 | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | `_new_project; _mark_all_initial_owned; _add_active_contract; daily_engine.run_day` | لا |
| 95 | `_new_project; _mark_all_initial_owned; create_guarantee_claim; p.guarantee_claims.append; execute_dynamic_closure` | `_new_project; _mark_all_initial_owned; create_guarantee_claim; p.guarantee_claims.append; invoke_closure_and_get_state` | لا |
| 96 | `_new_project; _mark_all_initial_owned; execute_dynamic_closure` | `_new_project; _mark_all_initial_owned; execute_dynamic_closure(project, current_date, recovery_rate_pct)` | لا |
| 97 | `_new_project; _mark_all_initial_owned; create_guarantee_claim; p.guarantee_claims.append; execute_dynamic_closure` | `_new_project; _mark_all_initial_owned; create_guarantee_claim; p.guarantee_claims.append; execute_dynamic_closure(project, current_date, recovery_rate_pct)` | لا |
| 98 | `_new_project; _mark_all_initial_owned; _add_active_contract; execute_dynamic_closure` | `_new_project; _mark_all_initial_owned; _add_active_contract; execute_dynamic_closure(project, current_date, recovery_rate_pct)` | لا |
| 99 | `_new_project; _mark_all_initial_owned; execute_dynamic_closure; daily_engine.run_day` | `_new_project; _mark_all_initial_owned; execute_dynamic_closure(project, current_date, recovery_rate_pct); daily_engine.run_day` | لا |
| 100 | `_new_project; daily_engine.run_deterministic_trial` | `_new_project; daily_engine.run_deterministic_trial` | لا |
| 101 | `_deterministic_trial_cached; balance_sheet_snapshot` | `_deterministic_trial_cached; balance_sheet_snapshot` | لا |
| 102 | `Project; initialize_accounting; balance_sheet_snapshot` | `Project; initialize_accounting; balance_sheet_snapshot` | لا |
| 103 | `_deterministic_trial_cached` | `_deterministic_trial_cached` | لا |
| 104 | `_deterministic_trial_cached; append; byyear.setdefault; byyear.values` | `_deterministic_trial_cached; append; byyear.setdefault; byyear.values` | لا |
| 105 | `_deterministic_trial_cached; balance_sheet_snapshot` | `_deterministic_trial_cached; balance_sheet_snapshot` | لا |
| 106 | `_deterministic_trial_cached` | `_deterministic_trial_cached` | لا |
| 107 | `_deterministic_trial_cached` | `_deterministic_trial_cached` | لا |
| 108 | `_deterministic_trial_cached` | `_deterministic_trial_cached` | لا |
| 109 | `_deterministic_trial_cached` | `_deterministic_trial_cached` | لا |
| 110 | `_deterministic_trial_cached` | `_deterministic_trial_cached` | لا |
| 111 | `Project; initialize_accounting; accrue_rent; collect_from_ar` | `Project; initialize_accounting; Contract; accrue_rent(project, contract, amount); collect_from_ar(project, amount)` | لا |
| 112 | `Project; initialize_accounting; settle_guarantee_accounting; refresh_profit` | `Project; initialize_accounting; settle_guarantee_accounting; refresh_profit` | لا |
| 113 | `Project; initialize_accounting; refresh_profit` | `Project; initialize_accounting; refresh_profit` | لا |
| 114 | `_new_project; Bike; p.bikes.append; daily_engine._m2` | `_new_project; Bike; p.bikes.append; daily_engine._m2(project, current_date)` | لا |
| 115 | `read_text` | `read_text` | لا |
| 116 | `Project; initialize_accounting; Bike; p.bikes.append; apply_ownership_writeoff; record_asset_writeoff` | `apply_ownership_writeoff(gross_cost, accumulated_depreciation) + apply project_accumulated_depreciation_delta once` | لا |
| 117 | `_source_text; text.lower` | `_source_text; text.lower` | لا |
| 118 | `_source_text` | `_source_text` | لا |
| 119 | `_new_project` | `_new_project` | لا |
| 120 | `_new_project; final_entitlements` | `_new_project; final_entitlements(project)` | لا |
| 121 | `_new_project; final_entitlements` | `_new_project; final_entitlements(project)` | لا |
| 122 | `_source_text` | `_source_text` | لا |
| 123 | `balance_sheet_snapshot; _new_project` | `balance_sheet_snapshot; _new_project` | لا |
| 124 | `_new_project; final_entitlements` | `_new_project; final_entitlements(project)` | لا |
| 125 | `_deterministic_trial_cached` | `_deterministic_trial_cached` | لا |
| 126 | `derive_seed; rng_draw` | `derive_seed; rng_draw` | لا |
| 127 | `json.loads; read_text` | `pytest.mark.skip; json.loads; read_text` | لا |
| 128 | `derive_seed` | `derive_seed` | لا |
| 129 | `rng_draw; derive_seed` | `rng_draw; derive_seed` | لا |
| 130 | `Contract; AssertionError; apply_friday_fee_and_oil` | `Contract; AssertionError; apply_friday_fee_and_oil(delivery_date, current_date, friday_counter, in_tenant_possession)` | لا |
| 131 | `_claim; AssertionError; settle_guarantee_claim` | `_claim; AssertionError; settle_guarantee_claim` | لا |
| 132 | `derive_seed` | `derive_seed` | لا |
| 133 | `_new_project; _add_active_contract; daily_engine.run_day` | `_new_project; _add_active_contract; daily_engine.run_day` | لا |
| 134 | `_new_project` | `_new_project` | لا |
| 135 | `daily_engine._m1` | `dateutils.is_business_day` | لا |
| 136 | `derive_state_from_balance` | `derive_state_from_balance` | لا |
| 137 | `Contract; apply_ordinary_collection` | `Contract; apply_ordinary_collection(total_due, total_paid, daily_rate, success, current_date)` | لا |
| 138 | `_new_project; _add_active_contract; daily_engine.run_day` | `_new_project; _add_active_contract; daily_engine.run_day` | لا |
| 139 | `_claim; settle_guarantee_claim` | `_claim; settle_guarantee_claim` | لا |
| 140 | `_claim; settle_guarantee_claim` | `_claim; settle_guarantee_claim` | لا |
| 141 | `_new_project; _add_active_contract; daily_rate_for_contract; globals` | `_new_project; _add_active_contract; daily_rate_for_contract; globals` | لا |
| 142 | `_new_project; _add_active_contract; daily_engine.run_day` | `_new_project; _add_active_contract; daily_engine.run_day` | لا |
| 143 | `_new_project; _add_active_contract; daily_engine.run_day` | `_new_project; _add_active_contract; daily_engine.run_day` | لا |
| 144 | `_new_project; _add_active_contract; daily_engine._receivable; apply_legacy_debt_collection` | `_new_receivable(project, bike, contract, 800) + apply_legacy_debt_collection(800, True)` | لا |
| 145 | `_new_project; _add_active_contract; daily_engine._m13` | `_new_project; _add_active_contract; daily_engine._m13(project, current_date)` | لا |
| 146 | `_source_text` | `_source_text` | لا |
| 147 | `_new_project; daily_engine._m2` | `_new_project; daily_engine._m2(project, current_date)` | لا |
| 148 | `Contract; apply_friday_fee_and_oil` | `Contract; apply_friday_fee_and_oil(delivery_date, current_date, friday_counter, in_tenant_possession)` | لا |
| 149 | `—` | `—` | لا |
| 150 | `_claim; settle_guarantee_claim; pytest.raises` | `_claim; settle_guarantee_claim; pytest.raises` | لا |
| 151 | `derive_seed` | `derive_seed` | لا |
| 152 | `_claim` | `_claim` | لا |
| 153 | `_source_text` | `_source_text` | لا |
| 154 | `_new_project; _mark_all_initial_owned; _add_active_contract; closure_preconditions_met` | `_new_project; _mark_all_initial_owned; _add_active_contract; closure_preconditions_met` | لا |
| 155 | `read_text` | `read_text` | لا |
| 156 | `_source_text` | `_source_text` | لا |
| 157 | `_source_text` | `_source_text` | لا |
| 158 | `read_text` | `pytest.mark.skip; read_text` | لا |
| 159 | `json.loads; select_representative_trials; read_text; TrialResult` | `pytest.mark.skip; json.loads; select_representative_trials; read_text; TrialResult` | لا |
| 160 | `json.loads; read_text; exists` | `pytest.mark.skip; json.loads; read_text; exists` | لا |
| 161 | `json.loads; read_text; date.fromisoformat; isoformat` | `pytest.mark.skip; json.loads; read_text; date.fromisoformat; isoformat` | لا |
| 162 | `_new_project; _mark_all_initial_owned; closure_preconditions_met` | `_new_project; _mark_all_initial_owned; closure_preconditions_met` | لا |
| 163 | `_new_project; _mark_all_initial_owned; create_guarantee_claim; p.guarantee_claims.append; execute_dynamic_closure` | `_new_project; _mark_all_initial_owned; create_guarantee_claim; p.guarantee_claims.append; invoke_closure_and_get_state` | لا |