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

## R4 addendum — Bash heredoc indentation found during candidate read-back, before correction

**Observed current candidate:** `7f9c32ba0442ebaca8bd47e37e0076f324864002`; Workflow blob `144227494ffc699e08c54d5b61f7a84c70b0c0e8`. This change has not been proven by runtime execution.

| العنصر | الوضع الحالي | المرجع/القرار | الحكم |
|---|---|---|---|
| Python heredoc داخل خطوة كشف الدفعات الدائمة | قراءة YAML المصدر تظهر أن `python - <<'PY'` ومتن الكتلة وعلامة الإغلاق بها مسافات بادئة أكثر من خط الأساس لمحتوى `run: |`. بعد إزالة YAML indentation، تبقى المسافات الزائدة داخل shell script؛ وقد لا تُطابق علامة إغلاق heredoc كما يتطلبها Bash، كما يتلقى Python تعبيرات المستوى الأعلى بمسافة بادئة غير صالحة. | نفس التفويض المحدد لـCP-R4، على candidate فقط، مع R4 وتحقق exact-SHA قبل اعتبار الإصلاح صالحًا. | `K_CODE` — عيب بنيوي في تعديل المرشح نفسه مثبت بالقراءة، لا بنتيجة تشغيل. لا ندعي حدوث خطأ runtime لأن لا سجل تنفيذ متاح للـSHA الحالي. |
| أقل إصلاح | إزالة المسافات البادئة الزائدة من سطر `python - <<'PY'` ومن متن Python وعلامة `PY` حتى تبدأ علامة الإغلاق في أول العمود بعد معالجة YAML؛ ثم إعادة قراءة المقطع الكامل للتحقق من الإزاحة. | لا تغيير للمنطق أو البيانات. | نفّذ قبل تشغيل authoring verifier جديد. |

## Read-back disposition after the R4 edits — 2026-10-19

**Candidate now read back:** `tmp/cp-stage7-timeout-parallelism-20261019` at `2a127d78422236471ff233f2bf30e99437106570`; compare with `main` is ahead 48 / behind 0; the five changed paths remain the two Stage 7 Workflows, block runner, state module and authoring tests.

- `.github/workflows/stage7-full-run.yml` blob `b686004505f57e123708ce2d0aacce38b3d5033e`.
- `tests/test_stage7_authoring.py` blob `c0aff73f0ff05058e44975ffac86382612d3adfd`; 79 test functions. New static test `test_stage7_legacy_restore_detection_uses_complete_durable_tree_inventory` requires the legacy-detection step to call `store._block_listing()`, forbids the old `contents/stage7-blocks?ref=` listing, and checks the recursive Git-tree and `truncated` guards.
- `scripts/stage7_state.py` remains blob `5615178a40200dec90247b6ddae63cd93c07126f`; its recursive inventory rejects GitHub's `truncated=true`. Read-back confirms the legacy-detection step now invokes that same inventory, its Python heredoc delimiter and body align with the YAML `run: |` baseline after YAML indentation is removed, and all of the original shell commands after `PREVIOUS_RUN_ID` are byte-for-byte unchanged. Source outside the replaced detection preamble and after the step is unchanged from prior candidate SHA `09e66f203915609e3e5a199a11be6a1be890b1d6`.

**Verification limit:** after the candidate push at `2a127d78422236471ff233f2bf30e99437106570`, the connected workflow-run lookup returned zero runs and combined status returned an empty list; its documented wrapper filters PR-triggered runs, while direct Actions/checks pages returned Cache miss. This is **not** evidence that no run occurred. No verified run ID, artifact ID or tested SHA exists yet for this latest change. Thus `PASS` is not claimed: `tested_sha=null`, `run_id=NONE_VERIFIED`, `artifact_id=NONE_VERIFIED`, status `READ_BACK_PARTIAL / AUTHORING_RUN_UNVERIFIED`.

No production Workflow was executed, and the candidate `stage7-full-run.yml` trigger still targets only `tmp/stage7-full-run-20261004`, not this candidate branch. No CLI, Monte Carlo, Trial, Checkpoint, seed/RNG, source pin, cohort/policy, historic data, `main`, or main `state.json` was modified. No PR was merged/closed and no Release was created.

**Next allowed action:** retrieve the push-triggered authoring verifier run for exact HEAD `2a127d78422236471ff233f2bf30e99437106570` from a GitHub Actions view that lists push events; inspect every step before calling the updated candidate test PASS. Continue independent non-production review meanwhile; do not merge or trigger simulation.

## R4 — repair stale authoring assertion after durable-tree refactor — 2026-10-19

### Exact failing evidence
- Workflow Run: [39187134699](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39187134699)
- Event `push`; branch `tmp/cp-stage7-timeout-parallelism-20261019`; exact tested SHA `2a127d78422236471ff233f2bf30e99437106570`.
- Job `verify` ID `117851821706`, conclusion `failure`; AST parse and YAML lint succeeded before the test step.
- Exact result: `1 failed, 78 passed in 0.62s`.
- Literal failing assertion: `assert "contents/stage7-blocks?ref=${STATE_BRANCH}" in restore` at `tests/test_stage7_authoring.py:705`.
- The step was intentionally refactored to `store._block_listing()`; therefore the test was asserting an obsolete implementation detail, not a required behavior. The earlier new contract test already checks the shared inventory and refuses the Contents API listing.

### R4 before edit

| Element | Current | Governing decision / branch | Exact evidence | Ruling |
|---|---|---|---|---|
| `test_stage7_restore_prefers_durable_blocks_and_proves_legacy_artifact_identity` | It requires the old `contents/stage7-blocks?ref=...` token even though the candidate now calls `store._block_listing()`. | Owner-authorized candidate-only CP-R4 durable persistence/restore/fail-closed scope; branch `tmp/cp-stage7-timeout-parallelism-20261019`. The newly accepted implementation uses the recursive Git Trees API and raises on `truncated=true`. | Run 39187134699, tested SHA `2a127d78422236471ff233f2bf30e99437106570`, exact AssertionError/result above. | `K_TEST`: stale source-text assertion. Change only the assertion to require `store._block_listing()` and forbid the old Contents inventory; preserve all following checks of run provenance, artifact source, seed/source workflow identity, and fail-closed legacy proof. |
| Acceptance | Current tree/truncation guard is tested separately, but whole focused suite fails on this stale assertion. | Same CP-R4 scope. | Exact candidate-head authoring Workflow must complete all steps. | `PENDING_VERIFICATION` until a new push-run confirms the corrected candidate SHA. |

No business logic, model source, Workflow, seed/RNG, sampling/cohort/trial IDs, historical data, main, state, reference, or production output changes are needed for this test-only repair. No production workflow may be triggered.

## Exact-SHA revalidation and test-only repair — latest 2026-10-19

The earlier run-status statement above has been superseded by the newly available GitHub Actions run inventory:
- Run `39187134699`, branch `tmp/cp-stage7-timeout-parallelism-20261019`, exact tested SHA `2a127d78422236471ff233f2bf30e99437106570`, event `push`.
- Job `verify` ID `117851821706`, outcome `failure`. AST parsing and YAML lint passed; test output was exactly `1 failed, 78 passed in 0.62s`.
- Literal failure was the obsolete assertion at `tests/test_stage7_authoring.py:705`: `assert "contents/stage7-blocks?ref=${STATE_BRANCH}" in restore`. The candidate intentionally replaced that inventory with `store._block_listing()`; hence the classification is `K_TEST`, not a runtime failure in the new tree inventory.

R4 for this correction was recorded above before editing tests. On candidate-only branch, changed only `test_stage7_restore_prefers_durable_blocks_and_proves_legacy_artifact_identity` to require `store._block_listing()` and assert the legacy Contents listing is absent, retaining its existing assertions for the historical artifact/run identity proof, source/seed Workflow proof and fail-closed migration. Candidate tests blob is now `4afba1c7c66a60560bbe148cd503c38a67b9c4dd`, with 79 test functions; candidate HEAD is `12a30e69c1fd406683ba97cc824c9d27b9fce918`. The Stage 7 full-run Workflow blob remains `b686004505f57e123708ce2d0aacce38b3d5033e`; state module blob remains `5615178a40200dec90247b6ddae63cd93c07126f`.

A new authoring-only push run is visible: `39188323789`, exact head `12a30e69c1fd406683ba97cc824c9d27b9fce918`, status `in_progress` at the one permitted inspection. Per M4, this running Run is not polled further in this session; no conclusion is available yet. Do not label it PASS or infer its final result. No artifact has been inspected or produced for this Run.

No Stage 7 production workflow, CLI, Monte Carlo, Trial, Checkpoint, source/seed/RNG/sampling/cohort/history data change, main/state/reference edit, merge, PR closure or Release occurred within this CP. Candidate remains `PARTIAL / AUTHORING_VERIFICATION_IN_PROGRESS / NOT_READY_TO_MERGE` until a completed exact-head result is available.

