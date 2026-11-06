# PROJECT_DECISION_QUALITY_AND_EVIDENCE_HARDENING_PLAN_v1.0

**التاريخ المرجعي:** 2026-11-06  
**قرار المالك:** OWNER-DECISION-HARDENING-AND-D3-TO-D6-EXECUTION-2026-11-06  
**المستودع:** yasmin977209-ux/motorcycle-simulation  
**الفرع:** tmp/d1-rebuild-20261101  
**التصنيف:** خطة حوكمة وجودة أدلة — لا تغيّر قواعد الأعمال أو هوية التجارب أو العتبات.

> ملاحظة مصدرية: أُنشئ هذا النص من بنود قرار المالك الحي وREV6 المتحقق منهما. لم يظهر في HEAD السابق ملف مستقل يحمل هذا المسار؛ لذلك لا أدّعي استعادة نسخة سابقة غير موجودة في GitHub.

## 1. الهدف الحاكم
رفع جودة القرار الهندسي من «نجاح أداة/اختبار» إلى سلسلة إثبات قابلة لإعادة الفحص، مع فصل حقيقة الحساب عن المخرج المعياري، وفصل نجاح النطاق عن إغلاق المرحلة، والحفاظ على الأدلة التاريخية Append-only.

## 2. التحسينات العشرة المعتمدة

1. **تثبيت السلطة والهوية:** تسجيل current_governing_reference_sha256 منفصلاً عن historical_execution_reference_sha256، وربط كل تنفيذ بـCommit SHA وtested SHA وArtifact ID الدقيق.
2. **فصل الحقيقة الحسابية عن المخرج:** اعتماد CANONICAL_D3_D5_FULL_WORKBOOK_OUTPUTS للمصنفين الكاملين، مع إبقاء UPSTREAM_COMPUTATIONAL_TRUTH للمرجع v2.4.0 والبيانات المصدرية وresults/number_registry.json.
3. **توحيد نطاق D3 المعياري:** اعتماد حدود 105 مفاتيح/125 تعييناً تمثيلياً لـFull Logging، و25 حالة P50 تفصيلية، وإحصاءات 48K في أوراق الإحصاءات والتوزيع اليومي؛ وعدم تحويل هذه الحدود التصميمية إلى فجوات مصطنعة.
4. **تسوية تعارض الهوية Append-only:** تصنيف شجرة Git الأصغر HISTORICAL_COMPACT_GIT_TREE_SUBSET، وإغلاق تعارض هوية المصنف بقرار المالك دون حذف أو استبدال أي أثر تاريخي.
5. **سلسلة إثبات موحدة:** فرض Requirement → Source Identity → Implementation → Test Evidence → Output Evidence → Independent Audit → Retention Evidence → Exact Final HEAD لكل متطلب.
6. **حالة D3 فعالة مستقلة:** إنشاء D3_EFFECTIVE_CLOSURE_STATE_2026-11-06.json وملف Markdown يدمجان التصحيحات والقرارات فوق D3_BUILD_AUDIT.json وD3_MANIFEST.json دون تعديلهما.
7. **جسر تشفيري ثلاثي:** حساب SHA-256 وQuickXorHash وDropbox content_hash من البايتات الخام نفسها، ومقارنة القيم المحسوبة ببيانات OneDrive Graph وDropbox وGitHub Artifact Digest.
8. **نقل مدفوع بالـManifest واستعادة فعلية:** التحقق من أحجام الأجزاء وبصماتها وتغطية الفهارس، ثم إعادة التجميع ومطابقة SHA-256، وzipfile.testzip()، وفحص الأعضاء وفتح المصنفات والمستندات.
9. **Lineage لكل ظهور رقمي في D4:** اعتماد فحص occurrence-level عبر عناصر OOXML الخمسة، وتصنيف كل token إلى الفئات العشر، وإثبات صفر Unresolved قبل نجاح Test 176.
10. **استقلال D5/D6 والتوثيق:** إعادة فحص ما بعد النشر بواسطة مدقق مستقل عن Builder/Publisher، وتشغيل الاختبارات الثمانية المطلوبة فعلياً على Exact HEAD، وتسجيل Test ID / Run ID / Job ID / Tested SHA / Result ثم إكمال Raw readback والاستمرارية.

## 3. قاعدة المطابقة المعيارية للنطاق — v2.4.0 مقابل REV6
قرار المالك يحكم تفسير نطاق D3/D5 في تسليم T2_INTERIM:
- REPRESENTATIVE_CASES: 125 تعيين دور و105 مفاتيح فريدة.
- الأوراق التفصيلية الست لكل سيناريو: حالة P50 واحدة لكل واحد من 25 سيناريو.
- إحصاءات كل التكرارات والتوزيع اليومي: في أوراق _STATS وDAILY_DISTRIBUTION، لا في دفاتر تفصيلية ضخمة لكل تكرار.
- خلايا C100 الخمس: CROSS_COHORT_DETERMINISTIC_REUSE وفق Artifact 12630457193؛ لا تشغيل Golden جديد في تسليم T2_INTERIM.

هذه المواءمة لا تمحو القيود التالية ولا ترقيها:
- Full Logging لا يتجاوز 105 مفاتيح تمثيلية.
- C100 Golden revalidation يظل NOT_RUN في سجل القيود المستقبلية.
- الحقول الخمسة التاريخية تبقى MISSING_EVIDENCE ولا تُخمّن ولا تُصفّر.
- Financial Gate A = PASS_SCOPED، Production Gate A = NOT_DECLARED.
- Gate B عند N=2400 = FAIL_SCOPED (10/10)؛ Stability = NOT_CONVERGED (0/60)؛ N=4800 = NOT_EXECUTED.

## 4. بوابات التنفيذ
1. تثبيت Effective D3 closure مع الأدلة الحية.
2. استكمال Global Preservation Gate، بما فيه البايتات الخام والنسختان الدائمتان المستقلتان واختبار الاستعادة.
3. لا يبدأ D4 قبل D3 PASS_GAP_FREE واجتياز شرط الحفظ المطلوب.
4. لا يبدأ D5 قبل D4 PASS_GAP_FREE.
5. لا يبدأ D6 قبل D5، ويجب أن يكون Independent Post-Write Audit.
6. لا تُشغّل Trials أو Simulation أو Monte Carlo أو N expansion، ولا تغيّر SOURCE_SHA أو cohort_id أو MASTER_SEED.
7. لا تعديل لـmain، ولا دمج أو Force-push أو Release.

## 5. معيار النجاح
لا يُستخدم PASS_GAP_FREE إلا إذا اجتازت جميع المتطلبات الإلزامية الاختبارات الفعلية، وتطابقت البصمات والأحجام والهويات، ولم يبق NOT_RUN أو MISSING_EVIDENCE أو CONFLICTED ضمن نطاق المرحلة، واكتمل الاحتفاظ والاستعادة وفق REV6، وتم التحقق من Exact Final HEAD. وإلا فالحالة BLOCKED أو PASS_SCOPED بحسب الدليل، دون ترقية شكلية.

## 6. ملفات التنفيذ المرتبطة
- docs/stage_d/D3_EFFECTIVE_CLOSURE_STATE_2026-11-06.json
- docs/stage_d/D3_EFFECTIVE_CLOSURE_STATE_2026-11-06.md
- scripts/verify_tri_hash_preservation_bridge.py
- scripts/quickxorhash.c
- .github/workflows/tri-hash-preservation-verification.yml
- tests/test_tri_hash_preservation_bridge.py

**تنبيه تشغيلي:** يتطلب Workflow سرّي GitHub Actions باسم ONEDRIVE_GRAPH_ACCESS_TOKEN وDROPBOX_ACCESS_TOKEN بصلاحية قراءة فقط. لا تُكتب قيم الأسرار في المستودع أو سجلات Actions.
