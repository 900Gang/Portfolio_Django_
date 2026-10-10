"""
Email alerts for new contact messages, sent through Resend's HTTP API.

Render's free plan blocks outbound SMTP (ports 25, 465 and 587), so Django's
SMTP email backend cannot be used there; Resend is called over HTTPS instead.

The alert is a convenience: the message is already saved when it is sent, so
a failure is logged and never shown to the visitor.
"""
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"
TIMEOUT_SECONDS = 5


def _one_line(text):
    return " ".join(text.split())


def build_email(message):
    """The Resend payload for one ContactMessage."""
    lines = [
        f"From: {_one_line(message.name)} <{message.email}>",
        f"Subject: {message.subject}",
        "",
        message.message,
    ]
    base = settings.SITE_URL.rstrip("/")
    if base:
        admin_path = reverse("admin:portfolio_contactmessage_change", args=[message.pk])
        lines += ["", f"Open in the admin: {base}{admin_path}"]
    return {
        "from": settings.CONTACT_ALERT_FROM,
        "to": [settings.CONTACT_ALERT_TO],
        # Pressing Reply in the inbox answers the visitor.
        "reply_to": message.email,
        "subject": f"New portfolio message from {_one_line(message.name)}",
        "text": "\n".join(lines),
    }


def _post(payload):
    """The one place that talks to Resend; tests replace it."""
    request = urllib.request.Request(
        RESEND_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
            # Python's default urllib User-Agent is refused by some API gateways.
            "User-Agent": "nanomachine-portfolio/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.status


def notify_new_message(message):
    """
    Email the owner about a new contact message. Does nothing while
    RESEND_API_KEY is empty. Never raises; returns True when the alert was sent.
    """
    if not settings.RESEND_API_KEY:
        return False
    try:
        _post(build_email(message))
    except urllib.error.HTTPError as error:
        logger.exception("Contact alert rejected by Resend: %s %s", error.code, error.read()[:300])
    except OSError as error:  # URLError, timeouts and other network failures
        logger.exception("Contact alert could not be sent: %s", error)
    else:
        return True
    return False
