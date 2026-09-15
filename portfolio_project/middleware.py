"""Project middleware."""
import os

from django.conf import settings as django_settings
from whitenoise.middleware import WhiteNoiseMiddleware


class WhiteNoiseWithMediaMiddleware(WhiteNoiseMiddleware):
    """
    WhiteNoise, extended to also serve MEDIA_ROOT under MEDIA_URL.

    WhiteNoise serves STATIC_ROOT only, and `portfolio_project/urls.py` wires
    media up under DEBUG alone. Together that meant project screenshots — which
    are ImageField uploads living in MEDIA_ROOT, not static files — 404'd on a
    deployed site, so every project card fell back to the placeholder graphic
    while looking correct in development.

    Suitable for the single-instance deployment this project targets. Object
    storage is the answer for anything with more than one web process or an
    ephemeral filesystem; see the deployment note in the README.
    """

    def __init__(self, get_response=None, settings=django_settings):
        super().__init__(get_response, settings)

        media_root = str(settings.MEDIA_ROOT or '')
        if media_root and os.path.isdir(media_root):
            # add_files() wants the prefix the files are served under. Django
            # allows MEDIA_URL without a leading slash, which WhiteNoise would
            # otherwise treat as a relative path.
            prefix = settings.MEDIA_URL or '/media/'
            if not prefix.startswith('/'):
                prefix = '/' + prefix
            self.add_files(media_root, prefix=prefix)
