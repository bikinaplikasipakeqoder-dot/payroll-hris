from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN

# Standard precision for Indonesian Rupiah (no decimal places for final amounts)
IDR_PRECISION = Decimal("1")
# For intermediate calculations that need cent precision
CALC_PRECISION = Decimal("0.01")
# For rate calculations (4 decimal places)
RATE_PRECISION = Decimal("0.0001")


def round_money(amount: Decimal) -> Decimal:
    """Round to nearest Rupiah (no decimals) using ROUND_HALF_UP."""
    return amount.quantize(IDR_PRECISION, rounding=ROUND_HALF_UP)


def round_calc(amount: Decimal) -> Decimal:
    """Round to 2 decimal places for intermediate calculations."""
    return amount.quantize(CALC_PRECISION, rounding=ROUND_HALF_UP)


def to_decimal(value) -> Decimal:
    """Safely convert any numeric value to Decimal. Never use float conversion."""
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def ensure_non_negative(amount: Decimal) -> Decimal:
    """Ensure amount is not negative. Return 0 if negative."""
    return max(amount, Decimal("0"))
