"""Template filters for the portfolio templates."""
from django import template

register = template.Library()


@register.filter
def handle(name):
    """'Anand N' -> 'anand_n': the label on the hero's detection box."""
    return "_".join(str(name).lower().split())
