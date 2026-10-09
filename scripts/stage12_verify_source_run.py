from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the pinned CP-12-B GitHub Actions run.")
    parser.add_argument("path", help="JSON file returned by GitHub Actions REST API")
    args = parser.parse_args()
    run = json.loads(Path(args.path).read_text(encoding="utf-8"))
    expected_id = int(os.environ["CP12B_RUN_ID"])
    expected_sha = os.environ["CP12B_RUN_SHA"]
    assert run.get("id") == expected_id, f"unexpected run id: {run.get('id')}"
    assert run.get("status") == "completed" and run.get("conclusion") == "success", run
    assert run.get("head_sha") == expected_sha, f"unexpected source SHA: {run.get('head_sha')}"
    assert run.get("head_branch") == "tmp/stage12-b3-25jobs-20261009", run
    print(json.dumps({
        "run_id": run["id"],
        "conclusion": run["conclusion"],
        "head_sha": run["head_sha"],
        "head_branch": run["head_branch"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
