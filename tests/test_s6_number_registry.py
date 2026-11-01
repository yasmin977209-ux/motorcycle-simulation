import pytest
from scripts.s6_number_registry import display_fraction, source_number

def test_display_fraction():
    assert display_fraction(5, 2) == '2.50'
    assert display_fraction(1, 8) == '0.12'

def test_exact_source_decimal():
    from decimal import Decimal
    assert source_number(Decimal('0.30')) == (3, 10, '0.30', 'SOURCE_DECIMAL_EXACT')
    with pytest.raises(ValueError):
        source_number(0.3)
