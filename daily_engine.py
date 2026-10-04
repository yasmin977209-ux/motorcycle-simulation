"""Chapter 12 daily engine rebuilt from the authoritative reference."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Callable

import constants
import dateutils
import rng
from accounting import (
    accrue_rent,
    assert_balance_sheet_balanced,
    record_daily_rollforwards,
)
from closure import execute_dynamic_closure
from entities import (
    Bike,
    BikeSource,
    BikeState,
    ClaimStatus,
    Contract,
    ContractStatus,
    ContractType,
    EventLogEntry,
    EventType,
    Guarantor,
    Project,
    ReceivableEntry,
    ReceivableSource,
    ReceivableStatus,
    Tenant,
    TenantType,
    add_contract,
    contract_of,
)
from collection import apply_ordinary_collection
from guarantee import create_guarantee_claim
from partner_equity import (
    assert_memo_nonnegative,
    consume_partner1_for_expansion,
    record_eligible_inflow,
)
from friday import apply_friday_fee_and_oil
from settlement import (
    apply_legacy_debt_collection,
    apply_settlement_rent,
)
from state_machine import derive_state_from_balance


POSSESSION_STATES = frozenset(
    {
        BikeState.ACTIVE_PRIMARY,
        BikeState.WAITING_PRIMARY,
        BikeState.NOTICE_PRIMARY,
        BikeState.GRACE_PRIMARY,
        BikeState.POST_MATURITY_SETTLEMENT,
        BikeState.ACTIVE_SECONDARY,
        BikeState.NOTICE_SECONDARY,
    }
)


def create_initial_project(recovery_rate_pct: int = 100) -> Project:
    project = Project.opening()
    for index in range(1, constants.INITIAL_FLEET_SIZE + 1):
        project.bikes.append(
            Bike(
                bike_id=f"BK{index:04d}",
                source=BikeSource.INITIAL,
                purchase_date=constants.INITIAL_FLEET_PURCHASE_DATE,
                scheduled_ready_date=constants.INITIAL_FLEET_READY_DATE,
                funding_completion_date=constants.INITIAL_FLEET_PURCHASE_DATE,
                actual_ready_date=constants.INITIAL_FLEET_READY_DATE,
                prep_paid=True,
                customs_paid=True,
                delivery_date=None,
                gross_cost=constants.BIKE_GROSS_ASSET_COST,
                accumulated_depreciation=0,
                net_book_value=constants.BIKE_GROSS_ASSET_COST,
                current_state=BikeState.PREP,
            )
        )
    return project


def _new_contract(
    project: Project,
    bike: Bike,
    contract_type: ContractType,
    current_date: date,
) -> Contract:
    contract_id = f"CT{len(project.contracts) + 1:08d}"
    tenant_id = f"TN{len(project.tenants) + 1:08d}"
    guarantor_id = f"GR{len(project.guarantors) + 1:08d}"
    contract = Contract(
        contract_id=contract_id,
        bike_id=bike.bike_id,
        tenant_id=tenant_id,
        guarantor_id=guarantor_id,
        contract_type=contract_type,
        daily_rate=(
            constants.PRIMARY_DAILY_RENT
            if contract_type is ContractType.PRIMARY
            else constants.SECONDARY_DAILY_RENT
        ),
        start_date=current_date,
        maturity_date=(
            dateutils.primary_maturity_date(current_date)
            if contract_type is ContractType.PRIMARY
            else None
        ),
    )
    tenant = Tenant(
        tenant_id=tenant_id,
        tenant_type=(
            TenantType.ORIGINAL
            if contract_type is ContractType.PRIMARY
            else TenantType.SECONDARY
        ),
        contract_id=contract_id,
        guarantor_id=guarantor_id,
        start_date=current_date,
    )
    guarantor = Guarantor(
        guarantor_id=guarantor_id,
        related_contract_id=contract_id,
        related_tenant_id=tenant_id,
    )
    add_contract(project, contract)
    project.tenants.append(tenant)
    project.guarantors.append(guarantor)
    return contract


def _event(
    project: Project,
    current_date: date,
    bike: Bike,
    event_type: EventType,
    previous_state: BikeState | None = None,
    new_state: BikeState | None = None,
    contract_id: str | None = None,
    amount: int | None = None,
) -> None:
    if not project.log_events:
        return

    event = EventLogEntry(
        event_id=f"EV{len(project.event_log) + 1:08d}",
        date=current_date,
        bike_id=bike.bike_id,
        event_type=event_type,
        previous_state=previous_state,
        new_state=new_state,
        contract_id=contract_id,
        amount_if_applicable=amount,
    )
    project.event_log.append(event)
    bike.lifecycle_history.append(event)


def _new_receivable(
    project: Project,
    bike: Bike,
    contract: Contract,
    amount: int,
) -> ReceivableEntry:
    receivable_id = f"RC{len(project.receivables) + 1:08d}"
    receivable = ReceivableEntry(
        receivable_id=receivable_id,
        bike_id=bike.bike_id,
        contract_id=contract.contract_id,
        tenant_id=contract.tenant_id,
        source=ReceivableSource.SETTLEMENT_LEGACY_DEBT,
        original_amount=amount,
        collected_amount=0,
        remaining_amount=amount,
        status=ReceivableStatus.OUTSTANDING,
        created_date=None,
    )
    project.receivables.append(receivable)
    bike.active_settlement_receivable_id = receivable_id
    return receivable


def _receivable_of(project: Project, bike: Bike) -> ReceivableEntry | None:
    rid = bike.active_settlement_receivable_id
    if rid is None:
        return None
    return next(
        (item for item in project.receivables if item.receivable_id == rid),
        None,
    )


def _begin_day(project: Project) -> dict[str, int]:
    opening = {
        "Opening_Cash": project.project_cash,
        "Opening_AR": project.accounts_receivable,
        "Opening_Gross_Bike_Assets": project.gross_bike_assets,
        "Opening_Accumulated_Depreciation": project.accumulated_depreciation,
        "Opening_Equity": project.capital + project.retained_earnings,
    }
    _ensure_day_metrics(project, reset=True)
    return opening


def _ensure_day_metrics(project: Project, *, reset: bool = False) -> None:
    if hasattr(project, "_day_metrics") and not reset:
        return
    project._day_metrics = {
        "cash_inflows": 0,
        "cash_outflows": 0,
        "ar_accruals": 0,
        "ar_collections": 0,
        "ar_transfers_to_guarantee": 0,
        "capitalized_purchases_and_customs": 0,
        "gross_writeoffs_on_ownership": 0,
        "depreciation_expense": 0,
        "ad_removed_on_writeoff": 0,
    }


def _cash_in(project: Project, amount: int) -> None:
    _ensure_day_metrics(project)
    project.project_cash += amount
    project._day_metrics["cash_inflows"] += amount


def _cash_out(project: Project, amount: int) -> None:
    _ensure_day_metrics(project)
    project.project_cash -= amount
    project._day_metrics["cash_outflows"] += amount


def _ar_collect(project: Project, amount: int) -> None:
    _ensure_day_metrics(project)
    project.accounts_receivable -= amount
    project._day_metrics["ar_collections"] += amount


def _ar_transfer(project: Project, amount: int) -> None:
    _ensure_day_metrics(project)
    project.accounts_receivable -= amount
    project._day_metrics["ar_transfers_to_guarantee"] += amount


def _capitalize(project: Project, amount: int) -> None:
    _ensure_day_metrics(project)
    project.gross_bike_assets += amount
    project._day_metrics["capitalized_purchases_and_customs"] += amount


def _gross_writeoff(project: Project, amount: int) -> None:
    _ensure_day_metrics(project)
    project.gross_bike_assets -= amount
    project._day_metrics["gross_writeoffs_on_ownership"] += amount


def _dep(project: Project, amount: int) -> None:
    _ensure_day_metrics(project)
    project.accumulated_depreciation += amount
    project._day_metrics["depreciation_expense"] += amount


def _ad_remove(project: Project, amount: int) -> None:
    _ensure_day_metrics(project)
    project.accumulated_depreciation -= amount
    project._day_metrics["ad_removed_on_writeoff"] += amount


def _has_prep_underfunded(project: Project) -> bool:
    return any(
        bike.current_state is BikeState.PREP
        and (not bike.prep_paid or not bike.customs_paid)
        for bike in project.bikes
    )


def _m2(project: Project, current_date: date) -> None:
    _ensure_day_metrics(project)
    if not dateutils.is_business_day(current_date):
        return

    for bike in sorted(
        (b for b in project.bikes if b.current_state is BikeState.PREP),
        key=lambda b: (b.purchase_date, b.bike_id),
    ):
        if (
            not bike.prep_paid
            and project.project_cash >= constants.PREP_OPERATING_EXPENSE_PER_BIKE
            and project.partner1_reinvestment_balance
            >= constants.PREP_OPERATING_EXPENSE_PER_BIKE
        ):
            _cash_out(
                project,
                constants.PREP_OPERATING_EXPENSE_PER_BIKE,
            )
            consume_partner1_for_expansion(
                project,
                constants.PREP_OPERATING_EXPENSE_PER_BIKE,
            )
            project.expense_prep += constants.PREP_OPERATING_EXPENSE_PER_BIKE
            bike.prep_paid = True
        if (
            not bike.customs_paid
            and project.project_cash >= constants.CUSTOMS_AND_REGISTRATION_COST
            and project.partner1_reinvestment_balance
            >= constants.CUSTOMS_AND_REGISTRATION_COST
        ):
            _cash_out(project, constants.CUSTOMS_AND_REGISTRATION_COST)
            consume_partner1_for_expansion(
                project,
                constants.CUSTOMS_AND_REGISTRATION_COST,
            )
            _capitalize(
                project,
                constants.CUSTOMS_AND_REGISTRATION_COST,
            )
            bike.gross_cost += constants.CUSTOMS_AND_REGISTRATION_COST
            bike.customs_paid = True
        if bike.prep_paid and bike.customs_paid and bike.actual_ready_date is None:
            bike.funding_completion_date = current_date
            bike.actual_ready_date = max(
                bike.scheduled_ready_date,
                bike.funding_completion_date,
            )

    if (
        current_date <= constants.EXPANSION_CUTOFF_DATE
        and not _has_prep_underfunded(project)
    ):
        while (
            project.project_cash >= constants.EXPANSION_PURCHASE_CASH_THRESHOLD
            and project.partner1_reinvestment_balance
            >= constants.EXPANSION_PURCHASE_CASH_THRESHOLD
        ):
            _cash_out(project, constants.BIKE_BASE_PURCHASE_COST)
            consume_partner1_for_expansion(
                project,
                constants.BIKE_BASE_PURCHASE_COST,
            )
            _capitalize(
                project,
                constants.BIKE_BASE_PURCHASE_COST,
            )
            next_number = len(project.bikes) + 1
            project.bikes.append(
                Bike(
                    bike_id=f"BK{next_number:04d}",
                    source=BikeSource.EXPANSION,
                    purchase_date=current_date,
                    scheduled_ready_date=dateutils.scheduled_ready_date(
                        current_date
                    ),
                    gross_cost=constants.BIKE_BASE_PURCHASE_COST,
                    net_book_value=constants.BIKE_BASE_PURCHASE_COST,
                )
            )


def _m3(project: Project, current_date: date) -> None:
    if not dateutils.is_business_day(current_date):
        return
    for bike in project.bikes:
        if (
            bike.current_state is BikeState.PREP
            and bike.actual_ready_date is not None
            and current_date >= bike.actual_ready_date
        ):
            contract = _new_contract(
                project,
                bike,
                ContractType.PRIMARY,
                current_date,
            )
            bike.delivery_date = current_date
            bike.current_contract_id = contract.contract_id
            bike.current_tenant_id = contract.tenant_id
            bike.lifecycle_cycle_number = 1
            previous = bike.current_state
            bike.current_state = BikeState.ACTIVE_PRIMARY
            _event(
                project,
                current_date,
                bike,
                EventType.PRIMARY_CONTRACT_STARTED,
                previous,
                bike.current_state,
                contract.contract_id,
            )
        elif bike.current_state is BikeState.AVAILABLE_FOR_SECONDARY:
            contract = _new_contract(
                project,
                bike,
                ContractType.SECONDARY,
                current_date,
            )
            bike.delivery_date = current_date
            bike.current_contract_id = contract.contract_id
            bike.current_tenant_id = contract.tenant_id
            bike.secondary_cycle_count += 1
            bike.lifecycle_cycle_number += 1
            previous = bike.current_state
            bike.current_state = BikeState.ACTIVE_SECONDARY
            _event(
                project,
                current_date,
                bike,
                EventType.SECONDARY_CONTRACT_STARTED,
                previous,
                bike.current_state,
                contract.contract_id,
            )


def _m4(project: Project) -> dict[str, bool]:
    return {
        bike.bike_id: bike.current_state in POSSESSION_STATES
        for bike in project.bikes
    }


def _m5(project: Project, current_date: date) -> None:
    _ensure_day_metrics(project)
    if not dateutils.is_business_day(current_date):
        return
    for bike in list(project.bikes):
        contract = contract_of(project, bike)
        if contract is None:
            continue
        if bike.current_state in {
            BikeState.ACTIVE_PRIMARY,
            BikeState.WAITING_PRIMARY,
            BikeState.NOTICE_PRIMARY,
            BikeState.GRACE_PRIMARY,
        }:
            accrue_rent(project, contract)
            project._day_metrics["ar_accruals"] += contract.daily_rate
        elif bike.current_state in {
            BikeState.ACTIVE_SECONDARY,
            BikeState.NOTICE_SECONDARY,
        }:
            accrue_rent(project, contract)
            project._day_metrics["ar_accruals"] += contract.daily_rate
        elif bike.current_state is BikeState.POST_MATURITY_SETTLEMENT:
            result = apply_settlement_rent(
                current_date=current_date,
            )
            bike.settlement_rent_due_total += result.due
            bike.settlement_rent_collected_total += result.collected
            project.revenue_settlement += result.collected
            if result.cash_delta > 0:
                _cash_in(project, result.cash_delta)
            if result.collected > 0:
                record_eligible_inflow(project, result.collected)


def _m6(
    project: Project,
    current_date: date,
    possession: dict[str, bool],
) -> None:
    if not dateutils.is_friday(current_date):
        return
    for bike in project.bikes:
        if not possession.get(bike.bike_id, False):
            continue
        if bike.delivery_date is None:
            continue
        contract = contract_of(project, bike)
        if contract is None:
            continue
        result = apply_friday_fee_and_oil(
            bike.delivery_date,
            current_date,
            contract.friday_counter,
            True,
        )
        if not result.eligible:
            continue
        project.revenue_friday_fee += result.revenue_friday_fee
        contract.friday_counter = result.friday_counter_after
        if result.revenue_friday_fee:
            _cash_in(project, result.revenue_friday_fee)
            record_eligible_inflow(
                project,
                result.revenue_friday_fee,
            )
        if result.oil_service_expense:
            project.expense_oil_service += result.oil_service_expense
            _cash_out(project, result.oil_service_expense)


def _m7(
    project: Project,
    possession: dict[str, bool],
    current_date: date,
) -> None:
    for bike in project.bikes:
        if not possession.get(bike.bike_id, False):
            continue
        if bike.net_book_value <= 0:
            continue
        depreciation = min(
            constants.DEPRECIATION_RATE_PER_DAY,
            constants.MAX_DEPRECIATION - bike.accumulated_depreciation,
        )
        if depreciation <= 0:
            continue
        bike.accumulated_depreciation += depreciation
        bike.usage_days += 1
        bike.net_book_value = max(
            0,
            bike.gross_cost - bike.accumulated_depreciation,
        )
        _dep(project, depreciation)
        project.expense_depreciation += depreciation
        _event(
            project,
            current_date,
            bike,
            EventType.DEPRECIATION_RECORDED,
            bike.current_state,
            bike.current_state,
        )


def _collect_ordinary(
    project: Project,
    bike: Bike,
    contract: Contract,
    collection_probability: float,
    scenario_id: str,
    trial_id: int,
    master_seed: int,
    event_type: str,
) -> None:
    seed = rng.derive_seed(
        master_seed,
        scenario_id,
        trial_id,
        bike.bike_id,
        project._current_date,
        event_type,
    )
    if not rng.deterministic_success(collection_probability, seed):
        return
    result = apply_ordinary_collection(
        total_due=contract.total_due,
        total_paid=contract.total_paid,
        daily_rate=contract.daily_rate,
        success=True,
        current_date=project._current_date,
    )
    contract.total_paid = result.total_paid_after
    if result.cash_delta > 0:
        _cash_in(project, result.cash_delta)
    if result.collected > 0:
        _ar_collect(project, result.collected)
        record_eligible_inflow(project, result.collected)


def _m8(
    project: Project,
    current_date: date,
    collection_probability: float,
    scenario_id: str,
    trial_id: int,
    master_seed: int,
) -> None:
    if not dateutils.is_business_day(current_date):
        return
    project._current_date = current_date

    for bike in list(project.bikes):
        contract = contract_of(project, bike)
        if contract is None:
            continue
        if bike.current_state in {
            BikeState.ACTIVE_PRIMARY,
            BikeState.WAITING_PRIMARY,
            BikeState.NOTICE_PRIMARY,
            BikeState.GRACE_PRIMARY,
        }:
            _collect_ordinary(
                project,
                bike,
                contract,
                collection_probability,
                scenario_id,
                trial_id,
                master_seed,
                "PRIMARY_COLLECTION",
            )
        elif bike.current_state in {
            BikeState.ACTIVE_SECONDARY,
            BikeState.NOTICE_SECONDARY,
        }:
            _collect_ordinary(
                project,
                bike,
                contract,
                collection_probability,
                scenario_id,
                trial_id,
                master_seed,
                "SECONDARY_COLLECTION",
            )
        elif bike.current_state is BikeState.POST_MATURITY_SETTLEMENT:
            remaining = bike.settlement_legacy_debt_remaining
            if remaining is None or remaining <= 0:
                continue
            seed = rng.derive_seed(
                master_seed,
                scenario_id,
                trial_id,
                bike.bike_id,
                current_date,
                "LEGACY_DEBT_COLLECTION",
            )
            if not rng.deterministic_success(collection_probability, seed):
                continue
            result = apply_legacy_debt_collection(
                remaining_debt=remaining,
                success=True,
            )
            bike.settlement_legacy_debt_remaining = result.remaining_after
            if result.cash_delta > 0:
                _cash_in(project, result.cash_delta)
            if result.payment > 0:
                _ar_collect(project, result.payment)
            receivable = _receivable_of(project, bike)
            if receivable is not None:
                receivable.collected_amount += result.payment
                receivable.remaining_amount = bike.settlement_legacy_debt_remaining
                if receivable.remaining_amount == 0:
                    receivable.status = ReceivableStatus.SETTLED
            if result.payment > 0:
                record_eligible_inflow(project, result.payment)


def _m9(project: Project) -> None:
    for bike in project.bikes:
        contract = contract_of(project, bike)
        if contract is None:
            continue
        if bike.current_state in {
            BikeState.ACTIVE_PRIMARY,
            BikeState.WAITING_PRIMARY,
            BikeState.NOTICE_PRIMARY,
            BikeState.GRACE_PRIMARY,
        }:
            derived = derive_state_from_balance(
                contract.total_due - contract.total_paid,
                constants.PRIMARY_DAILY_RENT,
                ContractType.PRIMARY,
            )
            if derived is not None:
                bike.current_state = BikeState(derived)
        elif bike.current_state in {
            BikeState.ACTIVE_SECONDARY,
            BikeState.NOTICE_SECONDARY,
        }:
            derived = derive_state_from_balance(
                contract.total_due - contract.total_paid,
                constants.SECONDARY_DAILY_RENT,
                ContractType.SECONDARY,
            )
            if derived is not None:
                bike.current_state = BikeState(derived)


def _m11(
    project: Project,
    current_date: date,
    recovery_rate_pct: int,
) -> None:
    _ensure_day_metrics(project)
    for bike in list(project.bikes):
        contract = contract_of(project, bike)
        if contract is None:
            continue
        outstanding = contract.total_due - contract.total_paid

        if (
            bike.current_state
            in {
                BikeState.ACTIVE_PRIMARY,
                BikeState.WAITING_PRIMARY,
                BikeState.NOTICE_PRIMARY,
                BikeState.GRACE_PRIMARY,
            }
            and outstanding >= constants.PRIMARY_DEFAULT_AMOUNT
        ):
            claim_source = constants.CLAIM_SOURCE_PRIMARY_EARLY_TERMINATION
            event_type = EventType.PRIMARY_TERMINATED
            previous = bike.current_state
        elif (
            bike.current_state
            in {BikeState.ACTIVE_SECONDARY, BikeState.NOTICE_SECONDARY}
            and outstanding >= constants.SECONDARY_DEFAULT_AMOUNT
        ):
            claim_source = constants.CLAIM_SOURCE_SECONDARY_EARLY_TERMINATION
            event_type = EventType.SECONDARY_TERMINATED
            previous = bike.current_state
        else:
            continue

        claim_id = f"CL{len(project.guarantee_claims) + 1:08d}"
        claim = create_guarantee_claim(
            claim_id,
            bike.bike_id,
            contract.contract_id,
            contract.tenant_id,
            contract.guarantor_id,
            claim_source,
            outstanding,
            current_date,
            recovery_rate_pct,
        )
        project.guarantee_claims.append(claim)
        _ar_transfer(project, outstanding)
        project.guarantee_claim_receivable += outstanding
        contract.status = ContractStatus.TERMINATED
        bike.current_contract_id = None
        bike.current_tenant_id = None
        bike.termination_count += 1
        bike.current_state = BikeState.AVAILABLE_FOR_SECONDARY
        _event(
            project,
            current_date,
            bike,
            event_type,
            previous,
            bike.current_state,
            contract.contract_id,
            outstanding,
        )


def _m12(project: Project, current_date: date) -> None:
    for bike in list(project.bikes):
        contract = contract_of(project, bike)
        if contract is None or contract.status is not ContractStatus.ACTIVE:
            continue
        if contract.contract_type is not ContractType.PRIMARY:
            continue
        if current_date != contract.maturity_date:
            continue
        if bike.current_state not in {
            BikeState.ACTIVE_PRIMARY,
            BikeState.WAITING_PRIMARY,
            BikeState.NOTICE_PRIMARY,
            BikeState.GRACE_PRIMARY,
        }:
            continue

        outstanding = contract.total_due - contract.total_paid
        previous = bike.current_state
        if outstanding == 0:
            bike.current_state = BikeState.OWNED_TRANSFERRED
            contract.status = ContractStatus.SETTLED
            bike.pending_writeoff_today = True
            _event(
                project,
                current_date,
                bike,
                EventType.PRIMARY_CONTRACT_MATURED,
                previous,
                bike.current_state,
                contract.contract_id,
            )
            _event(
                project,
                current_date,
                bike,
                EventType.OWNERSHIP_TRANSFERRED,
                previous,
                bike.current_state,
                contract.contract_id,
            )
        else:
            bike.current_state = BikeState.POST_MATURITY_SETTLEMENT
            contract.status = ContractStatus.MATURED
            bike.settlement_legacy_debt_original = outstanding
            bike.settlement_legacy_debt_remaining = outstanding
            bike.settlement_start_date = None
            _new_receivable(project, bike, contract, outstanding)
            _event(
                project,
                current_date,
                bike,
                EventType.PRIMARY_CONTRACT_MATURED,
                previous,
                bike.current_state,
                contract.contract_id,
                outstanding,
            )
            _event(
                project,
                current_date,
                bike,
                EventType.SETTLEMENT_STARTED,
                previous,
                bike.current_state,
                contract.contract_id,
                outstanding,
            )


def _m13(
    project: Project,
    current_date: date,
    recovery_rate_pct: int = 100,
) -> None:
    for bike in list(project.bikes):
        if bike.current_state is not BikeState.POST_MATURITY_SETTLEMENT:
            continue
        contract = (
            project.contracts.get(bike.current_contract_id)
            if bike.current_contract_id
            else None
        )

        if bike.settlement_start_date is None:
            if (
                contract is None
                or contract.maturity_date is None
                or current_date <= contract.maturity_date
                or not dateutils.is_business_day(current_date)
            ):
                continue
            bike.settlement_start_date = current_date
            receivable = _receivable_of(project, bike)
            if receivable is not None:
                receivable.created_date = current_date

        if not dateutils.is_business_day(current_date):
            continue

        bike.settlement_business_days_elapsed += 1
        if bike.settlement_legacy_debt_remaining == 0:
            contract = (
                project.contracts.get(bike.current_contract_id)
                if bike.current_contract_id
                else None
            )
            if contract is not None:
                contract.status = ContractStatus.SETTLED
            previous = bike.current_state
            bike.current_state = BikeState.OWNED_TRANSFERRED
            bike.pending_writeoff_today = True
            _event(
                project,
                current_date,
                bike,
                EventType.SETTLEMENT_COMPLETED,
                previous,
                bike.current_state,
                bike.current_contract_id,
            )
            _event(
                project,
                current_date,
                bike,
                EventType.OWNERSHIP_TRANSFERRED,
                previous,
                bike.current_state,
                bike.current_contract_id,
            )
        elif (
            bike.settlement_business_days_elapsed
            > constants.SETTLEMENT_PERIOD_DAYS
        ):
            remaining = bike.settlement_legacy_debt_remaining
            contract = (
                project.contracts.get(bike.current_contract_id)
                if bike.current_contract_id
                else None
            )
            if contract is None:
                raise AssertionError(
                    "settlement bike lost its contract before failure"
                )
            claim_id = f"CL{len(project.guarantee_claims) + 1:08d}"
            claim = create_guarantee_claim(
                claim_id,
                bike.bike_id,
                contract.contract_id,
                contract.tenant_id,
                contract.guarantor_id,
                constants.CLAIM_SOURCE_POST_MATURITY_SETTLEMENT_FAILURE,
                remaining,
                current_date,
                recovery_rate_pct,
            )
            project.guarantee_claims.append(claim)
            _ar_transfer(project, remaining)
            project.guarantee_claim_receivable += remaining
            bike.settlement_legacy_debt_remaining = 0
            receivable = _receivable_of(project, bike)
            if receivable is not None:
                receivable.status = ReceivableStatus.TRANSFERRED_TO_GUARANTEE
                receivable.remaining_amount = 0
            contract.status = ContractStatus.TERMINATED
            bike.current_contract_id = None
            bike.current_tenant_id = None
            bike.current_state = BikeState.AVAILABLE_FOR_SECONDARY
            bike.active_settlement_receivable_id = None
            _event(
                project,
                current_date,
                bike,
                EventType.SETTLEMENT_FAILED,
                BikeState.POST_MATURITY_SETTLEMENT,
                bike.current_state,
                contract.contract_id,
                remaining,
            )


def _m14(
    project: Project,
    current_date: date,
) -> None:
    for claim in list(project.guarantee_claims):
        if claim.status is not ClaimStatus.PENDING:
            continue
        if current_date < claim.settlement_due_date:
            continue
        recovered = (claim.claim_amount * claim.recovery_rate_pct) // 100
        bad_debt = claim.claim_amount - recovered
        _cash_in(project, recovered)
        project.guarantee_claim_receivable -= claim.claim_amount
        project.bad_debt_expense += bad_debt
        record_eligible_inflow(project, recovered)
        claim.recovered_amount = recovered
        claim.bad_debt_amount = bad_debt
        claim.settlement_date = current_date
        claim.status = ClaimStatus.SETTLED
        bike = next(
            item for item in project.bikes if item.bike_id == claim.bike_id
        )
        _event(
            project,
            current_date,
            bike,
            EventType.GUARANTEE_RECOVERED
            if recovered > 0
            else EventType.GUARANTEE_WRITTEN_OFF,
            amount=claim.claim_amount,
        )


def _m15(
    project: Project,
    current_date: date,
    recovery_rate_pct: int,
) -> None:
    execute_dynamic_closure(project, current_date, recovery_rate_pct)


def _m16(project: Project, current_date: date) -> None:
    for bike in project.bikes:
        if not bike.pending_writeoff_today:
            continue
        old_accumulated = bike.accumulated_depreciation
        writeoff_amount = bike.gross_cost - old_accumulated
        _ad_remove(project, old_accumulated)
        project.asset_writeoff_expense += writeoff_amount
        _gross_writeoff(project, bike.gross_cost)
        bike.net_book_value = 0
        bike.accumulated_depreciation = bike.gross_cost
        bike.pending_writeoff_today = False
        _event(
            project,
            current_date,
            bike,
            EventType.OWNERSHIP_TRANSFERRED,
            bike.current_state,
            bike.current_state,
            amount=writeoff_amount,
        )


def _m17(
    project: Project,
    current_date: date,
    opening: dict[str, int],
) -> None:
    from accounting import refresh_profit

    refresh_profit(project)

    if project.simulation_stopped:
        project.final_net_project_equity = project.project_cash + sum(
            bike.net_book_value
            for bike in project.bikes
            if bike.current_state is BikeState.HELD_AS_ASSET
        )
        project.partner1_final_entitlement = (
            project.final_net_project_equity * 70
        ) // 100
        project.partner2_final_entitlement = (
            project.final_net_project_equity
            - project.partner1_final_entitlement
        )

    snapshot = assert_balance_sheet_balanced(project, current_date)
    project.daily_balance_checks.append(snapshot)
    record_daily_rollforwards(
        project,
        current_date,
        opening,
        project._day_metrics,
    )
    if project.simulation_stopped:
        if project.final_net_project_equity != snapshot["Total_Equity"]:
            raise AssertionError(
                "Final_Net_Project_Equity must equal Total_Equity after M17"
            )


def run_day(
    p: Project,
    current_date: date,
    collection_probability: float = 1.0,
    scenario_id: str = "C100_G100",
    trial_id: int = 1,
    recovery_rate_pct: int = 100,
    master_seed: int = constants.MASTER_SEED,
) -> None:
    if p.simulation_stopped:
        return

    p._recovery_rate_pct = recovery_rate_pct
    p._current_date = current_date
    opening = _begin_day(p)
    trace_enabled = getattr(p, "_execution_trace_enabled", False)
    trace = []

    stages = (
        ("M1", lambda: None),
        ("M2", lambda: _m2(p, current_date)),
        ("M3", lambda: _m3(p, current_date)),
        ("M4", lambda: None),
        ("M5", lambda: _m5(p, current_date)),
        ("M6", lambda: _m6(p, current_date, p._possession)),
        ("M7", lambda: _m7(p, p._possession, current_date)),
        (
            "M8",
            lambda: _m8(
                p,
                current_date,
                collection_probability,
                scenario_id,
                trial_id,
                master_seed,
            ),
        ),
        ("M9", lambda: _m9(p)),
        ("M10", lambda: None),
        ("M11", lambda: _m11(p, current_date, recovery_rate_pct)),
        ("M12", lambda: _m12(p, current_date)),
        ("M13", lambda: _m13(p, current_date, recovery_rate_pct)),
        ("M14", lambda: _m14(p, current_date)),
        ("M15", lambda: _m15(p, current_date, recovery_rate_pct)),
        ("M16", lambda: _m16(p, current_date)),
        ("M17", lambda: _m17(p, current_date, opening)),
    )

    p._possession = {}
    stages = (
        ("M1", lambda: None),
        ("M2", lambda: _m2(p, current_date)),
        ("M3", lambda: _m3(p, current_date)),
        ("M4", lambda: p._possession.update(_m4(p))),
        ("M5", lambda: _m5(p, current_date)),
        ("M6", lambda: _m6(p, current_date, p._possession)),
        ("M7", lambda: _m7(p, p._possession, current_date)),
        (
            "M8",
            lambda: _m8(
                p,
                current_date,
                collection_probability,
                scenario_id,
                trial_id,
                master_seed,
            ),
        ),
        ("M9", lambda: _m9(p)),
        ("M10", lambda: None),
        ("M11", lambda: _m11(p, current_date, recovery_rate_pct)),
        ("M12", lambda: _m12(p, current_date)),
        ("M13", lambda: _m13(p, current_date)),
        ("M14", lambda: _m14(p, current_date)),
        ("M15", lambda: _m15(p, current_date, recovery_rate_pct)),
        ("M16", lambda: _m16(p, current_date)),
        ("M17", lambda: _m17(p, current_date, opening)),
    )
    if trace_enabled:
        p.execution_trace.append(trace)

    for name, fn in stages:
        fn()
        if trace_enabled:
            trace.append(name)


def run_days(
    p: Project,
    start_date: date,
    end_date: date,
    **kwargs,
) -> Project:
    current = start_date
    while current <= end_date and not p.simulation_stopped:
        run_day(p, current, **kwargs)
        current += timedelta(days=1)
    return p


def run_deterministic_trial(
    recovery_rate_pct: int = 100,
    trial_id: int = 1,
    scenario_id: str = "C100_G100",
    master_seed: int = constants.MASTER_SEED,
    collection_probability: float = 1.0,
    on_day_end: Callable[[Project, date], None] | None = None,
    log_events: bool = True,
) -> Project:
    project = create_initial_project(recovery_rate_pct=recovery_rate_pct)
    project.log_events = log_events
    current = constants.PROJECT_START_DATE
    while not project.simulation_stopped:
        run_day(
            project,
            current,
            collection_probability=collection_probability,
            scenario_id=scenario_id,
            trial_id=trial_id,
            recovery_rate_pct=recovery_rate_pct,
            master_seed=master_seed,
        )
        if on_day_end is not None:
            on_day_end(project, current)
        current += timedelta(days=1)
    return project


__all__ = [
    "POSSESSION_STATES",
    "create_initial_project",
    "run_day",
    "run_days",
    "run_deterministic_trial",
]
