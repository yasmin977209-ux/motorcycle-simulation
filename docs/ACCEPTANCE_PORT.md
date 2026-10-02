# ACCEPTANCE_PORT.md

- مصدر الاختبارات الأصلي: SHA-256 `7a6d9672ca386f070367382f0117311966fba51ff7f07e9bc7a1561bc902766f` (793 سطراً، 163 اختباراً).
- المرجع البرمجي لواجهات المواءمة: `a2b0a1713cfd9811e5f00e210102abfb3af3e235`.
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
