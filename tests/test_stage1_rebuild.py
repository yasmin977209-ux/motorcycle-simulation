from datetime import date
from constants import *
from entities import *

def test_reference_constants():
    assert PROJECT_START_DATE == date(2027, 1, 1)
    assert INITIAL_FLEET_PURCHASE_DATE == date(2026, 12, 26)
    assert INITIAL_FLEET_READY_DATE == date(2027, 1, 1)
    assert INITIAL_FLEET_DELIVERY_DATE == date(2027, 1, 2)
    assert BIKE_PREP_SCHEDULE_DAYS == 6
    assert PRIMARY_CONTRACT_MONTHS == 24
    assert EXPANSION_CUTOFF_DATE == date(2030, 12, 31)
    assert TOTAL_CAPITAL == 3_700_000
    assert BIKE_GROSS_ASSET_COST == 360_000
    assert OPENING_BIKE_ASSETS == 3_600_000
    assert OPENING_RETAINED_LOSS == -100_000
    assert INITIAL_FLEET_SIZE == 10
    assert GUARANTEE_RECOVERY_RATES == (100, 70, 50, 30, 0)
    assert len(COLLECTION_PROBABILITIES) * len(GUARANTEE_RECOVERY_RATES) == 25

def test_entity_enums_are_reference_closed():
    assert len(BikeState) == 11
    assert "TERMINATION_PENDING" not in {x.value for x in BikeState}
    assert "MINI_PREP" not in {x.value for x in BikeState}
    assert "PENDING_RECALL" not in {x.value for x in BikeState}
    assert "GUARANTEE_PENDING" not in {x.value for x in BikeState}
    assert len(EventType) == 24

def test_opening_project_shell():
    p = Project.opening()
    assert p.project_cash == 0
    assert p.gross_bike_assets == 3_600_000
    assert p.capital == 3_700_000
    assert p.retained_earnings == -100_000
    assert p.partner1_reinvestment_balance == 0
    assert p.partner2_reinvestment_balance == 0
    assert not p.bikes
    assert not p.contracts
    assert not p.guarantee_claims
    assert not p.receivables
    assert not p.event_log

# GitHub execution verification marker

# PR verification marker 2

# PR synchronization trigger
