# Stage 6.5 — CP4 Evidence

## Result

CP4: PASS

- Run ID: 37203903230
- Code commit: 857ecd3fcba80f5f8cac3f1f08e92ea035a6700f
- Branch base: CP3 head fcbaeb9f0eb006eb4d2dfacb165d815e3c743c3b
- Branch: tmp/stage6.5-cp4-20261003

CP4 branched from CP3 head (fcbaeb9f) because log_events lives on Stage 6.5 branch chain, not on main. This is a documented deviation from the default 'branch from main' policy.

## R8 measurement result

Scenario: C050_G100
Trial IDs: 1, 2, 3, 4, 5

| trial_id | T_True (s) | T_False (s) | فرق% | RSS_True (KB) | RSS_False (KB) | SHA match | event_log_True | event_log_False |
|---:|---:|---:|---:|---:|---:|:---:|---:|---:|
| 1 | 3.318831 | 2.821201 | -14.994128 | 118340 | 39228 | true | 262603 | 0 |
| 2 | 3.338269 | 2.851678 | -14.576124 | 118348 | 39364 | true | 262603 | 0 |
| 3 | 3.395338 | 2.864497 | -15.634410 | 118440 | 39472 | true | 262603 | 0 |
| 4 | 3.310046 | 2.821165 | -14.769605 | 118444 | 39520 | true | 262603 | 0 |
| 5 | 3.326494 | 2.830677 | -14.905088 | 118368 | 39472 | true | 262603 | 0 |

### Means

- Mean T_True = 3.3377955780000006 s
- Mean T_False = 2.8378438517999998 s
- Time reduction = 14.978500465854495%
- Mean RSS_True = 118388.0 KB
- Mean RSS_False = 39411.2 KB
- RSS reduction = 66.71013954116971%
- 5/5 SHA matches = true
- All True event_log lengths > 0 = true
- All False event_log lengths = 0 = true

## Comparison with CP1

CP1 C085_G100:
- Time reduction = 13.804284889905377%
- RSS reduction = 67.6692862673%

CP4 C050_G100:
- Time reduction = 14.978500465854495%
- RSS reduction = 66.71013954116971%

Differences:
- Time reduction: +1.174215575949118 percentage points versus CP1.
- RSS reduction: -0.9591467261302853 percentage points versus CP1.

The direction is identical across both configurations: disabling event logging reduced both elapsed time and RSS. The measured reductions are of similar magnitude, so the log_events reduction is stable across C085_G100 and C050_G100 within these two five-trial samples.

## Comparison with Stage 6 C050_G100 trial 5

Stage 6 Round 3 stdout:
- C050_G100 trial 5 RSS = 190740 KB
- C050_G100 trial 5 elapsed = 5.379037712000013 s

CP4:
- Mean RSS_True = 118388.0 KB, which is 37.93226381461675% below the Stage 6 trial-5 RSS.
- Mean RSS_False = 39411.2 KB, which is 79.33773723393101% below the Stage 6 trial-5 RSS.

## CP4 stdout summary

{"all_false_event_log_zero": true, "all_sha_match": true, "all_true_event_log_positive": true, "mean_RSS_False_KB": 39411.2, "mean_RSS_True_KB": 118388.0, "mean_T_False_s": 2.8378438517999998, "mean_T_True_s": 3.3377955780000006, "rss_reduction_pct": 66.71013954116971, "scenario_id": "C050_G100", "time_reduction_pct": 14.978500465854495, "trial_count": 5}
