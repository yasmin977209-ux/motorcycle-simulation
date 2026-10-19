# CP-R4 — إصلاح كشف الدفعات الدائمة قبل ترحيل Artifact تاريخي — 2026-10-19

## الحالة والنطاق
**R4 مسجل قبل تعديل المرشح.** المراجعة الساكنة وجدت أن مسار الاستعادة الدائمة الجديد يستخدم Git Trees API داخل `StateStore._block_listing` مع رفض أي نتيجة `truncated=true`، لكن خطوة shell الأقدم التي تقرر هل توجد دفعات دائمة ما زالت تستخدم Contents API لإحصاء `stage7-blocks`، وتخفي أخطاء الطلب بـ`|| true`. المطلوب توحيد قرار «هل توجد دفعات دائمة؟» مع inventory الذي تم تدقيقه واختباره بالفعل.

## الهوية الحية وقت R4
- `main` HEAD: `647c19826b90d8224ce73ef9b90c306a45e03fb0`.
- `main/state.json` blob: `2178260bb18efeb81437486f13b6d10cf5e85936`; الحالة `12-CLOSED / FINAL_DELIVERY_BLOCKERS_OPEN`.
- Candidate branch: `tmp/cp-stage7-timeout-parallelism-20261019`.
- Candidate HEAD الموثق من Run authoring الناجح: `09e66f203915609e3e5a199a11be6a1be890b1d6`.
- Candidate Workflow blob: `514aff8bbde36e961f077469989b1245dff52c51`.
- Candidate tests blob: `be167bb8ea12e3f8f0bccb97c03996e1180e6105`.
- Workflow authoring-only Run سابق: `39178436432`, tested SHA `09e66f203915609e3e5a199a11be6a1be890b1d6`, نتيجته `success`, و`78 passed in 0.64s`. هذا دليل سابق قبل التغيير المخطط في هذا التقرير ولا يختبر التغيير الجديد.

## R4 — العنصر والحكم
| العنصر | الوضع الحالي | المرجع/القرار والفرع | النص/الدليل الحاكم | الحكم |
|---|---|---|---|---|
| خطوة `Restore previous scenario block artifacts when available` في `.github/workflows/stage7-full-run.yml` على المرشح | `gh api .../contents/stage7-blocks?ref=...`، ثم `2>/dev/null || true`، ثم `jq` يفسر أي رد غير مصفوفة على أنه عدد عناصر صفر. | تفويض المالك لنطاق `CP-R4-TIMEOUT-PARALLELISM-FAIL-CLOSED` على فرع مرشح فقط؛ لا تغيير `main` أو الهوية الإحصائية/البيانات أو تشغيل Workflow إنتاجي. لا تُستنتج قاعدة أعمال من هذا الفحص. | نفس الملف المرشح يذكر في `StateStore._block_listing` أن Contents API لا يصلح لجرد كل العناصر عند حد 1,000، ويستخدم `git/trees/{tree_sha}?recursive=1` ويرفض `truncated=true`. أما خطوة shell فتظل على المسار القديم وتخفي خطأ الـAPI. | `K_CODE`: مسارا القرار مختلفان. عند كِبر دليل الدفعات، قد يُفسَّر فشل الجرد بأنه «لا توجد دفعات» فتبدأ محاولة استرجاع Artifact تاريخي رغم وجود الدفعات الدائمة. هذا لا يثبت تلف بيانات؛ المسار اللاحق يفترض أن يفشل مغلقًا عند اختلاف المحتوى/الهوية، لكن fallback غير لازم ويمكنه إحداث فشل استعادة زائف أو عمل تنزيل زائد. |
| الإصلاح الأدنى المقترح | استبدال جرد Contents API باستدعاء read-only لـ`StateStore._block_listing()` من خطوة Python نفسها؛ تمرير المستودع/الفرع/الرمز عبر متغيرات البيئة؛ ترك الاستثناءات (ومنها الشجرة المبتورة أو تعذر API) تفشل الخطوة بدل تحويلها إلى صفر. | ضمن إصلاح دوام/استعادة Stage 7 نفسه؛ المرشح فقط. | يوجد اختبار سابق لـ1,105 مدخلات واختبار يثبت رفض Git Tree مبتور في `tests/test_stage7_authoring.py`. | يسمح هذا بإعادة استخدام كود الجرد الواحد الذي يخدم restore الفعلي، بدل إنشاء تنفيذ متوازٍ. |
| الاختبار | عقد verifier يفحص الـWorkflow واختبارات Stage 7 الثابتة؛ التغيير الجديد لم يُختبر بعد. | أي تعديل اختبار/Workflow لا بد أن يبقى ضمن R4 والموافقة المحددة لـCP-R4. | القبول يتطلب اختبار عقد يثبت أن كشف الدفعات لا يستعمل Contents API وأنه يستدعي inventory الموثوق، ثم تشغيل authoring-only verifier على exact HEAD الجديد. | `PENDING_VERIFICATION` إلى أن تتاح نتيجة Run exact-SHA. |

## معايير القبول وحدود التنفيذ
1. يتطابق فحص وجود الدفعات الدائمة مع `StateStore._block_listing`؛ لا يُحوّل فشل/تقطيع Git Tree إلى عدد صفر.
2. تبقى الترحيلات التاريخية خاضعة لفحوص مصدر/seed/run/workflow الموجودة، ولا يعاد استخدام أي Trial مكتمل.
3. ينجح الـauthoring verifier على الـSHA الجديد بالضبط؛ لا يكفي نجاح سابق على SHA آخر.
4. لا تشغيل لـ`stage7-full-run.yml` ولا Monte Carlo/CLI/Trial/Checkpoint، ولا تعديل `main` أو `state.json` أو SOURCE_SHA أو master_seed/RNG أو سياسة sampling/cohort/Trial IDs أو البيانات التاريخية/Parquet؛ لا دمج/إغلاق PR أو Release.
5. يظل المشروع `PARTIAL / NOT_READY_TO_MERGE` حتى اجتياز البوابات كاملةً.

