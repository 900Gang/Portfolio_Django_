"""
Admin sign-in with a lockout: after five failed attempts from one visitor in
fifteen minutes, further attempts from that visitor are refused without
checking the password until the window ends. A successful sign-in clears the
count.

The lockout is per visitor address, never per username, so nobody can lock
the owner out of their own admin by typing their username from elsewhere.
"""
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError

from . import throttle

MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60


class ThrottledAdminAuthenticationForm(AdminAuthenticationForm):
    error_messages = {
        **AdminAuthenticationForm.error_messages,
        "throttled": "Too many failed sign-in attempts. Try again in 15 minutes.",
    }

    def _key(self):
        ip = throttle.client_ip(self.request) if self.request is not None else "unknown"
        return f"admin-login:failures:{ip}"

    def clean(self):
        key = self._key()
        if throttle.count(key) >= MAX_FAILURES:
            raise ValidationError(self.error_messages["throttled"], code="throttled")
        try:
            cleaned_data = super().clean()
        except ValidationError:
            throttle.hit(key, WINDOW_SECONDS)
            raise
        throttle.reset(key)
        return cleaned_data
