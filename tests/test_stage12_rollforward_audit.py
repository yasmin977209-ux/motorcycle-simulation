import numpy as np

from scripts.stage12_validate_rollforward import invariant_masks


def _balanced_columns():
    return {
        "Opening_Cash": np.array([0, 1500], dtype=np.int64),
        "cash_inflows": np.array([1500, 0], dtype=np.int64),
        "cash_outflows": np.array([0, 500], dtype=np.int64),
        "Closing_Cash": np.array([1500, 1000], dtype=np.int64),
        "Opening_AR": np.array([0, 1000], dtype=np.int64),
        "ar_accruals": np.array([1000, 0], dtype=np.int64),
        "ar_collections": np.array([0, 500], dtype=np.int64),
        "ar_transfers_to_guarantee": np.array([0, 0], dtype=np.int64),
        "Closing_AR": np.array([1000, 500], dtype=np.int64),
        "Opening_Gross_Bike_Assets": np.array([3600000, 3600000], dtype=np.int64),
        "capitalized_purchases_and_customs": np.array([0, 0], dtype=np.int64),
        "gross_writeoffs_on_ownership": np.array([0, 0], dtype=np.int64),
        "Closing_Gross_Bike_Assets": np.array([3600000, 3600000], dtype=np.int64),
        "Opening_Accumulated_Depreciation": np.array([0, 50], dtype=np.int64),
        "depreciation_expense": np.array([50, 50], dtype=np.int64),
        "ad_removed_on_writeoff": np.array([0, 0], dtype=np.int64),
        "Closing_Accumulated_Depreciation": np.array([50, 100], dtype=np.int64),
        "Net_Bike_Assets": np.array([3599950, 3599900], dtype=np.int64),
        "Capital": np.array([3700000, 3700000], dtype=np.int64),
        "Retained_Earnings": np.array([-97550, -98600], dtype=np.int64),
        "Opening_Equity": np.array([3600000, 3602450], dtype=np.int64),
        "Operating_Net_Profit": np.array([2450, -1050], dtype=np.int64),
        "Closing_Equity": np.array([3602450, 3601400], dtype=np.int64),
        "Guarantee_Claim_Receivable": np.array([0, 0], dtype=np.int64),
        "Total_Assets": np.array([3602450, 3601400], dtype=np.int64),
        "Liabilities": np.array([0, 0], dtype=np.int64),
        "Balance_Difference": np.array([0, 0], dtype=np.int64),
    }


def test_all_reference_defined_accounting_identities_pass_for_balanced_rows():
    masks = invariant_masks(_balanced_columns())
    assert len(masks) == 11
    assert all(bool(mask.all()) for mask in masks.values())


def test_cash_rollforward_violation_is_detected():
    columns = _balanced_columns()
    columns["Closing_Cash"][1] = 999
    masks = invariant_masks(columns)
    assert not bool(masks["cash_rollforward"][1])
    assert not bool(masks["total_assets_components"][1])
    assert not bool(masks["balance_difference_zero"][1])


def test_zero_liabilities_is_an_explicit_gate():
    columns = _balanced_columns()
    columns["Liabilities"][0] = 1
    masks = invariant_masks(columns)
    assert not bool(masks["liabilities_zero"][0])
