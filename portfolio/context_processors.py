"""
Context available to every template, including those rendered by views that
don't build it themselves (the shared nav and footer in base.html).
"""
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.templatetags.static import static

from .models import JourneyEntry


def site(request):
    return {
        'site_owner': settings.SITE_OWNER,
        'site_role': settings.SITE_ROLE,
        'site_description': settings.SITE_DESCRIPTION,
        # Drives both the Journey section and its nav entry, so an empty
        # section is never advertised in the navigation.
        'has_journey_entries': JourneyEntry.objects.exists(),
        'resume_url': _resume_url(),
    }


def _resume_url():
    """
    URL for the resume, or None when the file has not been added yet.

    Checked rather than assumed so a missing file hides the button instead of
    shipping a link that 404s.
    """
    path = settings.RESUME_STATIC_PATH
    if not path:
        return None
    if finders.find(path) or Path(settings.STATIC_ROOT or '', path).is_file():
        return static(path)
    return None
