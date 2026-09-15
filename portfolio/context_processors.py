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
    """Identity, contact details and shared flags for every page."""
    return {
        'site_owner': settings.SITE_OWNER,
        'site_role': settings.SITE_ROLE,
        'site_tagline': settings.SITE_TAGLINE,
        'site_description': settings.SITE_DESCRIPTION,
        'site_email': settings.SITE_EMAIL,
        'site_phone': settings.SITE_PHONE,
        'site_github_url': settings.SITE_GITHUB_URL,
        'site_linkedin_url': settings.SITE_LINKEDIN_URL,
        'site_location': settings.SITE_LOCATION,
        'site_current': settings.SITE_CURRENT,
        'site_focus': settings.SITE_FOCUS,
        'site_availability': settings.SITE_AVAILABILITY,
        # Drives both the Journey section and its nav entry, so an empty
        # section is never advertised in the navigation.
        'has_journey_entries': JourneyEntry.objects.exists(),
        'resume_url': _static_if_present(settings.RESUME_STATIC_PATH),
        'resume_download_name': settings.RESUME_DOWNLOAD_NAME,
        'og_image_url': _absolute(request, _static_if_present(settings.OG_IMAGE_STATIC_PATH)),
    }


def _static_if_present(path):
    """
    URL for a static file, or None when it has not been added yet.

    Checked rather than assumed so a missing file hides its button (or omits
    its meta tag) instead of shipping a link that 404s.
    """
    if not path:
        return None
    if finders.find(path) or Path(settings.STATIC_ROOT or '', path).is_file():
        return static(path)
    return None


def _absolute(request, url):
    """
    Promote a site-relative URL to an absolute one.

    Link-preview scrapers do not resolve relative og:image URLs, so a
    relative path there is the same as having no image at all. SITE_URL wins
    when set — behind a proxy the request's own host may be the internal one.
    """
    if not url or url.startswith(('http://', 'https://')):
        return url
    base = settings.SITE_URL.rstrip('/')
    if base:
        return f'{base}{url}'
    if request is not None:
        return request.build_absolute_uri(url)
    return url
