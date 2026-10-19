# CP-Excel DAILY — مراجعة R4 وفحص P50 حقيقي

**التاريخ:** 2026-10-19  
**النمط:** مراجعة هندسية ضمن CP-P7؛ لا تعديل للكود/الاختبارات/Workflow في هذه الخطوة، ولا تشغيل للمحاكاة أو Trial أو Checkpoint جديد.  
**الفرع الحالي للمرشح:** `tmp/cp-excel-daily-repair-20261017`, HEAD `ff02990ccc706ca7d0c68416b8a91f9aa475a5f2`  
**`main` HEAD:** `647c19826b90d8224ce73ef9b90c306a45e03fb0`

## R4 — العقد ومحل العيب

| العنصر | الوضع الحالي | المرجع/القرار والنص الحاكم | الحكم |
|---|---|---|---|
| `write_daily_sheet` في `main` | ملف `scripts/excel_builder.py` blob `50115a2fea5812727e0e5a8bfbb07e1f853f026b` يحدد `headers=list(rows[0])` ثم يستدعي `write_table(ws,headers,rows,...)` مع `rows=payload["daily"]` وهي قائمة قواميس. | داخل `write_table` ينفذ الكود `for col, value in enumerate(row, 1)` ثم يكتب `py_value(value)`. تكرار dict يخرج **المفاتيح** لا القيم. | **K_CODE — عيب مثبت بالقراءة:** ورقة DAILY في main معرضة لكتابة أسماء الحقول داخل كل صف بيانات بدل قيمها. لم أعد تشغيل هذا الكود على main. |
| الإصلاح المرشح | مرشح `scripts/excel_builder.py` blob `05ef1685eed7f9deb4bb7a4ffb64e3447c9a1a82` يبني `value_rows = [[row.get(header) for header in headers] for row in rows]` ويمررها إلى `write_table`. | قسم P7 من مرجع المشروع: «تحويل كل dict إلى صف values» والحفاظ على ترتيب الأعمدة والقيم والتواريخ و`None` والمبالغ كأعداد صحيحة. | **مطابق للعقد ضمن المدخل الموثق:** تحويل صغير يحافظ على ترتيب الرؤوس ويكتب القيم. |
| اختبار الانحدار | `tests/test_excel_daily_sheet.py` blob `46684e70e62705196549b863e3bed37dfaa0f31e`؛ يختبر round-trip اصطناعيًا واختبار P50 الحقيقي. | لا تُحوّل fixture إلى دليل لبيانات الإنتاج؛ قبول P7 يشترط بيانات حقيقية ذات هوية ثابتة عند توفرها. | **مطابق للنطاق:** اختبار P50 الحقيقي موجود ومشغّل في Run مفصل أدناه؛ لم يعدّل في هذه المراجعة. |
| حدود القبول | Stage 9A سجّل 185 ورقة، أما Stage 9C فيبقى `PARTIAL` لعدم توفر daily accounting ledger كامل لكل 9,005 تكرارات. | تقرير `docs/stage9c/STAGE9C_REPORT.md` على `main` ينص صراحة أن سجلات `_ACCTG` المتاحة تخص التكرارات التمثيلية وليست دفترًا يوميًا لجميع التكرارات. | لا يترقى نجاح DAILY الفردية إلى قبول المصنف ذي 185 ورقة، ولا إلى إغلاق Stage 9C أو التسليم النهائي. |

## دليل التحقق من الكود والـRun

- Workflow: [CP Excel DAILY repair real P50 verification](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/38969329539)
- Run ID `38969329539`, event `push`, branch `tmp/cp-excel-daily-repair-20261017`, tested SHA `e3aa5b16da6fec729ff9e7b9591336d33ffef324`, conclusion `success`.
- Job `daily-real-p50-acceptance`, ID `117203529690`, succeeded, including source-identity download and verification, the focused acceptance tests, evidence hashing, XLSX/evidence upload and acceptance-contract assertions.
- Exact pytest output: `3 passed, 1 warning in 1.02s`; `exit_code=0`; workflow printed `REAL_P50_SOURCE=PASS rows=1568` and `DAILY_ACCEPTANCE_CONTRACT=PASS`. Warning: `SyntaxWarning: invalid escape sequence '\\ '` at `scripts/excel_builder.py:301`; it was non-fatal and outside the narrow serializer change.
- Relevant source/test blobs at the tested SHA were read back equal to the blobs at the current candidate HEAD: builder `05ef1685eed7f9deb4bb7a4ffb64e3447c9a1a82`, tests `46684e70e62705196549b863e3bed37dfaa0f31e`. Current candidate HEAD is **not** the exact tested SHA: later commit `ff02990ccc706ca7d0c68416b8a91f9aa475a5f2` changed `state.json` by 97 additions. This report does not treat the whole current tree as identical to the tested tree or adjudicate that later state change. The main branch/state are separate and were not changed here.

## Real P50 data identity and artifact

The run fetched and checksum-verified the existing canonical source artifacts before exporting the real representative. The report and identity sidecar state:

- Canonical source Run `37225915321`, producer head `e0b2fab6710833774937d778097363d7a8ee8e59`, `SOURCE_SHA=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`.
- Scenario `C030_G030`, P50 `trial_id=156`, scenario cohort size `450`, schema `1.0`, master seed `20270101`, RNG `RNG_SHA256_DERIVED_V1`, sampling `SAMPLING_ADAPTIVE_1_300_PLUS50_V1`, trial-ID policy `TRIAL_ID_SEQ_1_TO_N_NO_GAPS_V1`, approved reference SHA `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`.
- Canonical enriched input artifact ID `11497409735`; source artifact ZIP SHA-256 `9331c726560471f3092b2c61893a7ad87f3bafed363217249b6f4a992c029c07`; scenario TAR SHA-256 `a2403a9175ef85ec30663fbdb7ecd322c88beaf9672e1b73b30488312cd4aa10`; P50 JSON SHA-256 `e86d0c48cd48028f465dcc10cab92b60f672ef919cefc7d400097fe303ac00de`; scenario metadata SHA-256 `b4ae78a224b4fb296cceac2adbcad81fa3624a053b93b621434f7349551c9a73`.
- Published 185-sheet workbook was used only as read-only provenance and verified at its pinned inner XLSX SHA `0fb325fc9e196a534ba8ab7484dcfd0541cefd3a2ca37c3b6f930e3215f62f6d`, `46,958,193` bytes, artifact ID `11507380986`, global manifest SHA `892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6`. It was not rewritten or replaced by this CP.
- Real DAILY test report: `PASS_REAL_P50_DAILY_ROUND_TRIP`; `daily_row_count=1568`, `header_count=20`, `tested_row_comparisons=1568`, `tested_cell_comparisons=31360`, zero formulas and zero Excel error cells; source dates `2027-01-01` through `2031-04-17`; `simulation_rerun=false`, `historical_data_modified=false`.
- Run artifact `12075489041`, name `cp-excel-daily-repair-real-p50`, size `147,993` bytes, ZIP digest `sha256:2ee7b21782165d602ada7f704cf2d8cadfd8ccb84d5e77e5e53dc6063f4faf36`. This digest matches the uploaded review ZIP `/mnt/data/cp-excel-daily-repair-real-p50.zip`. All six entries in its internal `SHA256SUMS.txt` matched the actual member bytes.

## Independent inspection of the physical XLSX supplied for review

The actual file `C030_G030_DAILY_P50_trial_156.xlsx` was opened via the spreadsheet artifact inspection tool, not inferred from logs alone.

- Actual XLSX SHA-256 `51a48060197274166ea7588328d966354180d70f4216d57dcda9a09de9f58d22`, exact byte size `161,976`; matches the archive’s embedded checksum and the acceptance report.
- One sheet: `C030_G030_DAILY`, dimensions `A1:T1569`: one header row + 1,568 data rows, 20 columns.
- Header order exactly matches the acceptance report: `Accounts_Receivable`, `Accumulated_Depreciation`, `Active_Bikes`, `Capital`, `Cash`, `Cumulative_Project_Profit`, `Final_Close_Date`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Net_Equity`, `Operating_Expenses`, `Operating_Net_Profit`, `Operating_Revenue`, `Owned_Transferred_Bikes`, `Partner1_Reinvestment_Balance`, `Partner2_Reinvestment_Balance`, `Pending_Claims`, `Retained_Earnings`, `date`, `trial_id`.
- Date-column serial values begin at `46388` and end at `47955`, with a strict increment of one per row (1,568 contiguous dates); the source and acceptance report map these to `2027-01-01` and `2031-04-17`. All data rows carry `trial_id=156`; `Final_Close_Date` is constant at serial `47955`.
- Independent table scan: zero blank data cells, no non-integer numeric values, no Excel error tokens matched. Formula count is zero in the Run’s acceptance report and the test’s physical-workbook scan.
- The inspected first/last row values agree with the acceptance report. For example first day starts with cash `0`, capital `3,700,000`, cumulative project profit `-100,000`; last day has cash `11,903,500`, net equity `37,197,400`, final date `2031-04-17`.

## Acceptance judgment and remaining gap

**P7 scoped disposition: `PASS_REAL_P50_DAILY_ROUND_TRIP` for the candidate serializer and this one source-identified P50 sheet.** The binary XLSX and all archive-internal checksums were independently re-read and validated in this review.

**Overall project status: `PARTIAL / NOT_READY_TO_MERGE_OR_DELIVER`.** Current `main` still has the dict-to-row defect (builder blob `50115a2fea5812727e0e5a8bfbb07e1f853f026b`); this reviewed fix is only on a temporary branch and was not merged. The test Run checked SHA `e3aa5b16da6fec729ff9e7b9591336d33ffef324`, not current candidate HEAD `ff02990ccc706ca7d0c68416b8a91f9aa475a5f2`, although the code and test blobs match. The real-data acceptance covers one scenario/one representative, not all 25 P50 sheets or the final 185-sheet workbook; it does not resolve Stage 9C’s explicit full-daily-ledger gap.

No code, test, workflow, reference, main branch, main `state.json`, model source, RNG, sampling policy, trial data, Parquet, workbook source, or production output was modified in this review. No merge or Release was made.


## Addendum — correct workbook SHA-256 transcription (2026-10-19)

Post-write read-back review found a one-character transcription typo in the earlier “Actual XLSX SHA-256” field above. The authoritative SHA-256 verified by the live file bytes, archive checksum list, and embedded acceptance report is:

`51a48060197274166ea7588328d966354180d70f4216d57dcda9a09de9f58d22`

The ZIP digest remains `2ee7b21782165d602ada7f704cf2d8cadfd8ccb84d5e77e5e53dc6063f4faf36`, and internal `SHA256SUMS.txt` confirms the same workbook digest and `161,976` byte size. This was a report transcription issue only; no workbook/code/data bytes changed.
