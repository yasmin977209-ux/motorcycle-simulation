# Stage 10 Benchmark Report

## 1. Executive Summary
تمت قياسات Stage 10 الفعلية على GitHub Actions في Run 37709936740 على commit ca73f2df37baacebbcad965fc5f433f129675820، وجميع 45 وظيفة matrix للقياس اكتملت بنجاح.
تم قياس جميع التوليفات الـ25: 20 Scenario غير C100 أضافت 100 trial canonical لكل Scenario، و5 Scenarios C100 نفذت 100 قياس أداء فقط لكل Scenario.
إجمالي التنفيذات المقبولة في الدليل = 2500، وإجمالي canonical trials الجديدة الفعلية = 2000، وليس رقمًا مفترضًا.
الـ20 Scenario غير C100 أصبحت artifacts قابلة للاستئناف وتحتوي فعليًا على التسلسل 1..550؛ لم يُعد تشغيل أي trial من dataset القياس المقبول.
C100 حافظت على canonical trial واحد فقط، وتم التحقق من تطابق نتيجة المحرك عبر 100 benchmark samples لكل Scenario.
أقصى زمن Job فعلي في Run القياس = 470 ثانية، وأقصى أقل من 35 دقيقة؛ أقصى concurrency مرصودة = 10، وزمن matrix الكلي = 1051 ثانية.
تم التحقق من source_sha وmaster_seed وrequirements blob وmanifest blob وfingerprints عبر artifacts نفسها.
التوافق مع مسار Stage 11 مثبت على مستوى source/Python/requirements/scenario/RNG/schema/serialization في القياس المقبول؛ لكن Workflow/Topology Stage 11 نفسها غير موجودة حاليًا في المستودع.
لذلك تقدير Stage 11 الكامل لا يمكن عرضه كزمن Job فعلي وحيد؛ التقرير يقدم serial وStage10-topology وتقديرات checkpoint مشروطة فقط.
حدثت أثناء CP بعض WORKFLOW_DEFECTS في harness/aggregate وتم تصحيحها، Run القياس المقبول مستقل عنها، بينما Runs recovery اللاحقة غير مقبولة كدليل benchmark ولا تدخل في dataset.
البيانات الخام المقبولة كاملة 25/25 و2500/2500 و2000/2000، لكن environment fingerprint الكامل (package fingerprint وavailable RAM) لم يُسجل داخل القياس المقبول.
الحكم النهائي لـStage 10 = STAGE-10-PARTIAL بسبب نقص بعض عناصر environment identity المطلوبة، مع بقاء dataset extension نفسها مكتملة وقابلة للاستئناف.

## 2. Current State Verification

| العنصر | expected/history | verified value | judgment |
|---|---|---|---|
| main HEAD before Stage10 | 7c92ea491cafe8434e0c42063160a8f3ae4740f1 | 7c92ea491cafe8434e0c42063160a8f3ae4740f1 | MATCH |
| state.sha | a7db0153299b3af8f89111bec52bb07d1356509c | a7db0153299b3af8f89111bec52bb07d1356509c | MATCH |
| state.sha_semantics | parent_state_commit_pointer | parent_state_commit_pointer | MATCH |
| canonical_content_sha | a7db0153299b3af8f89111bec52bb07d1356509c | a7db0153299b3af8f89111bec52bb07d1356509c | MATCH |
| Stage7 Run | 37225915321 | 37225915321 | MATCH |
| Stage7 run_head_sha | e0b2fab6710833774937d778097363d7a8ee8e59 | e0b2fab6710833774937d778097363d7a8ee8e59 | MATCH |
| Stage7 source_sha | f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b | f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b | MATCH |
| current dataset total before Stage10 | 9005 | 9005 (from approved state/manifest) | MATCH |
| scenario count | 25 | 25 | MATCH |
| source of benchmark Run | expected branch tmp/stage10-bench-20261008 | tmp/stage10-bench-20261008 | MATCH |

## 3. R4

| Element | main | stage3b-preserved | reference / Stage10 instruction | verdict |
|---|---|---|---|---|
| Trigger | workflow_dispatch; unrestricted invocation | لا يوجد Workflow Stage10 مماثل متاح في stage3b | push to exact tmp/stage10-bench-20261008 + path trigger; no workflow_dispatch | REPLACE |
| Source | reconstruct archive + old source hash | no matching Stage10 source contract | github.sha/source identity + Stage7 artifact identity | REPLACE |
| Timeout | 350 min/job | not available | timeout inside job; >35m is high risk; 45m ceiling in benchmark | REPLACE |
| Matrix | 25 jobs, one demo trial | not available | 45 jobs: 20 canonical + 25 C100 chunks; max-parallel 10 | REPLACE |
| Artifacts | stage10-benchmark one-trial output | not available | Stage7 block artifacts + stage10-bench-* verifiable artifacts | REPLACE |
| Branch scope | manual | not available | exact pinned temporary branch; no wildcard | REPLACE |

Workflow classification: **ARCHIVE-AND-REPLACE**.
The legacy workflow was retained only under `docs/stage10/legacy/` as documentation, not as a discovered workflow.

## 4. Trial Identity and Scenario State

| Scenario | C | G | Current N | Highest | Next ID | New range | Status | Next check |
|---|---:|---:|---:|---:|---:|---|---|---:|
| C100_G100 | 1.00 | 100% | 1 | 1 | 2 | none (benchmark-only) | stable | 1 |
| C100_G070 | 1.00 | 70% | 1 | 1 | 2 | none (benchmark-only) | stable | 1 |
| C100_G050 | 1.00 | 50% | 1 | 1 | 2 | none (benchmark-only) | stable | 1 |
| C100_G030 | 1.00 | 30% | 1 | 1 | 2 | none (benchmark-only) | stable | 1 |
| C100_G000 | 1.00 | 0% | 1 | 1 | 2 | none (benchmark-only) | stable | 1 |
| C085_G100 | 0.85 | 100% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C085_G070 | 0.85 | 70% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C085_G050 | 0.85 | 50% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C085_G030 | 0.85 | 30% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C085_G000 | 0.85 | 0% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C070_G100 | 0.70 | 100% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C070_G070 | 0.70 | 70% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C070_G050 | 0.70 | 50% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C070_G030 | 0.70 | 30% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C070_G000 | 0.70 | 0% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C050_G100 | 0.50 | 100% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C050_G070 | 0.50 | 70% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C050_G050 | 0.50 | 50% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C050_G030 | 0.50 | 30% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C050_G000 | 0.50 | 0% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C030_G100 | 0.30 | 100% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C030_G070 | 0.30 | 70% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C030_G050 | 0.30 | 50% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C030_G030 | 0.30 | 30% | 450 | 450 | 451 | [451, 550] | stable | 500 |
| C030_G000 | 0.30 | 0% | 450 | 450 | 451 | [451, 550] | stable | 500 |

## 5. Scenario Results

| Scenario | Exec | Canonical Added | p50 s | p95 s | p99 s | Job s | Peak RSS MB | Artifact KB | Final fingerprint |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| C100_G100 | 100 | 0 | 3.762 | 3.965 | 3.996 | 421 | 111.8 | 16.6 | `95c9d98d895e4a5711f3c06e2f2a56c9a9f3dc1e0936a6ffa5c989c43299f571` |
| C100_G070 | 100 | 0 | 3.627 | 3.988 | 4.021 | 433 | 114.4 | 16.6 | `6efa5f1f85f07c24380dfff01d19280938d0068c9b8b57d5ce904905bb945529` |
| C100_G050 | 100 | 0 | 3.659 | 3.971 | 3.988 | 456 | 112.6 | 16.7 | `86e095f84d26fc6398af1fbd624d353b6c01009feda9434ab37af788b420b5c3` |
| C100_G030 | 100 | 0 | 2.783 | 3.954 | 3.962 | 381 | 111.9 | 16.5 | `f342dc950b12810108825d842a93b51e6816fe4c2e90bc7fd49d0b51762f0a70` |
| C100_G000 | 100 | 0 | 3.904 | 4.035 | 4.062 | 456 | 110.9 | 16.5 | `1b6390fe7326200133e133d68a4b260694bc2f72a9a58b8461da5494e231272c` |
| C085_G100 | 100 | 100 | 4.001 | 4.021 | 4.029 | 425 | 114.6 | 47.8 | `eba464e979c8b15e96bbae8783380732c78fc8404cb39fe30f1ae1e1940425e6` |
| C085_G070 | 100 | 100 | 2.026 | 2.073 | 2.111 | 221 | 118.5 | 47.8 | `62ee2197b613986e7f0062b4d5f08f8f05739dde0624895d35dc4607850ec814` |
| C085_G050 | 100 | 100 | 4.037 | 4.055 | 4.062 | 424 | 116.9 | 47.7 | `f4d9f3874213f7da3cda6ecf1644a43751f23a5d5d64f39a5a1df7e52de42d8a` |
| C085_G030 | 100 | 100 | 1.996 | 2.069 | 2.100 | 218 | 118.0 | 47.8 | `dc8a28bec6ca9a0c183bb68bda2aa365dcdd31a45127676813f94fe76edbbce7` |
| C085_G000 | 100 | 100 | 4.000 | 4.026 | 4.038 | 421 | 116.4 | 48.1 | `fb330c6fd85971140ab27fc878e778affcd957ef44ab64675735fbc3fbc485c5` |
| C070_G100 | 100 | 100 | 3.848 | 3.886 | 3.921 | 407 | 114.1 | 51.2 | `19f69c89013e182cbc6893bf3c0ccd33af14d244542f98a3460aa50ff001242b` |
| C070_G070 | 100 | 100 | 3.902 | 3.943 | 3.957 | 414 | 116.3 | 50.8 | `4d5dc82fced74abee95d5a34a2aeb00aee07ca3de58351f5f9b5c333b803b34c` |
| C070_G050 | 100 | 100 | 3.903 | 3.943 | 3.972 | 413 | 117.4 | 50.8 | `6006c98ad76a5d906a8e2b4eca2faedc7c584213f60b2198782322150b2ffa82` |
| C070_G030 | 100 | 100 | 2.809 | 2.849 | 2.863 | 301 | 118.0 | 51.0 | `fb953cebb484f15538c310229c687ebe868430a363679987dd11b8e3f583478b` |
| C070_G000 | 100 | 100 | 3.912 | 3.982 | 3.993 | 412 | 114.4 | 50.8 | `f158340602c169c56a158d7151ecde210b3b92bdd9922b7c7b5dff39f1063608` |
| C050_G100 | 100 | 100 | 4.458 | 4.634 | 4.694 | 470 | 114.8 | 65.7 | `05614a6280863b422103225c385292ac1a722338b70c0c6756c23af3dc878926` |
| C050_G070 | 100 | 100 | 3.930 | 4.088 | 4.126 | 413 | 118.5 | 68.2 | `22ecf74930ff07b7318faf53f4929b343cb1c9bad93d3cccb69eeb599ee7539b` |
| C050_G050 | 100 | 100 | 4.241 | 4.455 | 4.564 | 450 | 119.4 | 68.3 | `ede8c949c11f7215534bf34232ca918542e5b2e18152f8723208e5a13c6b95c8` |
| C050_G030 | 100 | 100 | 4.197 | 4.375 | 4.427 | 439 | 115.2 | 68.3 | `fbc857a1318fe87e7eeca4a1879c8424a308b1a53ad02506969d24fb98491196` |
| C050_G000 | 100 | 100 | 4.103 | 4.285 | 4.338 | 432 | 114.9 | 67.9 | `2e6bda707dc44882fdca6ba10c1249992b6d529d33574872d759c7b883ed2188` |
| C030_G100 | 100 | 100 | 1.035 | 1.113 | 1.168 | 128 | 120.0 | 65.1 | `307bd866bfe0322adec7a283ab9a29e86d8cb299d2dd15f2770922ca4cd11308` |
| C030_G070 | 100 | 100 | 1.140 | 1.211 | 1.251 | 137 | 116.8 | 66.9 | `8de72e47111abc1c7e15a1460001bfa3020a2bbf8c8ceaf82deed16abf4df690` |
| C030_G050 | 100 | 100 | 1.022 | 1.082 | 1.100 | 122 | 114.9 | 64.4 | `ce59996de32731bde321006f194142854737793871123e741df21191e0391c4b` |
| C030_G030 | 100 | 100 | 0.781 | 0.820 | 0.827 | 101 | 115.5 | 66.3 | `a5541d72c212e3953c4ed11b1fe03ab9e89ba00f1c0b05348f413cc13822691b` |
| C030_G000 | 100 | 100 | 0.646 | 0.684 | 0.688 | 83 | 117.2 | 64.2 | `2cb52a9170f835ac8daae7588f95d3aa086a73cd0200b1aa97c4e618dcbb3b8b` |

## 6. C100 Equality Gate

| Scenario | Samples | Unique result SHA256 count | Judgment |
|---|---:|---:|---|
| C100_G100 | 100 | 1 | PASS |
| C100_G070 | 100 | 1 | PASS |
| C100_G050 | 100 | 1 | PASS |
| C100_G030 | 100 | 1 | PASS |
| C100_G000 | 100 | 1 | PASS |

## 7. Artifact / Dataset Verification

- Accepted measurement artifacts: **45/45**.
- Accepted execution measurements: **2500/2500**.
- Accepted canonical additions: **2000/2000**.
- Non-C100 sequence verification: every accepted scenario contains exactly trial IDs **1..550**, unique and gap-free.
- C100: one canonical trial only; benchmark samples remain performance-only.
- All accepted metrics report `source_sha = f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, `master_seed = 20270101`, `schema_version = stage10-benchmark-v1`.

## 8. Environment / Fidelity

- Python observed: 3.11.17.
- Runner OS: Ubuntu 24.04 / X64.
- Runner image: 20261004.327.1.
- CPU count: 4.
- CPU model string returned by runner: `x86_64` (not a specific model).
- Engine source, scenario parsing, `TrialResult` schema and Parquet serialization are directly executed from the pinned repository source; no engine file was modified.
- Missing environment measurements: installed-package fingerprint and available-memory value were not recorded by the accepted benchmark harness. Peak RSS was recorded. This prevents a full source/environment identity PASS.

## 9. Performance Summary

- Stage10 matrix jobs: 45.
- Configured/observed max concurrency: 10 / 10.
- Matrix wall time: 1051 s = 17.52 min.
- Sum of job wall time: 8578 s = 2.383 h.
- Longest job: 470 s = 7.83 min; no job exceeded 35 min.

## 10. Stage 11 Estimate

| Estimate | Central | Conservative/p95 | Scope |
|---|---:|---:|---|
| Fresh serial rebuild of current 9005 trials | 7.763 h | 7.960 h | workload reference, not Stage11 topology |
| Fresh serial rebuild of extended 11005 trials | 9.430 h | 9.671 h | workload reference, not Stage11 topology |
| Next 50-trial checkpoint cost across 20 non-C100 scenarios | 0.834 h | 0.855 h | conditional; those 50 rows are already included in Stage10 extension |
| New simulation trials required after accepting Stage10 canonical extension | 0 h | 0 h | current stage7-state is already stable; extension is already executed and reusable |

Stage11 topology is **NOT DEFINED IN CURRENT REPOSITORY**. Therefore no invented worker count/job count is used. The Stage11 runtime beyond already-executed simulation work remains conditional on its later workflow.

## 11. Failure Classification

| Run | Classification | Evidence | Treatment |
|---|---|---|---|
| 37709744299 | WORKFLOW_DEFECT | harness SyntaxError: unterminated string literal | excluded; no engine trial executed |
| 37709840088 | WORKFLOW_DEFECT | harness SyntaxError: malformed f-string | excluded; no engine trial executed |
| 37709936740 aggregate job | WORKFLOW_DEFECT | aggregate script syntax error; 45/45 matrix jobs were successful | excluded aggregate only; matrix artifacts accepted |
| 37711508265 | WORKFLOW_DEFECT | recovery workflow path did not support aggregate-only contract | excluded |
| 37711587801 | WORKFLOW_DEFECT / INVALID RUN | recovery condition launched matrix jobs, including canonical execution path | excluded entirely from dataset/evidence |

## 12. PASS / PARTIAL Gates

| Gate | Result | Evidence |
|---|---|---|
| 25/25 measured | PASS | 45 matrix jobs cover all 25 scenarios |
| 2500 executions | PASS | 20×100 + 5×100 = 2500 |
| 2000 canonical added | PASS | artifact-derived count |
| No duplicate accepted trial IDs | PASS | non-C100 1..550 verified; C100 remained trial 1 |
| Dataset identity | PASS | baseline fingerprints/state identities matched |
| Source identity | PARTIAL | source/Python/runner identity present; package fingerprint/RAM missing |
| Artifacts/fingerprints | PASS | 45 accepted artifacts; SHA-256 verified locally |
| Fidelity to Stage11 | PARTIAL | engine path same; Stage11 workflow itself not defined |
| No engine change | PASS | only Stage10 workflow/scripts/docs/state touched |
| No stage7-state change | PASS | Stage7 state used read-only |
| Workflow defects resolved for accepted path | PASS | measurement harness and aggregate corrected; invalid recovery runs excluded |
| Final Stage10 verdict | PARTIAL | full environment fingerprint gate not satisfied |

## 13. SHA Verification Block

- Pre-Stage10 main: `7c92ea491cafe8434e0c42063160a8f3ae4740f1`
- Accepted measurement branch head / Run head: `ca73f2df37baacebbcad965fc5f433f129675820`
- Source SHA: `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`
- Stage7 Run ID: `37225915321`
- Measurement Run ID: `37709936740`
- requirements blob SHA: `81131ac1437fc652ceff21831570ce19de314b78`
- dataset manifest blob SHA: `e796fa2443493b607f1f9c60b58eb63607959c26`

## 14. Final Verdict

**PRODUCT: PRODUCT-VERIFIED**

**STAGE-10: STAGE-10-PARTIAL**

سبب PARTIAL: القياس التشغيلي والامتداد canonical مكتملان، لكن accepted benchmark لا يحتوي installed-package fingerprint وavailable-RAM measurement، كما أن Stage11 workflow/topology غير معرف حاليًا؛ لذلك لا يجوز إعلان PASS كامل وفق بوابات Stage10.

Invalid recovery runs are not part of the accepted dataset and must not be used as evidence or resumed trials.

**STAGE-11: NOT STARTED**

**NEXT ALLOWED ACTION:** لا يبدأ Stage 11 إلا بإذن منفصل، وبعد معالجة/قبول أسباب PARTIAL حسب قرار المستخدم.
