# برومبت استئناف مشروع Motorcycle Simulation — 2026-11-07

انسخ النص التالي كاملاً إلى دردشة ChatGPT الجديدة المتصلة بمستودع GitHub:

---

أنت تستأنف مشروع Motorcycle Simulation من سجلات GitHub الحية، لا من الذاكرة وحدها. لا تبدأ من الصفر ولا تطلب مني إعادة رفع ملفات موجودة في المستودع أو Artifacts المتاحة.

## المستودع ونقطة الانطلاق
- Repository: `yasmin977209-ux/motorcycle-simulation`
- Working branch: `tmp/d1-rebuild-20261101`
- آخر HEAD موثق قبل تحديث التسليم هذا: `cd38117740c1577627fdebeb1ce9600019a5d338`
- Protected main آخر قيمة موثقة: `01a6f79eedc522bb734ed9c5ea31beee581f2468` — ممنوع الكتابة إليه.

## اقرأ هذه الملفات أولاً من الفرع الحي
1. `docs/PROJECT_CONTINUITY.md`
2. `docs/PROJECT_HANDOFF.md`
3. `docs/stage_d/SESSION_STATUS_2026-11-07_LIVE_REVALIDATION.md`
4. `docs/stage_d/CONTINUITY_HANDOFF_2026-11-07_LIVE_REVALIDATION.md`
5. `docs/stage_d/PRESERVATION_RECOVERY_STATUS_2026-11-07.md`
6. `docs/stage_d/SESSION_STATUS_2026-11-07_OWNER_DECISION_EXECUTION.md` مع قراءة التصحيح اللاحق في آخر الملف
7. `docs/stage_d/CONTINUITY_HANDOFF_2026-11-07_OWNER_DECISION_EXECUTION.md` مع قراءة التصحيح اللاحق في آخر الملف
8. `docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md`
9. `docs/governance/D-2026-10-30-REFERENCE-V2.4.0.md`
10. `docs/governance/OWNER_MASTER_BLOCKER_REMOVAL_2026-11-05.md`
11. `docs/stage_d/D3_EFFECTIVE_CLOSURE_STATE_2026-11-06.json` وملف MD المقابل
12. `docs/stage_d/D4_EFFECTIVE_CLOSURE_STATE_2026-11-07.json`
13. `.github/workflows/stage-d5-delivery-package.yml` و`.github/workflows/stage-d6-independent-audit.yml`
14. `.github/workflows/project-continuity-raw-readback.yml`

## تحقق حي قبل أي كتابة
أعد قراءة branch ref وmain ref، وآخر commits، وأحدث 100 Actions runs، وJobs/Steps/Artifacts الخاصة بـD3 وD4 وأي D5/D6 أحدث. لا تفترض أن اللقطة السابقة لا تزال حديثة. افحص PRs وReleases فقط بقدر ما يؤثر على صلاحية المتابعة. سجّل أي اختلاف قبل اتخاذ أي إجراء.

## الحالة الموثقة التي يجب إعادة التحقق منها
- Governing v2.4.0 معتمد بقرار `D-2026-10-30-REFERENCE-V2.4.0`، SHA-256 `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`، 401,397 bytes.
- D3: `PASS_GAP_FREE_NORMATIVE_V240_SCOPE` ضمن D3-01..D3-18 وD3-S1/S2؛ لا يعني قبول المشروع كله.
- Tri-hash Stage A: Run 42330906466 / Job 128276958747 / Artifact 13557202516 / SHA-256 `a785c6bc51f9427c9e728a94797829eb4cf83ab33fc6509e1e49a6a1044d3b25`.
- Stage B: 72/72 provider metadata matches؛ ليست provider raw-byte readback ولا restore proof.
- Global Preservation Gate مستقل وما زال BLOCKED قبل E3 بسبب E2 Replay 20 archives وإثبات two independent durable failure domains؛ لا يمنع D3/D4/D5/D6.
- D4: Run 42387025927 / Job 128446462610 / tested SHA `1fb4898480629c0a327dbff13792d455cd205a59`; D4 closure `PASS_GAP_FREE` في نطاقه، وbuild report `PASS_SCOPED_WITH_LIMITATIONS`; Test 176: 241 = 64 resolved + 177 classified + 0 unresolved.
- D4 Artifact 13579374315، 18,527 bytes، digest `sha256:0607b2974373739e51f0454f25e13138b4f50c54c02906cf57362cd37d46e4e2`.
- Branch HEAD بعد D4: `cd38117740c1577627fdebeb1ce9600019a5d338`; D1-D2 وD3 الأحدث اختبرا `1fb489...` وليس `cd381...`. D4 وحده نفذ Raw readback/exact-head في workflow الخاص به.
- D5/D6 الجديدان: NOT_RUN. Workflow files على فرع العمل فقط، ونسختاهما على main غير موجودتين حسب فحص 2026-11-07؛ لذلك لا تفترض أن workflow_dispatch متاح.
- لا تخلط D5/D6 التاريخيين مع السلسلة الجديدة.

## المهمة التالية
حل عائق تشغيل D5 على فرع العمل دون تعديل main. افحص trigger فعلياً من جديد. لا تغيّر D4 closure JSON شكلياً لتوليد push trigger، ولا تخترع API/dispatch workaround. إذا لم توجد آلية آمنة ومسموحة، توقف واطلب قرار المالك المحدد.

بعد نجاح D5:
1. تحقق من D5 package ZIP وmanifest وSHA256SUMS، والـ8 members، الأحجام والبصمات وCRC.
2. انشر D5 Artifact ثم نزّله مستقلاً بواسطة Artifact ID وتحقق من digest/size/inventory/CRC/كل payload bytes.
3. سجل Run ID وJob ID وtested SHA وArtifact ID وdigest وexpiry.
4. لا تبدأ D6 قبل D5 PASS_GAP_FREE.
5. نفذ D6 المستقل، مع إثبات الاختبارات 175 و176 و179 و180 و181 و182 و183 و186 كلٌّ على exact tested SHA؛ لا تكتفِ بوجود test names أو نتائج تاريخية.
6. تحقق من D5 artifact ومن independent post-write audit وسجل القيود.
7. أنشئ final atomic continuity commit بعد D6 فقط، ثم نفّذ Raw readback وD1-D2 وD3 وD4 وD5 وD6 على Exact Final HEAD. لا تستخدم tested SHA قديم لإثبات HEAD أحدث.

## القيود غير القابلة للتجاوز
- لا تعديل main ولا merge ولا force-push ولا Release.
- لا Trial ولا Simulation ولا Monte Carlo ولا N expansion (بما فيه N=4800).
- لا backfill ولا zero-fill ولا استنتاج للقيم المالية المفقودة.
- لا تغيير SOURCE_SHA أو cohort أو MASTER_SEED أو RNG أو trial IDs أو scenario identity.
- لا خلط S6 وC100.
- Gate B يبقى FAIL_SCOPED (10/10)، Stability NOT_CONVERGED (0/60)، N=4800 NOT_EXECUTED، Production Gate A NOT_DECLARED، والحقول الخمسة MISSING_EVIDENCE.
- لا تعلن FINAL_ACCEPTED أو P17/P18 أو CONVERGED.
- افصل D3/D4 عن Global Preservation Gate.
- لا تصف 72/72 metadata matches بأنها raw-byte readback.
- كل تحديث توثيقي Append-only؛ لا تمحُ الفشل أو السجل التاريخي.

## أسلوب التنفيذ
ابدأ بجدول baseline قصير: HEADs، D3، D4، D5/D6، preservation، القيود. لا تكتب قبل التحقق الحي. نفّذ خطوة واحدة في كل مرة. أعطني Run/Job/tested SHA/Artifact/digest لكل نتيجة، واذكر صراحةً ما لم يتم فحصه. لا تدّعِ نجاحاً دون دليل.

---
