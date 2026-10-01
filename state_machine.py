"""Eleven-state bike lifecycle state machine from Chapter 4."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence

from constants import (
    EXPANSION_PURCHASE_CASH_THRESHOLD,
    PRIMARY_DEFAULT_AMOUNT,
    SECONDARY_DEFAULT_AMOUNT,
    WAITING_PRIMARY_UPPER,
    NOTICE_PRIMARY_UPPER,
    GRACE_PRIMARY_UPPER,
    PRIMARY_DAILY_RENT,
    SECONDARY_DAILY_RENT,
)
from entities import ContractType


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


STATE_COUNT = 11

FORBIDDEN_STATE_NAMES = frozenset(
    {
        "TERMINATION_PENDING",
        "MINI_PREP",
        "PENDING_RECALL",
        "GUARANTEE_PENDING",
    }
)


def derive_state_from_balance(
    outstanding_amount: int,
    daily_rate: int,
    contract_type: str | ContractType,
) -> Optional[str]:
    """Derive state from current outstanding balance only.

    A threshold breach returns None. It does not perform termination;
    M11 owns the actual termination transition.
    """

    if outstanding_amount < 0:
        raise ValueError("outstanding_amount must not be negative")
    if daily_rate <= 0:
        raise ValueError("daily_rate must be positive")

    contract = ContractType(contract_type)

    if contract is ContractType.PRIMARY:
        if outstanding_amount == 0:
            return BikeState.ACTIVE_PRIMARY.value
        if outstanding_amount < 21 * daily_rate:
            return BikeState.WAITING_PRIMARY.value
        if outstanding_amount < 28 * daily_rate:
            return BikeState.NOTICE_PRIMARY.value
        if outstanding_amount < 30 * daily_rate:
            return BikeState.GRACE_PRIMARY.value
        return None

    if outstanding_amount == 0:
        return BikeState.ACTIVE_SECONDARY.value
    if outstanding_amount < 10 * daily_rate:
        return BikeState.NOTICE_SECONDARY.value
    return None


@dataclass(frozen=True)
class TransitionRule:
    from_states: tuple[str, ...]
    to_states: tuple[str, ...]
    condition: str
    phase: str


# Table 4.3, represented as data rather than hidden control flow.
TRANSITION_TABLE: tuple[TransitionRule, ...] = (
    TransitionRule(
        ("PREP",),
        ("ACTIVE_PRIMARY",),
        "prep_paid and customs_paid and first working day on/after actual_ready_date",
        "M3",
    ),
    TransitionRule(
        ("ACTIVE_PRIMARY",),
        ("WAITING_PRIMARY",),
        "0 < outstanding < 21 * daily_rate",
        "M10",
    ),
    TransitionRule(
        ("WAITING_PRIMARY",),
        ("ACTIVE_PRIMARY",),
        "outstanding == 0",
        "M10",
    ),
    TransitionRule(
        ("WAITING_PRIMARY",),
        ("NOTICE_PRIMARY",),
        "21 * daily_rate <= outstanding < 28 * daily_rate",
        "M10",
    ),
    TransitionRule(
        ("NOTICE_PRIMARY",),
        ("WAITING_PRIMARY", "ACTIVE_PRIMARY"),
        "new outstanding after payment is in WAITING_PRIMARY or ACTIVE_PRIMARY band",
        "M10",
    ),
    TransitionRule(
        ("NOTICE_PRIMARY",),
        ("GRACE_PRIMARY",),
        "28 * daily_rate <= outstanding < 30 * daily_rate",
        "M10",
    ),
    TransitionRule(
        ("GRACE_PRIMARY",),
        ("ACTIVE_PRIMARY", "WAITING_PRIMARY", "NOTICE_PRIMARY", "GRACE_PRIMARY"),
        "new outstanding after payment is below 30 * daily_rate",
        "M10",
    ),
    TransitionRule(
        ("GRACE_PRIMARY",),
        ("AVAILABLE_FOR_SECONDARY",),
        "outstanding >= 30 * daily_rate",
        "M11",
    ),
    TransitionRule(
        ("ACTIVE_PRIMARY", "WAITING_PRIMARY", "NOTICE_PRIMARY", "GRACE_PRIMARY"),
        ("OWNED_TRANSFERRED",),
        "current_date == maturity_date and total_due == total_paid after maturity-day collection",
        "M12",
    ),
    TransitionRule(
        ("ACTIVE_PRIMARY", "WAITING_PRIMARY", "NOTICE_PRIMARY", "GRACE_PRIMARY"),
        ("POST_MATURITY_SETTLEMENT",),
        "current_date == maturity_date and total_due > total_paid after maturity-day collection",
        "M12",
    ),
    TransitionRule(
        ("POST_MATURITY_SETTLEMENT",),
        ("OWNED_TRANSFERRED",),
        "settlement_legacy_debt_remaining == 0",
        "M13",
    ),
    TransitionRule(
        ("POST_MATURITY_SETTLEMENT",),
        ("AVAILABLE_FOR_SECONDARY",),
        "30 working days have elapsed from settlement_start_date without full payment",
        "M13",
    ),
    TransitionRule(
        ("AVAILABLE_FOR_SECONDARY",),
        ("ACTIVE_SECONDARY",),
        "first eligible working day",
        "M3",
    ),
    TransitionRule(
        ("ACTIVE_SECONDARY",),
        ("NOTICE_SECONDARY",),
        "0 < outstanding < 10 * daily_rate",
        "M10",
    ),
    TransitionRule(
        ("NOTICE_SECONDARY",),
        ("ACTIVE_SECONDARY",),
        "outstanding == 0",
        "M10",
    ),
    TransitionRule(
        ("NOTICE_SECONDARY",),
        ("AVAILABLE_FOR_SECONDARY",),
        "outstanding >= 10 * daily_rate",
        "M11",
    ),
    TransitionRule(
        ("ACTIVE_SECONDARY", "NOTICE_SECONDARY"),
        ("HELD_AS_ASSET",),
        "dynamic closure conditions satisfied",
        "M15",
    ),
    TransitionRule(
        (
            "PREP",
            "ACTIVE_PRIMARY",
            "WAITING_PRIMARY",
            "NOTICE_PRIMARY",
            "GRACE_PRIMARY",
            "POST_MATURITY_SETTLEMENT",
            "AVAILABLE_FOR_SECONDARY",
            "ACTIVE_SECONDARY",
            "NOTICE_SECONDARY",
        ),
        ("HELD_AS_ASSET",),
        "dynamic closure conditions satisfied",
        "M15",
    ),
)


def validate_transition_table(table: Sequence[TransitionRule] = TRANSITION_TABLE) -> bool:
    """Validate the declared Chapter 4 transition table structurally."""
    declared = {state.value for state in BikeState}
    if len(declared) != STATE_COUNT:
        return False
    seen: set[tuple[str, str]] = set()
    for rule in table:
        if not rule.from_states or not rule.to_states or not rule.condition or not rule.phase:
            return False
        for from_state in rule.from_states:
            if from_state not in declared or from_state in FORBIDDEN_STATE_NAMES:
                return False
            for to_state in rule.to_states:
                if to_state not in declared or to_state in FORBIDDEN_STATE_NAMES:
                    return False
                edge = (from_state, to_state)
                if edge in seen:
                    return False
                seen.add(edge)
    return True
def is_declared_transition(from_state: str, to_state: str) -> bool:
    """Return whether Table 4.3 explicitly declares this state edge."""
    for rule in TRANSITION_TABLE:
        if to_state in rule.to_states and from_state in rule.from_states:
            return True
    return False


def run_reference_path(path: Sequence[str]) -> tuple[str, ...]:
    """Execute a reference lifecycle path through the declared transition table.

    This is a structural state-machine runner for Chapter 4 only. It does not
    invent event timing or implement M1-M17; it verifies each requested edge
    against the authoritative transition table.
    """
    if len(path) < 2:
        raise ValueError("A lifecycle path must contain at least two states")
    declared = {state.value for state in BikeState}
    if any(state not in declared for state in path):
        raise ValueError("Path contains an undeclared state")
    for current, target in zip(path, path[1:]):
        if not is_declared_transition(current, target):
            raise ValueError(f"Undeclared transition: {current} -> {target}")
    return tuple(path)

def _state_band(outstanding_amount: int, daily_rate: int, contract_type: str) -> str:
    state = derive_state_from_balance(outstanding_amount, daily_rate, contract_type)
    if state is not None:
        return state
    return BikeState.GRACE_PRIMARY.value if ContractType(contract_type) is ContractType.PRIMARY else BikeState.NOTICE_SECONDARY.value


def legal_next_state(
    current_state: str,
    outstanding_amount: int,
    daily_rate: int,
    contract_type: str | ContractType,
) -> Optional[str]:
    """Apply only balance-derived M10 classification.

    This intentionally leaves threshold breaches in the prior state; M11
    performs the termination transition separately.
    """

    state = BikeState(current_state)
    derived = derive_state_from_balance(outstanding_amount, daily_rate, contract_type)

    if state in {
        BikeState.ACTIVE_PRIMARY,
        BikeState.WAITING_PRIMARY,
        BikeState.NOTICE_PRIMARY,
        BikeState.GRACE_PRIMARY,
    }:
        return derived

    if state in {BikeState.ACTIVE_SECONDARY, BikeState.NOTICE_SECONDARY}:
        return derived

    return state.value


# Reference-linked numeric integrity checks: thresholds remain derived from
# constants and daily rates rather than being magic business values.
assert WAITING_PRIMARY_UPPER == 21 * PRIMARY_DAILY_RENT
assert NOTICE_PRIMARY_UPPER == 28 * PRIMARY_DAILY_RENT
assert GRACE_PRIMARY_UPPER == PRIMARY_DEFAULT_AMOUNT
assert PRIMARY_DEFAULT_AMOUNT == 30 * PRIMARY_DAILY_RENT
assert SECONDARY_DEFAULT_AMOUNT == 10 * SECONDARY_DAILY_RENT
assert EXPANSION_PURCHASE_CASH_THRESHOLD == 350_000
assert len(BikeState) == STATE_COUNT
assert len(TRANSITION_TABLE) == 18
assert not (set(BikeState.__members__) & FORBIDDEN_STATE_NAMES)
