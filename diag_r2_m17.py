from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from collections import Counter

import daily_engine
from accounting import balance_sheet_snapshot


ROOT = Path(__file__).resolve().parent
TEST_FILE = ROOT / "tests" / "test_acceptance_16_v2.py"
import sys
sys.path.insert(0, str(ROOT / "tests"))


def load_tests():
    spec = importlib.util.spec_from_file_location("acceptance_v2_diag", TEST_FILE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load acceptance v2 tests")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def diagnostics(project):
    snapshot = balance_sheet_snapshot(project)
    final_equity = project.final_net_project_equity
    total_equity = snapshot["Total_Equity"]
    state_counts = Counter(b.current_state.value for b in project.bikes)
    nbv_by_state = {}
    for bike in project.bikes:
        key = bike.current_state.value
        nbv_by_state[key] = nbv_by_state.get(key, 0) + bike.net_book_value
    owned_pending = [
        b.bike_id for b in project.bikes
        if b.current_state.value == "OWNED_TRANSFERRED"
        and b.pending_writeoff_today
    ]
    owned_positive = [
        b.bike_id for b in project.bikes
        if b.current_state.value == "OWNED_TRANSFERRED"
        and b.net_book_value > 0
    ]
    nonheld_positive = [
        {
            "bike_id": b.bike_id,
            "state": b.current_state.value,
            "net_book_value": b.net_book_value,
        }
        for b in project.bikes
        if b.current_state.value != "HELD_AS_ASSET"
        and b.net_book_value > 0
    ]
    held_nbv = sum(
        b.net_book_value for b in project.bikes
        if b.current_state.value == "HELD_AS_ASSET"
    )
    nonheld_nbv = sum(
        b.net_book_value for b in project.bikes
        if b.current_state.value != "HELD_AS_ASSET"
    )
    explained = (
        project.accounts_receivable
        + project.guarantee_claim_receivable
        + nonheld_nbv
    )
    classification = []
    if project.accounts_receivable:
        classification.append("AR")
    if project.guarantee_claim_receivable:
        classification.append("GCR")
    if nonheld_nbv:
        classification.append("non-HELD NBV")
    if not classification:
        classification.append("other")
    return {
        "Final_Net_Project_Equity": final_equity,
        "Total_Equity": total_equity,
        "Total_Assets": snapshot["Total_Assets"],
        "Capital": project.capital,
        "Retained_Earnings": project.retained_earnings,
        "project_cash": project.project_cash,
        "accounts_receivable": project.accounts_receivable,
        "guarantee_claim_receivable": project.guarantee_claim_receivable,
        "gross_bike_assets": project.gross_bike_assets,
        "accumulated_depreciation": project.accumulated_depreciation,
        "held_nbv": held_nbv,
        "nonheld_nbv": nonheld_nbv,
        "nbv_by_state": nbv_by_state,
        "state_counts": dict(state_counts),
        "owned_pending_writeoff": owned_pending,
        "owned_positive_nbv": owned_positive,
        "nonheld_positive_nbv_bikes": nonheld_positive,
        "difference_Total_Equity_minus_Final": total_equity - final_equity,
        "difference_reconstructed_AR_plus_GCR_plus_nonheld_NBV": explained,
        "classification": " + ".join(classification),
        "balance_difference": snapshot["Balance_Difference"],
    }


def run_one(fn, name):
    original = daily_engine._m17
    captured = {}

    def diagnostic_m17(project, current_date, opening):
        try:
            return original(project, current_date, opening)
        except AssertionError:
            captured.update(diagnostics(project))
            raise

    daily_engine._m17 = diagnostic_m17
    try:
        fn()
    except AssertionError as exc:
        print(f"TEST={name}")
        print(f"FAIL_TEXT={exc}")
        print(json.dumps(captured, ensure_ascii=False, sort_keys=True, indent=2))
        return captured
    finally:
        daily_engine._m17 = original
    raise AssertionError(f"{name} did not fail at M17")


def main():
    tests = load_tests()
    cases = [
        ("45", tests.test_045_يوم_النضج_يستحق_ايجارا_عاديا),
        ("90", tests.test_090_تحصيل_الثانوي_قبل_الاغلاق_في_نفس_اليوم),
        ("94", tests.test_094_انشاء_مطالبة_ADMINISTRATIVE_CLOSURE_للمتأخرات),
    ]
    results = {}
    for name, fn in cases:
        results[name] = run_one(fn, name)
    all_equal = len({json.dumps(v, sort_keys=True) for v in results.values()}) == 1
    print("ALL_THREE_HAVE_IDENTICAL_DIAGNOSTIC_VALUES=" + str(all_equal))
    print("CLASSIFICATIONS=" + json.dumps(
        {k: v["classification"] for k, v in results.items()},
        ensure_ascii=False,
        sort_keys=True,
    ))


if __name__ == "__main__":
    main()
