import numpy as np

from scripts.stage12_validate_closure import CUTOFF_DATE, closure_row_masks


def _base():
    return {
        "Active_Bikes": np.array([1, 0], dtype=np.int64),
        "Owned_Transferred_Bikes": np.array([0, 1], dtype=np.int64),
        "Pending_Claims": np.array([1, 0], dtype=np.int64),
        "Closing_AR": np.array([100, 0], dtype=np.int64),
        "Guarantee_Claim_Receivable": np.array([100, 0], dtype=np.int64),
        "Balance_Difference": np.array([0, 0], dtype=np.int64),
        "Total_Assets": np.array([1000, 900], dtype=np.int64),
        "Closing_Equity": np.array([1000, 900], dtype=np.int64),
        "Liabilities": np.array([0, 0], dtype=np.int64),
    }


def test_valid_preclose_and_terminal_rows_pass():
    columns = _base()
    dates = np.array(["2031-01-01", "2031-01-02"], dtype="datetime64[D]")
    final_dates = np.array(["2031-01-02", "2031-01-02"], dtype="datetime64[D]")
    stopped = np.array([False, True])
    masks = closure_row_masks(columns, dates, final_dates, stopped)
    assert len(masks) == 13
    assert all(bool(mask.all()) for mask in masks.values())


def test_closure_on_expansion_cutoff_is_rejected():
    columns = _base()
    dates = np.array(["2030-12-31"], dtype="datetime64[D]")
    final_dates = np.array(["2030-12-31"], dtype="datetime64[D]")
    stopped = np.array([True])
    masks = closure_row_masks({k: v[:1] for k, v in columns.items()}, dates, final_dates, stopped)
    assert not bool(masks["final_close_date_after_expansion_cutoff"][0])
    assert CUTOFF_DATE == np.datetime64("2030-12-31", "D")


def test_terminal_pending_claim_fails_gate():
    columns = _base()
    columns["Pending_Claims"][1] = 1
    dates = np.array(["2031-01-01", "2031-01-02"], dtype="datetime64[D]")
    final_dates = np.array(["2031-01-02", "2031-01-02"], dtype="datetime64[D]")
    stopped = np.array([False, True])
    masks = closure_row_masks(columns, dates, final_dates, stopped)
    assert not bool(masks["terminal_no_pending_claims"][1])


def test_stopped_flag_must_match_final_close_date():
    columns = _base()
    dates = np.array(["2031-01-01", "2031-01-02"], dtype="datetime64[D]")
    final_dates = np.array(["2031-01-02", "2031-01-02"], dtype="datetime64[D]")
    stopped = np.array([True, True])
    masks = closure_row_masks(columns, dates, final_dates, stopped)
    assert not bool(masks["simulation_stopped_matches_final_close_date"][0])
