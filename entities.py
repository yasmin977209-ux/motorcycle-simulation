"""Entities defined by Chapters 3 and 4 of the authoritative reference.

This module contains data structures only. No daily engine, accounting engine,
Monte Carlo loop, or random behavior is implemented here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


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
class Project:
    """Unified project entity.

    The two partner reinvestment balances are memo-only allocation figures,
    not separate cash accounts or balance-sheet assets.
    """

    project_cash: int = 0
    partner1_reinvestment_balance: int = 0
    partner2_reinvestment_balance: int = 0
    accounts_receivable: int = 0
    guarantee_claim_receivable: int = 0
    gross_bike_assets: int = 0
    accumulated_depreciation: int = 0
    capital: int = 0
    retained_earnings: int = 0
    opening_loss: int = 0
    revenue_primary: int = 0
    revenue_secondary: int = 0
    revenue_settlement: int = 0
    revenue_friday_fee: int = 0
    expense_depreciation: int = 0
    expense_oil_service: int = 0
    expense_prep: int = 0
    expense_marketing: int = 0
    bad_debt_expense: int = 0
    asset_writeoff_expense: int = 0
    bikes: list[Bike] = field(default_factory=list)
    contracts: list[Contract] = field(default_factory=list)
    tenants: list[Tenant] = field(default_factory=list)
    guarantors: list[Guarantor] = field(default_factory=list)
    guarantee_claims: list[GuaranteeClaim] = field(default_factory=list)
    receivables: list[ReceivableEntry] = field(default_factory=list)
    event_log: list[EventLogEntry] = field(default_factory=list)
    daily_balance_checks: list[dict] = field(default_factory=list)
    execution_trace: list[list[str]] = field(default_factory=list)
    simulation_stopped: bool = False
    final_close_date: Optional[date] = None
    final_net_project_equity: Optional[int] = None
    partner1_final_entitlement: Optional[int] = None
    partner2_final_entitlement: Optional[int] = None


@dataclass
class Bike:
    bike_id: str
    source: BikeSource
    purchase_date: date
    scheduled_ready_date: date
    funding_completion_date: Optional[date] = None
    actual_ready_date: Optional[date] = None
    prep_paid: bool = False
    customs_paid: bool = False
    delivery_date: Optional[date] = None
    gross_cost: int = 0
    accumulated_depreciation: int = 0
    net_book_value: int = 0
    current_state: str = "PREP"
    current_contract_id: Optional[str] = None
    current_tenant_id: Optional[str] = None
    settlement_start_date: Optional[date] = None
    settlement_legacy_debt_original: Optional[int] = None
    settlement_legacy_debt_remaining: Optional[int] = None
    settlement_business_days_elapsed: int = 0
    settlement_rent_due_total: int = 0
    settlement_rent_collected_total: int = 0
    termination_count: int = 0
    secondary_cycle_count: int = 0
    usage_days: int = 0
    lifecycle_cycle_number: int = 1
    active_settlement_receivable_id: Optional[str] = None
    pending_writeoff_today: bool = False
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
    maturity_date: Optional[date] = None
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
    end_date: Optional[date] = None


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
    settlement_date: Optional[date] = None
    recovered_amount: Optional[int] = None
    bad_debt_amount: Optional[int] = None
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
    created_date: Optional[date]
    settlement_date: Optional[date] = None


@dataclass
class EventLogEntry:
    event_id: str
    date: date
    bike_id: str
    event_type: EventType
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    contract_id: Optional[str] = None
    tenant_id: Optional[str] = None
    guarantor_id: Optional[str] = None
    receivable_id: Optional[str] = None
    claim_id: Optional[str] = None
    amount_if_applicable: Optional[int] = None
    balance_before: Optional[int] = None
    balance_after: Optional[int] = None
    trigger_reason: str = ""
    notes: str = ""


# Forward-reference containers are resolved after class creation.
Bike.__annotations__["lifecycle_history"] = list[EventLogEntry]
Bike.__annotations__["receivables_ledger"] = list[ReceivableEntry]
