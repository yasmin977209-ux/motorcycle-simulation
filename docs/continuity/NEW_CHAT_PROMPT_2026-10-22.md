# Prompt to resume in a new ChatGPT conversation

Copy the entire prompt below into a new chat inside the same ChatGPT Project.

---

أنت تعمل على مشروع «مهندس أسطول الدراجات — بوابة 163/185» في المستودع `yasmin977209-ux/motorcycle-simulation`. هدفك ليس كتابة تقارير فقط؛ بل مواصلة التنفيذ الهندسي المسموح حتى مطابقة المرجع، إغلاق البوابات، إنتاج ملفات التسليم السبعة، وإجراء تدقيق مستقل. لا تعلن اكتمالًا قبل أدلة القبول، ولا تنشئ Release دون إذن صريح منفصل.

## 1) ابدأ بالسلطة والمصادر الفعلية

1. اقرأ Project Sources وProject Instructions الفعلية في واجهة ChatGPT إن أمكن. لا تدّعِ أن تعليمات GitHub مطبّقة في إعدادات المشروع؛ إذا تعذّر الوصول، قل ذلك بوضوح واطلب من المالك التحقق اليدوي.
2. المرجع الحاكم هو النص الأصلي `المرجع_النهائي_الموحد_المعتمد.md` المضمّن داخل `المرجع النهائي الموحد المعتمد المدمج.md`. بصمة SHA-256 المعروفة/المعاد حسابها للبايتات الأصلية هي `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`. بصمة الملف المدمج مختلفة؛ القراءة المحلية في جلسة التسليم أعطت `c816e2b61734390e57500cab738829ae1810d0063f9b49bdf0d107344f867fd5`. المرجع الأصلي وحده يحكم قواعد الأعمال؛ التقارير والبرومبتات والكود أدلة مساعدة وليست سلطة.
3. تحقق حيًا من `main` HEAD و`state.json` و`docs/STATE_SHA_SEMANTICS.md` وسجل القرارات والتعديلات المرجعية، ثم PRs والفروع وRuns/Jobs/tested SHAs/Artifacts. لا تعتمد على أي SHA أدناه بوصفه حيًا دون إعادة قراءته.
4. اقرأ PR #46 وسجل الاستمرارية كاملاً من الرأس الحي: `docs/continuity/START_HERE.md`, `docs/PROJECT_CONTINUITY.md`, `docs/continuity/SESSION_OUTPUTS.jsonl`. PR #46 فرع توثيق/استمرارية، لا main ولا مصدر قواعد. تقرير التسليم `docs/continuity/HANDOFF_2026-10-22_FINAL_REVIEW.md` وسجل الإخراج `FINAL-REVIEW-HANDOFF-2026-10-22` أدلة مساعدة، وليسا بديلًا عن التحقق الحي.
5. إذا تغيرت الحالة منذ هذا التسليم، وثّق الفرق ولا تستنتج شيئًا من الذاكرة وحدها.

## 2) لقطة معروفة للتوجيه فقط — يجب إعادة التحقق منها

- آخر `main` HEAD شوهد في هذه المراجعة: `7621ddefe6c971e9eb231eb2a987519c86a2cb51`.
- `main/state.json` blob `0b7db78b2678aeea3f73f6114e69ab6802806fd3`; داخله `state.sha=0b083fa472d7a11089a15137cfad16d87785689a` و`sha_semantics=parent_state_commit_pointer`. لا تقارن `state.sha` بـHEAD كأنهما مطلوب أن يتطابقا.
- `main/docs/stage9a/dataset_manifest.json` blob `e796fa2443493b607f1f9c60b58eb63607959c26`.
- PR #46 كان OPEN/DRAFT/unmerged؛ رأسه تغيّر بعد تحديث سجل الاستمرارية، لذا اكتشف head/base حيًا.
- PR #48 Stage 7 Gate B guards merged؛ PR #55 restored pinned model-source identity merged؛ PR #56 Stage 7 workflow serialization/fail-closed checks merged. تحقق من الكود الحالي والـtested SHAs، ولا تعمم نجاح الاختبارات المركزة.
- PR #49 Stage 13 assembler OPEN/DRAFT. Run `39689589357` passed 55 focused synthetic/compatibility tests in 15.62s on SHA `0d5556eb77b9efcac3abf468654b9f4a8bf4ca81`, not necessarily current PR head. Full-suite Runs `39689267217`, `39689360855`, `39694421445`, `39695399707`, `39695670379` failed; failures include missing `results_stage5/` fixtures (main-based control reproduced four of them). Fetch latest logs and distinguish baseline fixture defects from new failures.
- PR #60 Stage 9C reconciliation, #61 MaxCase daily extraction, #62 C050_G000 provenance reconciliation were OPEN/DRAFT in the snapshot. PR #47 DAILY serialization was also OPEN/DRAFT. Recheck all PR metadata and exact code/test blobs.
- Releases endpoint returned no releases in this snapshot.
- Final delivery is `NOT_ACCEPTED`; Gate A is `BLOCKED`; Stage 13 production acceptance is `BLOCKED`; independent final audit is `NOT_ACCEPTED`; Release is `BLOCKED / NOT_AUTHORIZED`.

## 3) Non-negotiable permissions

- Owner has expressed broad continuing execution intent. Continue low-risk, permitted engineering on isolated candidate branches without asking for routine confirmation each time.
- This does NOT authorize main writes, reference changes, changing `SOURCE_SHA`, seed/RNG/sampling/cohort/trial IDs, historical data/Parquet, Golden coverage, production Monte Carlo/trials/checkpoints, tests/workflows changes without a fresh scoped R4 and specific approval, merging/closing PRs/deleting branches, final delivery acceptance, or Release.
- Never invent a business rule. Keep `UNDEFINED_BUSINESS_RULE/PENDING_APPROVAL` for Stage 11 topology and any other unresolved normative requirement; block only the affected path and continue independent work.
- Before any change, create R4: item/current state/reference+decision+branch/SHA/exact controlling text/defect class/minimal change/authority/acceptance criterion/risk. Do not change tests/workflows absent the required approval.
- Preserve failed historical evidence. Keep `VERIFIED`, `PASS_SCOPED`, `REPORTED_ONLY`, `MISSING_EVIDENCE`, `CONFLICTED`, `PENDING_APPROVAL`, `BLOCKED`, `PARTIAL`, `FAIL`, `NOT_ACCEPTED`, `NOT_AUTHORIZED` distinctions.

## 4) Critical blockers and first work

1. Gate A production provider/coverage/authority gap: exact fail-closed checks exist but production callers do not yet provide validated approved Golden provider identity and coverage. Do not claim Gate A PASS or extend production checkpoints until proven.
2. Source pin: `SOURCE_SHA=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`. PR #55 reportedly restored source identity; directly verify current source blob against pinned source before any dataset extension. Never change the pin to fit code.
3. Stage 11 topology is undefined. Do not invent topology.
4. Stage 13 assembler is absent from main at the snapshot. Candidate PR #49 proves only scoped synthetic behavior, not production output. Full suite is not green.
5. C050_G000 provenance conflict: main manifest references artifact `11503191706` associated with Run `37660610243`; artifact `11503510055` is associated with Run `37662891608`. Their `scenario_metadata.json` differs in `log_events`. PR #62 is only a proposal. Do not change canonical manifest or substitute IDs until an effective scoped decision and evidence reconcile this.
6. Partner1/Partner2 reinvestment daily memo balances are absent from the Stage 12 Parquet audit. Never fabricate from Cash/Equity or fill zero. Use canonical reference mapping only where explicitly defined (e.g., `Cumulative_Project_Profit=Final_Retained_Earnings` for matching timestamp per the reference).
7. Stage 9C historical overall status remains `PARTIAL` under D-2026-10-12-02 even though CP-D passed its narrower 500 exact comparisons. Do not upgrade to full PASS.
8. P16 cell `C030_G030_STATS!L3` value `13185720.000000002` was reproduced by NumPy float64 quantile on 450 integer Final_Cash values; exact rational linear P90 is 13,185,720 YER. No rounding/workbook patch is authorized; CP-D's 500-cell comparison is exact with no tolerance.
9. Stage 7 workflow hardening PR #56 merged; state.json timeout note may be stale. Verify live workflow and record any state/document conflict without changing state in this handoff.
10. The seven final deliverables are not accepted as one fully verified set. No independent final audit acceptance exists and no release is authorized.

**First permitted action:** conduct a read-only provenance/data-contract audit of PR #62's C050_G000 artifact/run evidence and PR #61's MaxCase daily payload for the missing partner memo balances; independently verify the current pinned model-source identity and the production Gate A caller/provider gap. Do not edit the canonical manifest or generate production outputs. Then choose the smallest independent R4-scoped fix that is authorized, branch-only, and verifiable.

## 5) Evidence and cohort distinctions

- Historical Stage 12 run `37964656154`: 11,005 trials, 22,546,465 daily rows, aggregate SHA-256 `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`, source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, seed 20270101.
- Stage 9A/P16 cohort is 9,005 TrialResult rows (5 C100 × 1 and 20 non-C100 × 450); do not confuse with Stage 12's 11,005.
- Gate B historic N=300/600/1200 had 60/60 CI points pass per checkpoint, but that is scoped evidence, not overall stability acceptance. Later C030_G030 1200→2400 passed scoped checks, while the 300→600 P90_Final_Cash transition failed strict <1% at 1.5715059334983579%. Reconcile full current stability rules and per-scenario coverage before any further checkpoint.
- Confidence Sequences remain pending owner decisions: financial mean assumptions, loss-probability precision criterion, alpha/IUT vs simultaneous coverage.
- P16 full provisional build Run `39635040311` produced provisional artifacts, not accepted delivery. Primary artifact `12363135623`, SHA-256 `7e2e821e8c1f8e13b37189638e9a975ac8fc8862ee349abce928fea0cd048ada`; sealed artifact `12363265619`, SHA-256 `b2bd6096b0b4b273e412cf2756d70c1f5e79bda19681cb39463ea867d3dd6a54`. A direct OOXML check disproved the claim that MaxCase trial_id cells were missing; daily payload/provenance/accounting fields remain incomplete.

## 6) Required final deliverables

Only after all blocking gates and cohort/source identity are resolved, build and independently inspect:
1. `النتائج_الكاملة_AR.xlsx`
2. `Full_Results_EN.xlsx`
3. `التقرير_الكامل_AR`
4. `Full_Report_EN`
5. `الملخص_AR`
6. `Summary_EN`
7. `دراسة_الجدوى_AR`

For every file, verify actual post-write bytes, SHA-256, size, source/cohort/source SHA, producer/tested SHA, Run/Artifact IDs. For workbooks verify exactly 185 sheets in correct order, all required ledgers, integer YER values, accounting balances and roll-forward, representative cases/daily payload, and numeric parity across Arabic/English reports and summaries. Then a separate auditor must reopen the files and score every criterion. Never use a synthetic workbook as evidence of production delivery.

## 7) Record and finish responsibly

Read the live continuity register before adding a new append-only event. Verify any write with a fresh read-back and commit/blob evidence. Do not merge PR #46 or alter main to make continuity appear official. Continue independent allowed work when another path is blocked. The release remains a separately protected action requiring explicit authorization.
