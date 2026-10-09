import argparse, hashlib, json
from datetime import date, timedelta
from pathlib import Path

import pyarrow.parquet as pq

EXPECTED_GLOBAL = "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"
EXPECTED = {f"C{c:03}_G{g:03}": (1 if c == 100 else 550)
            for c in (100, 85, 70, 50, 30) for g in (100, 70, 50, 30, 0)}
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    root = Path(p.parse_args().root)
    files = sorted(root.rglob("*.parquet"))
    if len(files) != 225:
        raise SystemExit(f"expected 225 parquet files, got {len(files)}")
    keys, trials, total_rows, sources = set(), [], 0, set()
    for path in files:
        rows = pq.read_table(path, columns=["scenario_id", "trial_id", "date", "source_sha", "result_sha256"]).to_pylist()
        state = None
        for r in rows:
            total_rows += 1
            sources.add(r["source_sha"])
            key, d = (r["scenario_id"], int(r["trial_id"])), date.fromisoformat(r["date"])
            if state is None or key != state[0]:
                if state is not None:
                    if state[3] != (state[2] - state[1]).days + 1:
                        raise SystemExit(f"daily gap/duplicate: {state[0]}")
                    trials.append((state[0][0], state[0][1], state[4]))
                if key in keys:
                    raise SystemExit(f"duplicate trial: {key}")
                keys.add(key)
                state = [key, d, d, 1, r["result_sha256"]]
            else:
                if d != state[2] + timedelta(days=1):
                    raise SystemExit(f"daily gap/duplicate: {key} {d}")
                if r["result_sha256"] != state[4]:
                    raise SystemExit(f"trial fingerprint drift: {key}")
                state[2], state[3] = d, state[3] + 1
        if state is not None:
            if state[3] != (state[2] - state[1]).days + 1:
                raise SystemExit(f"daily gap/duplicate: {state[0]}")
            trials.append((state[0][0], state[0][1], state[4]))
    if sources != {SOURCE_SHA} or len(trials) != 11005:
        raise SystemExit("source or trial-count mismatch")
    counts = {s: 0 for s in EXPECTED}
    for sc, tid, _ in trials:
        if sc not in EXPECTED or not 1 <= tid <= EXPECTED[sc]:
            raise SystemExit(f"trial coverage failure: {sc} {tid}")
        counts[sc] += 1
    if counts != EXPECTED or len(keys) != 11005:
        raise SystemExit("trial coverage failure")
    payload = "".join(f"{sc}|{tid}|{sha}\n" for sc, tid, sha in sorted(trials))
    reproduced = hashlib.sha256(payload.encode()).hexdigest()
    if reproduced != EXPECTED_GLOBAL:
        raise SystemExit(f"global fingerprint mismatch: {reproduced}")
    out = Path("docs/stage12/reproduction_result.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "created_by_cp": "CP-12-B2", "overall_result": "PASS",
        "original_global_sha256": EXPECTED_GLOBAL, "reproduced_global_sha256": reproduced,
        "match": "YES", "total_trials": len(trials), "total_daily_rows": total_rows,
        "parquet_files": len(files), "scenarios": 25, "retries": 0
    }, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
