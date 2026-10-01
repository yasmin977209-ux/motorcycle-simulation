"""Chapter 3 entities — rebuilt from the authoritative reference.

This module contains the domain data model only. It does not import dateutils
or rng and it does not execute daily business logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum

from constants import (
    INITIAL_FLEET_SIZE,
    OPENING_BIKE_ASSETS,
    OPENING_CASH,
    OPENING_MARKETING_EXPENSE,
    OPENING_PARTNER1_REINVESTMENT_BALANCE,
    OPENING_PARTNER2_REINVESTMENT_BALANCE,
    OPENING_PREP_EXPENSE,
    OPENING_RETAINED_LOSS,
    TOTAL_CAPITAL,
)


class BikeSource(str, Enum):
    INITIAL = "INITIAL"
    EXPANSION = "EXPANSION"


class ContractType(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"


class ContractStatus(str, Enum):
    ACTIVE = "ACTIVE"
    MATURED = "MATURED"
    TERMINATED = "TERMINATED"
    SETTLED = "SETTLED"


class TenantType(str, Enum):
    ORIGINAL = "ORIGINAL"
    SECONDARY = "SECONDARY"


class ClaimSource(str, Enum):
    PRIMARY_EARLY_TERMINATION = "PRIMARY_EARLY_TERMINATION"
    SECONDARY_EARLY_TERMINATION = "SECONDARY_EARLY_TERMINATION"
    POST_MATURITY_SETTLEMENT_FAILURE = "POST_MATURITY_SETTLEMENT_FAILURE"
    ADMINISTRATIVE_CLOSURE = "ADMINISTRATIVE_CLOSURE"
    FINAL_CLOSURE = "FINAL_CLOSURE"


class ClaimStatus(str, Enum):
    PENDING = "PENDING"
    SETTLED = "SETTLED"


class ReceivableSource(str, Enum):
    SETTLEMENT_LEGACY_DEBT = "SETTLEMENT_LEGACY_DEBT"


class ReceivableStatus(str, Enum):
    OUTSTANDING = "OUTSTANDING"
    SETTLED = "SETTLED"
    TRANSFERRED_TO_GUARANTEE = "TRANSFERRED_TO_GUARANTEE"


class BikeState(str, Enum):
    PREP = "PREP"
    ACTIVE_PRIMARY = "ACTIVE_PRIMARY"
    WAITING_PRIMARY = "WAITING_PRIMARY"
    NOTICE_PRIMARY = "NOTICE_PRIMARY"
    GRACE_PRIMARY = "GRACE_PRIMARY"
    POST_MATURITY_SETTLEMENT = "POST_MATURITY_SETTLEMENT"
    AVAILABLE_FOR_SECONDARY = "AVAILABLE_FOR_SECONDARY"
    ACTIVE_SECONDARY = "ACTIVE_SECONDARY"
    NOTICE_SECONDARY = "NOTICE_SECONDARY"
    OWNED_TRANSFERRED = "OWNED_TRANSFERRED"
    HELD_AS_ASSET = "HELD_AS_ASSET"


class EventType(str, Enum):
    BIKE_PURCHASED = "BIKE_PURCHASED"
    PREP_STARTED = "PREP_STARTED"
    PREP_COMPLETED = "PREP_COMPLETED"
    PRIMARY_CONTRACT_STARTED = "PRIMARY_CONTRACT_STARTED"
    PRIMARY_CONTRACT_MATURED = "PRIMARY_CONTRACT_MATURED"
    WAITING_STARTED = "WAITING_STARTED"
    NOTICE_STARTED = "NOTICE_STARTED"
    GRACE_STARTED = "GRACE_STARTED"
    PRIMARY_TERMINATED = "PRIMARY_TERMINATED"
    SETTLEMENT_STARTED = "SETTLEMENT_STARTED"
    SETTLEMENT_COMPLETED = "SETTLEMENT_COMPLETED"
    SETTLEMENT_FAILED = "SETTLEMENT_FAILED"
    SECONDARY_CONTRACT_STARTED = "SECONDARY_CONTRACT_STARTED"
    SECONDARY_TERMINATED = "SECONDARY_TERMINATED"
    ADMINISTRATIVE_CLOSURE = "ADMINISTRATIVE_CLOSURE"
    GUARANTEE_CLAIM_CREATED = "GUARANTEE_CLAIM_CREATED"
    GUARANTEE_RECOVERED = "GUARANTEE_RECOVERED"
    GUARANTEE_WRITTEN_OFF = "GUARANTEE_WRITTEN_OFF"
    OWNERSHIP_TRANSFERRED = "OWNERSHIP_TRANSFERRED"
    FINAL_ASSET_HELD = "FINAL_ASSET_HELD"
    EXPANSION_PURCHASE = "EXPANSION_PURCHASE"
    FRIDAY_FEE_COLLECTED = "FRIDAY_FEE_COLLECTED"
    OIL_SERVICE_PERFORMED = "OIL_SERVICE_PERFORMED"
    DEPRECIATION_RECORDED = "DEPRECIATION_RECORDED"


@dataclass
class Bike:
    bike_id: str
    source: BikeSource
    purchase_date: date
    scheduled_ready_date: date
    funding_completion_date: date | None = None
    actual_ready_date: date | None = None
    prep_paid: bool = False
    customs_paid: bool = False
    delivery_date: date | None = None
    gross_cost: int = 0
    accumulated_depreciation: int = 0
    net_book_value: int = 0
    current_state: BikeState = BikeState.PREP
    current_contract_id: str | None = None
    current_tenant_id: str | None = None
    active_settlement_receivable_id: str | None = None
    pending_writeoff_today: bool = False
    settlement_start_date: date | None = None
    settlement_legacy_debt_original: int | None = None
    settlement_legacy_debt_remaining: int | None = None
    settlement_business_days_elapsed: int = 0
    settlement_rent_due_total: int = 0
    settlement_rent_collected_total: int = 0
    termination_count: int = 0
    secondary_cycle_count: int = 0
    usage_days: int = 0
    lifecycle_cycle_number: int = 1
    lifecycle_history: list[EventLogEntry] = field(default_factory=list)
    receivables_ledger: list[ReceivableEntry] = field(default_factory=list)


@dataclass
class Contract:
    contract_id: str
    bike_id: str
    tenant_id: str
    guarantor_id: str
    contract_type: ContractType
    daily_rate: int
    start_date: date
    maturity_date: date | None = None
    status: ContractStatus = ContractStatus.ACTIVE
    total_due: int = 0
    total_paid: int = 0
    friday_counter: int = 0


@dataclass
class Tenant:
    tenant_id: str
    tenant_type: TenantType
    contract_id: str
    guarantor_id: str
    start_date: date
    end_date: date | None = None


@dataclass
class Guarantor:
    guarantor_id: str
    related_contract_id: str
    related_tenant_id: str


@dataclass
class GuaranteeClaim:
    claim_id: str
    bike_id: str
    contract_id: str
    tenant_id: str
    guarantor_id: str
    claim_source: ClaimSource
    claim_amount: int
    created_date: date
    waiting_period_days: int
    settlement_due_date: date
    recovery_rate_pct: int
    settlement_date: date | None = None
    recovered_amount: int | None = None
    bad_debt_amount: int | None = None
    status: ClaimStatus = ClaimStatus.PENDING


@dataclass
class ReceivableEntry:
    receivable_id: str
    bike_id: str
    contract_id: str
    tenant_id: str
    source: ReceivableSource
    original_amount: int
    collected_amount: int
    remaining_amount: int
    status: ReceivableStatus
    created_date: date
    settlement_date: date | None = None


@dataclass
class EventLogEntry:
    event_id: str
    date: date
    bike_id: str
    event_type: EventType
    previous_state: BikeState | None = None
    new_state: BikeState | None = None
    contract_id: str | None = None
    tenant_id: str | None = None
    guarantor_id: str | None = None
    receivable_id: str | None = None
    claim_id: str | None = None
    amount_if_applicable: int | None = None
    balance_before: int | None = None
    balance_after: int | None = None
    trigger_reason: str = ""
    notes: str = ""


@dataclass
class Project:
    project_cash: int = OPENING_CASH
    partner1_reinvestment_balance: int = OPENING_PARTNER1_REINVESTMENT_BALANCE
    partner2_reinvestment_balance: int = OPENING_PARTNER2_REINVESTMENT_BALANCE
    accounts_receivable: int = 0
    guarantee_claim_receivable: int = 0
    gross_bike_assets: int = OPENING_BIKE_ASSETS
    accumulated_depreciation: int = 0
    capital: int = TOTAL_CAPITAL
    retained_earnings: int = OPENING_RETAINED_LOSS
    opening_loss: int = OPENING_RETAINED_LOSS
    revenue_primary: int = 0
    revenue_secondary: int = 0
    revenue_settlement: int = 0
    revenue_friday_fee: int = 0
    expense_depreciation: int = 0
    expense_oil_service: int = 0
    expense_prep: int = 0
    expense_marketing: int = OPENING_MARKETING_EXPENSE
    bad_debt_expense: int = 0
    asset_writeoff_expense: int = 0
    operating_revenue: int = 0
    operating_expenses: int = 0
    operating_net_profit: int = 0
    cumulative_project_profit: int = 0
    final_close_date: date | None = None
    final_net_project_equity: int | None = None
    partner1_final_entitlement: int | None = None
    partner2_final_entitlement: int | None = None
    simulation_stopped: bool = False
    bikes: list[Bike] = field(default_factory=list)
    # O(1) contract lookup by the authoritative contract_id key.
    contracts: dict[str, Contract] = field(default_factory=dict)
    tenants: list[Tenant] = field(default_factory=list)
    guarantors: list[Guarantor] = field(default_factory=list)
    guarantee_claims: list[GuaranteeClaim] = field(default_factory=list)
    receivables: list[ReceivableEntry] = field(default_factory=list)
    event_log: list[EventLogEntry] = field(default_factory=list)
    cash_rollforward: list[dict] = field(default_factory=list)
    ar_rollforward: list[dict] = field(default_factory=list)
    asset_rollforward: list[dict] = field(default_factory=list)
    equity_rollforward: list[dict] = field(default_factory=list)
    daily_snapshots: list[dict] = field(default_factory=list)
    daily_balance_checks: list[dict] = field(default_factory=list)
    execution_trace: list[list[str]] = field(default_factory=list)
    error_log: list[dict] = field(default_factory=list)

    @classmethod
    def opening(cls) -> "Project":
        return cls(
            project_cash=OPENING_CASH,
            partner1_reinvestment_balance=OPENING_PARTNER1_REINVESTMENT_BALANCE,
            partner2_reinvestment_balance=OPENING_PARTNER2_REINVESTMENT_BALANCE,
            gross_bike_assets=OPENING_BIKE_ASSETS,
            capital=TOTAL_CAPITAL,
            retained_earnings=OPENING_RETAINED_LOSS,
            opening_loss=OPENING_RETAINED_LOSS,
            expense_marketing=OPENING_MARKETING_EXPENSE,
        )


def opening_fleet_size() -> int:
    return INITIAL_FLEET_SIZE


__all__ = [
    "BikeSource",
    "ContractType",
    "ContractStatus",
    "TenantType",
    "ClaimSource",
    "ClaimStatus",
    "ReceivableSource",
    "ReceivableStatus",
    "BikeState",
    "EventType",
    "Bike",
    "Contract",
    "Tenant",
    "Guarantor",
    "GuaranteeClaim",
    "ReceivableEntry",
    "EventLogEntry",
    "Project",
    "opening_fleet_size",
]
