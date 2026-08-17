from decimal import Decimal

def format_currency_inr(value):
    """
    Formats a numeric value as a standard Indian Rupee (INR) amount string.
    Example: 1500000 -> "INR 1,500,000.00"
    """
    if value is None:
        return "INR 0.00"
    val = Decimal(str(value))
    return f"INR {val:,.2f}"
