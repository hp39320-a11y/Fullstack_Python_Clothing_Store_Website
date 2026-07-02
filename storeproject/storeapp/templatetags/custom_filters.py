from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='currency')
def currency(value):
    """
    Format a value as a currency (₹ followed by amount with two decimal places).
    """
    try:
        val = Decimal(str(value))
        return f"₹{val:,.2f}"
    except Exception:
        return value

@register.filter(name='subtract')
def subtract(value, arg):
    """
    Subtract arg from value (useful for calculations in Django templates).
    """
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except Exception:
        return value
