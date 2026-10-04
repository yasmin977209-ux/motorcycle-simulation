# Stage 6.5 — CP3 Evidence

## Result

CP3: PASS

- Run ID: 37203438351
- Successful code commit: 8e1e4155f91163e32f0cf472b6fb73a67f6d4227
- Branch: tmp/stage6.5-cp3-20261003
- Main: 2de92e2c8d484d4682990fd3d6381d6aa60227b4
- CP2 artifact source Run ID: 37138843161 (temporary fixed source approved for CP3)
- CP2 artifacts downloaded: 16/16
- CP3 artifact ID: 11304130534

## Aggregate stdout

```json
{
  "aggregate_sha256": "c09d39cd3f79e9460d16df4fc2a6a47b6b029983e2f596de4af4009bc169a14a",
  "max_chunk_elapsed": 1488.361695994,
  "max_parallel": 16,
  "statistics": {
    "Max": 209837500,
    "Mean": 209084541.0,
    "Min": 208351000,
    "P10": 209026500.0,
    "P50": 209125500.0,
    "P90": 209199500.0,
    "Probability_of_Accounting_Loss": 0.0,
    "Std": 178837.62626751675
  },
  "total_trials": 6000,
  "wall_clock_estimate": 1488.361695994
}
```

## Verification stdout

```json
{
  "aggregate_fingerprint": "c09d39cd3f79e9460d16df4fc2a6a47b6b029983e2f596de4af4009bc169a14a",
  "aggregate_fingerprint_match": true,
  "all_match": true,
  "expected_cp2_aggregate_sha256": "c09d39cd3f79e9460d16df4fc2a6a47b6b029983e2f596de4af4009bc169a14a",
  "per_trial_fingerprint_match": true,
  "per_trial_match": {
    "1": true,
    "1000": true,
    "2000": true,
    "3000": true,
    "4000": true,
    "500": true,
    "5000": true,
    "5500": true,
    "5900": true,
    "6000": true
  },
  "rerun_sample_fingerprint": "73a008a596a4447ac7326e9991c106f770f4be3d2e642c7bd2112fd74e14e12c",
  "sample_trial_ids": [
    1,
    500,
    1000,
    2000,
    3000,
    4000,
    5000,
    5500,
    5900,
    6000
  ],
  "stored_sample_fingerprint": "73a008a596a4447ac7326e9991c106f770f4be3d2e642c7bd2112fd74e14e12c"
}
```

## R8

| بوابة | المتوقع | الفعلي | الحكم |
|---|---|---|---|
| aggregate_sha256 | c09d39cd3f79e9460d16df4fc2a6a47b6b029983e2f596de4af4009bc169a14a | c09d39cd3f79e9460d16df4fc2a6a47b6b029983e2f596de4af4009bc169a14a | PASS |
| total_trials | 6000 | 6000 | PASS |
| 10/10 per_trial_match | true | 10/10 true | PASS |
| per_trial_fingerprint_match | true | true | PASS |
| aggregate_fingerprint_match | true | true | PASS |
| all_match | true | true | PASS |
| max_parallel | 16 | 16 | PASS |

## Required aggregate statistics

- P10 = 209026500.0
- P50 = 209125500.0
- P90 = 209199500.0
- Mean = 209084541.0
- Std = 178837.62626751675
- Min = 208351000
- Max = 209837500
- Probability_of_Accounting_Loss = 0.0
- max_chunk_elapsed = 1488.361695994 s
- wall_clock_estimate = 1488.361695994 s
- max_parallel = 16

## Execution path

The CP3 workflow downloads the 16 approved CP2 chunk artifacts from Run 37138843161, executes the aggregate with `python -m scripts.stage6_5_aggregate`, then executes verification with `python -m scripts.stage6_5_verify_cp3`.

Both aggregate and verification completed successfully. No production file, CP2 workflow, or `scripts/stage6_5_run_chunk.py` was modified during CP3.
