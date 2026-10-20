# CP — حسم MaxCase في V3 وتدقيق حقول Partner Balance في Stage 12 — 2026-10-21

**الحالة:** `MAXCASE_V3_VERIFIED / PARTNER_BALANCES_MISSING / PASS_SCOPED`.
**النطاق:** قراءة Artifact IDs موجودة وتحليل صفوف Parquet المخزنة فقط. لم تُشغّل محاكاة أو Trials أو CS ولم تُعدّل البيانات أو Parquet أو manifest.
**المرجع الأصلي:** SHA-256 `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`.

## 1. هوية التشغيل الذي نفذ الفحص

- Audit branch: `tmp/cp-v3-stage12-parquet-audit-20261021`.
- Audit tested SHA: `de347e90a36a6e2d19cb3da24b10fd3728d641e9`.
- Workflow Run: `39513482405`, Job: `118939926028`, conclusion `success`.
- [سجل التشغيل](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39513482405).
- Output Artifact: `12307560449`, `cp-v3-stage12-parquet-audit-39513482405`, 2,467 bytes, SHA-256 `360e1bc3ff2863cf7d80561e27df83fdfa418127405ded42d88e3897adc2c260`.
- أُعيد تنزيل Artifact وفتح JSON داخله؛ حقول الهوية والنتيجة أدناه مطابقة لمحتواه، لا لتقرير الإنشاء وحده.

## 2. حسم MaxCase من V3 ذاتها (450 trial)

- Artifact `11503510055`, Run `37662891608`, producer SHA `6128b22864bb171ba49ec15dbb42439a6513c30c`, المصدر الرسمي `37225915321`, source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`.
- ZIP: 17,787,110 bytes, SHA-256 `111eb7a2abd7b85625a02c55ee6f3140a14644ef253141bfdc3f8fc5ae4c287d`; API digest matches.
- `trial_results.parquet`: 450 rows read, 450 unique contiguous IDs 1–450; internal member SHA-256 `09c223d8348f93a5c5e9246a409614d6345a76b224ff65f865c6bdbaea5fbbe8`.
- `trial_fingerprints.json`: 450 IDs; member SHA-256 `82cb7a2725944edc3b749bcc722d22040459baac2db6c68f3c0ddde98b0db8f6`.
- Highest positive integer `final_net_project_equity` across all 450 rows: **308,412,450 YER, trial_id=60**, with one trial at this maximum. This is the maximum of the V3 cohort, rather than an inference from Stage 12's larger 550-trial cohort.
- V3 fingerprint for trial 60 is `e749225975424a11bb2e560c6fe82a83ad2cc1c2f7c190c07b6405d3db7fa645`, matching the Stage 12/official selected TrialResult fingerprint for trial 60.
- Cross-checks from this same V3 TrialResult table: P10 trial 131 = 265,600,350; P50 trial 29 = 276,669,500; P90 trial 18 = 288,621,050; Loss trial 304 = 249,030,500. These agree with V3's existing role register. The existing file name remains `Loss.json` and maps to the normative role `LossCase`.

**Disposition:** MaxCase selection for cohort V3 is now `PASS_SCOPED`: `trial_id=60`, equity `308412450`. It is not a claim that a MaxCase daily JSON is present inside V3; it is not.

## 3. Stage 12 Parquet search for Partner balances

- Artifact `11634501915`, Run `37964656154`, producer SHA `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`, source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`.
- ZIP: 65,578,787 bytes, SHA-256 `7d67097186dad801c6f0377a70decb5cf8dadea8f82a0b86956823a6a4191cf1`; digest and producer identity matched GitHub API metadata.
- Parquet member `C050_G000.parquet`: SHA-256 `6beecb837a3c6b71f34aedbeb958e8dd176cce3d60b2dfa1b95ee9bd57e6a380`, 1,225,547 rows scanned for schema-field presence.
- Schema includes `Retained_Earnings`, `Closing_Cash`, `Closing_Equity`, `Net_Bike_Assets`, `Balance_Difference`, and `result_sha256`. It has no `Cumulative_Project_Profit` field.
- Search across the full schema for `partner`, `memo`, `reinvest`, and `balance` returned only `Balance_Difference`. There is no `Partner1_Reinvestment_Balance`, no `Partner2_Reinvestment_Balance`, and no alternate partner/memo/reinvestment-balance column name in this Stage 12 artifact.
- Trial 60 has 2,235 daily rows, `2027-01-01` through `2033-02-12`. The Stage 12 verifier records the same TrialResult fingerprint as V3, so the selected trial identity agrees across these two artifacts; it does not create the absent partner-balance fields.

## 4. Resolved vs. remaining fields

- `Cumulative_Project_Profit` is **not** an unresolved business decision: the original reference §§10.9–10.10 explicitly equates it to `Final_Retained_Earnings` at the same time. The pinned source calculation also sets `retained_earnings = cumulative_project_profit`. Use only when trial/date/source identity is bound; financial amounts remain exact integers.
- The two partner reinvestment balances are absent from the Stage 12 Parquet schema and from the missing fifth V3 MaxCase payload. The four existing V3 representative payloads P10/P50/P90/Loss do contain these fields in their daily arrays; they cannot substitute for a MaxCase daily record. Their source for MaxCase remains `MISSING_EVIDENCE / PENDING_DATA_SOURCE`; do not derive them from cash, equity, retained earnings, or any unrelated balance field.
- Hence the only missing daily-accounting fields identified for the provisional MaxCase row are `Partner1_Reinvestment_Balance` and `Partner2_Reinvestment_Balance`. The selection ID and final equity are known from V3; the full role contract and production acceptance remain incomplete.

## 5. Boundaries and next action

- No source SHA, seed/RNG, trial IDs, historical data, Parquet or manifest changed.
- No production simulation, Trial, Monte Carlo, CS or XLSX delivery build occurred in this CP.
- Gate A remains `BLOCKED`; `log_events` remains `PENDING_APPROVAL`; Stage 9C historical status remains `PARTIAL / CONFLICTED`.
- The owner's provisional P16 instructions specify how to mark MaxCase/partner fields while missing. This result satisfies the selection part and confirms the partner-balance gap; P16 must preserve the missing-field labels and not present a final accepted contract.
- Delivery remains `NOT_ACCEPTED`; Release remains `BLOCKED / NOT_AUTHORIZED`.
