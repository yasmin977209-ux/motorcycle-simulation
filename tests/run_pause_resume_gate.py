from __future__ import annotations

import hashlib
import json
import pickle
import tempfile
from datetime import date, timedelta

from daily_engine import create_initial_project, run_day


SCENARIO_ID = "C100_G100"
COLLECTION_PROBABILITY = 1.0
RECOVERY_RATE_PCT = 100
TRIAL_ID = 1
START_DATE = date(2027, 1, 1)
CHECKPOINT_DATE = date(2027, 1, 15)
END_DATE = date(2027, 2, 15)


def run_range(project, first: date, last: date) -> None:
    current = first
    while current <= last:
        run_day(
            project,
            current,
            collection_probability=COLLECTION_PROBABILITY,
            scenario_id=SCENARIO_ID,
            trial_id=TRIAL_ID,
        )
        current += timedelta(days=1)


def state_fingerprint(project) -> str:
    payload = pickle.dumps(project, protocol=5)
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    baseline = create_initial_project(recovery_rate_pct=RECOVERY_RATE_PCT)
    run_range(baseline, START_DATE, END_DATE)
    baseline_hash = state_fingerprint(baseline)

    paused = create_initial_project(recovery_rate_pct=RECOVERY_RATE_PCT)
    run_range(paused, START_DATE, CHECKPOINT_DATE)

    with tempfile.NamedTemporaryFile(prefix="motorcycle-state-", suffix=".pkl") as handle:
        handle.write(pickle.dumps(paused, protocol=5))
        handle.flush()
        handle.seek(0)
        restored = pickle.loads(handle.read())

    run_range(restored, CHECKPOINT_DATE + timedelta(days=1), END_DATE)
    resumed_hash = state_fingerprint(restored)

    result = {
        "gate": "pause_resume_exact",
        "scenario_id": SCENARIO_ID,
        "checkpoint_date": CHECKPOINT_DATE.isoformat(),
        "end_date": END_DATE.isoformat(),
        "baseline_sha256": baseline_hash,
        "resumed_sha256": resumed_hash,
        "exact_match": baseline_hash == resumed_hash,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if baseline_hash != resumed_hash:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
