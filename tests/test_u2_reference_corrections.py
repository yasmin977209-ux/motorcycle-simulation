from datetime import date

import daily_engine
from entities import ContractType


def test_168_first_eligible_friday_is_stored_per_secondary_contract() -> None:
    project = daily_engine.create_initial_project()
    bike = project.bikes[0]

    saturday = daily_engine._new_contract(
        project, bike, ContractType.SECONDARY, date(2027, 1, 2)
    )
    tuesday = daily_engine._new_contract(
        project, bike, ContractType.SECONDARY, date(2027, 1, 5)
    )

    assert saturday.first_eligible_friday_date == date(2027, 1, 8)
    assert tuesday.first_eligible_friday_date == date(2027, 1, 15)
    assert saturday.friday_counter == 0
    assert tuesday.friday_counter == 0
