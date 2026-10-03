# Stage 6.5 — CP1 Evidence

## Run metadata

- CP: CP1
- Scenario: C085_G100
- GitHub Actions Run: 37137722603
- GitHub Actions Job: 111245549492
- Code/workflow commit tested: 7d31c209ff13efbed6047638ec9755c494784a66
- Result: PASS
- No `ModuleNotFoundError` or `ImportError` occurred.

## Regression stdout

The workflow executed the authorized CP1 scope only.

```text
============================== 1 passed in 10.64s ==============================
6 passed in 0.12s
19 passed in 0.23s
33 passed in 0.09s
22 passed in 52.68s
```

Interpretation by command order:

1. `python -m pytest -q tests/test_stage6_5_log_events.py -v`
   - 1 passed in 10.64s
2. `python -m pytest -q tests/test_stage1.py`
   - 6 passed in 0.12s
3. `python -m pytest -q tests/test_stage2.py tests/test_stage2_entities_additions.py`
   - 19 passed in 0.23s
4. `python -m pytest -q tests/test_stage3a.py`
   - 33 passed in 0.09s
5. `python -m pytest -q tests/test_stage3b_accounting.py tests/test_stage3b_partner_equity.py tests/test_stage3b_m_order.py tests/test_stage3b_closure.py tests/test_stage3b_path1.py tests/test_stage3b_paths.py tests/test_stage3b_no_time_cap.py tests/test_stage3b_determinism.py`
   - 22 passed in 52.68s

Total across these five pytest invocations: 81 passed, 0 failed.

## Raw measurement stdout

### log_events=True

```text
{"elapsed_seconds": 3.8173689779999904, "event_log_len": 262603, "lifecycle_history_len_bike0": 736, "log_events": true, "rss_kb": 116852, "trial_id": 1, "trial_result_sha256": "a60bc3e8cce2f3dc00c47314d9365867cb65841699fe81b2d9c49fbf8d3520a3"}
{"elapsed_seconds": 3.734831063999991, "event_log_len": 262603, "lifecycle_history_len_bike0": 736, "log_events": true, "rss_kb": 116688, "trial_id": 2, "trial_result_sha256": "7fa6a52a8d048c6ba1017e97110f3b68d20fee1c2a09c6d0fa0131cf87b58549"}
{"elapsed_seconds": 3.781303429999994, "event_log_len": 262603, "lifecycle_history_len_bike0": 736, "log_events": true, "rss_kb": 116712, "trial_id": 3, "trial_result_sha256": "a172127e92ee93a37338985132da2c296178dc801cfa4b845314fa4d0f7f8851"}
{"elapsed_seconds": 3.764741963000006, "event_log_len": 262603, "lifecycle_history_len_bike0": 736, "log_events": true, "rss_kb": 116776, "trial_id": 4, "trial_result_sha256": "88cc39c72f5a83d6107ddc03c15afba1fe656cc108d24d73dc64e0f23cc351fc"}
{"elapsed_seconds": 3.7723679489999995, "event_log_len": 262603, "lifecycle_history_len_bike0": 736, "log_events": true, "rss_kb": 116776, "trial_id": 5, "trial_result_sha256": "18a9c6731a8e6ac2d2a2bc270bd9f787476a48513daf5f397f07d440f2859fc"}
```

### log_events=False

```text
{"elapsed_seconds": 3.2668478490000012, "event_log_len": 0, "lifecycle_history_len_bike0": 0, "log_events": false, "rss_kb": 37676, "trial_id": 1, "trial_result_sha256": "a60bc3e8cce2f3dc00c47314d9365867cb65841699fe81b2d9c49fbf8d3520a3"}
{"elapsed_seconds": 3.2596894059999926, "event_log_len": 0, "lifecycle_history_len_bike0": 0, "log_events": false, "rss_kb": 37852, "trial_id": 2, "trial_result_sha256": "7fa6a52a8d048c6ba1017e97110f3b68d20fee1c2a09c6d0fa0131cf87b58549"}
{"elapsed_seconds": 3.2550805230000037, "event_log_len": 0, "lifecycle_history_len_bike0": 0, "log_events": false, "rss_kb": 37768, "trial_id": 3, "trial_result_sha256": "a172127e92ee93a37338985132da2c296178dc801cfa4b845fa4d0f7f8851"}
{"elapsed_seconds": 3.241626970999988, "event_log_len": 0, "lifecycle_history_len_bike0": 0, "log_events": false, "rss_kb": 37724, "trial_id": 4, "trial_result_sha256": "88cc39c72f5a83d6107ddc03c15afba1fe656cc108d24d73dc64e0f23cc351fc"}
{"elapsed_seconds": 3.242415403000024, "event_log_len": 0, "lifecycle_history_len_bike0": 0, "log_events": false, "rss_kb": 37728, "trial_id": 5, "trial_result_sha256": "18a9c6731a8e6ac2d2a2bc270bd9f787476a48513daf5f397f07d440f2859fc"}
```

## Comparison table from stdout

| trial_id | T_True (s) | T_False (s) | فرق % | RSS_True (KB) | RSS_False (KB) | dlog | SHA match |
|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1 | 3.817369 | 3.266848 | -14.421481 | 116852 | 37676 | 262603 | نعم |
| 2 | 3.734831 | 3.259689 | -12.721905 | 116688 | 37852 | 262603 | نعم |
| 3 | 3.781303 | 3.255081 | -13.916442 | 116712 | 37768 | 262603 | نعم |
| 4 | 3.764742 | 3.241627 | -13.895109 | 116776 | 37724 | 262603 | نعم |
| 5 | 3.772368 | 3.242415 | -14.048273 | 116776 | 37728 | 262603 | نعم |

## Summary from stdout

```json
{"all_false_event_log_zero": true, "all_sha_match": true, "all_true_event_log_positive": true, "mean_RSS_False_KB": 37749.6, "mean_RSS_True_KB": 116760.8, "mean_T_False_s": 3.253132030400002, "mean_T_True_s": 3.7741226767999962, "mean_time_difference_pct": -13.804284889905377, "rss_false_lower": true, "scenario_id": "C085_G100", "time_false_lower": true, "trials": 5}
```

## Required checks

- SHA-256 matched for all 5 trial IDs: PASS.
- `len(project.event_log) > 0` for all True runs: PASS; 262603 in every True run.
- `len(project.event_log) == 0` for all False runs: PASS.
- Mean T_False < Mean T_True: PASS.
- Mean RSS_False < Mean RSS_True: PASS.

## Averages

- Mean T_True: 3.7741226767999962 s
- Mean T_False: 3.253132030400002 s
- Mean difference: -13.804284889905377%
- Mean RSS_True: 116760.8 KB
- Mean RSS_False: 37749.6 KB
- Derived RSS reduction: 67.6692862673089%

## Initial recommendation

The measured C085_G100 sample shows a clear measured benefit from disabling event logging for the tested non-representative trials: mean execution time was 13.804284889905377% lower and mean RSS was 67.6692862673089% lower. This is an initial CP1 measurement for the specified 5-trial sample, not a general performance claim beyond that sample.

No CP2 work was started.
