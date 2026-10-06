"""Template filters for the portfolio templates."""
from django import template

from ..models import SkillStatus

register = template.Library()

TICKER_LIMIT = 16


@register.filter
def handle(name):
    """'Anand N' -> 'anand_n': the label on the hero's detection box."""
    return "_".join(str(name).lower().split())


@register.filter
def ticker_skills(skills, limit=TICKER_LIMIT):
    """
    The technologies for the ticker under the hero: skills already used in
    projects first, then the rest, capped at `limit`.

    Works on the list the view already fetched, so it adds no query.
    """
    skills = list(skills)
    used = [skill for skill in skills if skill.status == SkillStatus.USED_IN_PROJECTS]
    rest = [skill for skill in skills if skill.status != SkillStatus.USED_IN_PROJECTS]
    return (used + rest)[: int(limit)]
