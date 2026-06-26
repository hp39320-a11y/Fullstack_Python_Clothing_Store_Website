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
    except (ValueError, TypeError):
        return value
