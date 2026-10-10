"""
Tests for the email alert sent when a visitor uses the contact form.

No test talks to Resend: the network call goes through
notifications._post(), which these tests replace, or through
urllib.request.urlopen(), which the request-shape test replaces.
"""
import io
import json
import urllib.error
from unittest import mock

from django.conf import settings
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse

from . import notifications
from .models import ContactMessage

ENABLED = override_settings(RESEND_API_KEY="re_test_key")
DISABLED = override_settings(RESEND_API_KEY="")

FORM = {
    "name": "Priya Recruiter",
    "email": "priya@example.com",
    "subject": "AI internship",
    "message": "We'd like to talk about a role.",
}


def submit(client):
    return client.post(reverse("portfolio:home"), FORM)


class ContactAlertSettingsTest(TestCase):
    def test_alerts_go_to_the_site_email_from_resends_test_sender_by_default(self):
        self.assertEqual(settings.CONTACT_ALERT_TO, settings.SITE_EMAIL)
        self.assertEqual(settings.CONTACT_ALERT_FROM, "Portfolio <onboarding@resend.dev>")


class BuildEmailTest(TestCase):
    def setUp(self):
        self.message = ContactMessage.objects.create(**FORM)

    @override_settings(SITE_URL="https://nanomachine.xyz/")
    def test_email_contents(self):
        email = notifications.build_email(self.message)
        self.assertEqual(email["from"], settings.CONTACT_ALERT_FROM)
        self.assertEqual(email["to"], [settings.CONTACT_ALERT_TO])
        # Pressing Reply answers the visitor, not the alert sender.
        self.assertEqual(email["reply_to"], "priya@example.com")
        self.assertEqual(email["subject"], "New portfolio message from Priya Recruiter")
        for part in ("priya@example.com", "AI internship", "We'd like to talk about a role."):
            self.assertIn(part, email["text"])
        admin_path = reverse("admin:portfolio_contactmessage_change", args=[self.message.pk])
        self.assertIn(f"https://nanomachine.xyz{admin_path}", email["text"])

    @override_settings(SITE_URL="")
    def test_admin_link_is_left_out_without_a_site_url(self):
        self.assertNotIn("/admin/", notifications.build_email(self.message)["text"])

    def test_line_breaks_in_the_name_stay_out_of_the_subject(self):
        self.message.name = "Priya\r\nRecruiter"
        self.assertEqual(
            notifications.build_email(self.message)["subject"],
            "New portfolio message from Priya Recruiter",
        )


class SendRequestTest(TestCase):
    @ENABLED
    def test_request_sent_to_resend(self):
        response = mock.MagicMock(status=200)
        response.__enter__.return_value = response
        with mock.patch("urllib.request.urlopen", return_value=response) as urlopen:
            notifications._post({"subject": "Hello"})

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.resend.com/emails")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Authorization"), "Bearer re_test_key")
        self.assertEqual(request.get_header("Content-type"), "application/json")
        # Python's default urllib User-Agent is refused by some API gateways.
        self.assertNotIn("Python-urllib", request.get_header("User-agent"))
        self.assertEqual(json.loads(request.data), {"subject": "Hello"})
        self.assertEqual(urlopen.call_args.kwargs["timeout"], notifications.TIMEOUT_SECONDS)


class ContactFormAlertTest(TestCase):
    @ENABLED
    def test_a_new_message_sends_one_alert(self):
        with mock.patch("portfolio.notifications._post") as post:
            response = submit(self.client)
        self.assertRedirects(response, reverse("portfolio:home"), fetch_redirect_response=False)
        post.assert_called_once()
        self.assertEqual(post.call_args.args[0]["reply_to"], "priya@example.com")

    @DISABLED
    def test_no_alert_without_a_key(self):
        with mock.patch("portfolio.notifications._post") as post:
            submit(self.client)
        post.assert_not_called()
        self.assertEqual(ContactMessage.objects.count(), 1)

    @ENABLED
    def test_an_invalid_form_sends_nothing(self):
        with mock.patch("portfolio.notifications._post") as post:
            self.client.post(reverse("portfolio:home"), {**FORM, "email": "not-an-email"})
        post.assert_not_called()

    @ENABLED
    def test_a_failed_alert_never_breaks_the_form(self):
        failures = {
            "rejected by Resend": urllib.error.HTTPError(
                "https://api.resend.com/emails", 403, "Forbidden", {}, io.BytesIO(b'{"message": "bad key"}')
            ),
            "network down": urllib.error.URLError("Name or service not known"),
            "timeout": TimeoutError("timed out"),
        }
        for name, error in failures.items():
            with self.subTest(failure=name):
                ContactMessage.objects.all().delete()
                with mock.patch("portfolio.notifications._post", side_effect=error):
                    with self.assertLogs("portfolio.notifications", level="ERROR"):
                        response = submit(self.client)
                self.assertRedirects(response, reverse("portfolio:home"), fetch_redirect_response=False)
                self.assertEqual(ContactMessage.objects.count(), 1)
                self.assertIn(
                    "Your message has been sent successfully.",
                    [str(m) for m in get_messages(response.wsgi_request)],
                )
