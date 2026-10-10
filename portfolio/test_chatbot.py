"""
Tests for the portfolio assistant
(docs/superpowers/specs/2026-10-10-portfolio-chatbot-design.md).

No test talks to Google: every call goes through chatbot.get_client(),
which these tests replace with a fake, so no API key is needed.

Each task of the paste guide adds one section at the end of this file, with
the imports that section needs at its top.
"""
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

# The assistant switches on only when a key is configured. Tests set both
# values explicitly, so a key in a developer's local .env cannot change the
# outcome.
ENABLED = override_settings(GEMINI_API_KEY="test-key", CHATBOT_ENABLED=True)
DISABLED = override_settings(GEMINI_API_KEY="", CHATBOT_ENABLED=False)


# --- Task 1: settings and template flags -------------------------------------


class ChatbotSettingsTest(TestCase):
    def test_flash_lite_is_the_default_model(self):
        self.assertEqual(settings.CHATBOT_MODEL, "gemini-3.5-flash-lite")

    def test_template_flag_follows_the_setting(self):
        with ENABLED:
            self.assertTrue(self.client.get(reverse("portfolio:home")).context["chatbot_enabled"])
        with DISABLED:
            self.assertFalse(self.client.get(reverse("portfolio:home")).context["chatbot_enabled"])

    def test_first_name_is_available_to_templates(self):
        context = self.client.get(reverse("portfolio:home")).context
        self.assertEqual(context["site_first_name"], settings.SITE_OWNER.split()[0])


# --- Task 2: the chat log -------------------------------------------------------

from datetime import timedelta  # noqa: E402

from django.contrib.auth.models import User  # noqa: E402
from django.utils import timezone  # noqa: E402

from .models import ChatLog  # noqa: E402


class ChatLogTest(TestCase):
    def test_str_shows_the_date_and_the_start_of_the_question(self):
        log = ChatLog.objects.create(
            conversation_id="c", question="What are his main skills? " * 5, answer="a", model="m"
        )
        self.assertTrue(str(log).startswith(log.created_at.strftime("%Y-%m-%d")))
        self.assertIn("What are his main skills?", str(log))
        self.assertLess(len(str(log)), 80)

    def test_saving_deletes_logs_older_than_ninety_days(self):
        old = ChatLog.objects.create(conversation_id="c", question="old", answer="a", model="m")
        ChatLog.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=91))
        recent = ChatLog.objects.create(conversation_id="c", question="recent", answer="a", model="m")
        ChatLog.objects.filter(pk=recent.pk).update(created_at=timezone.now() - timedelta(days=89))

        ChatLog.objects.create(conversation_id="c", question="new", answer="a", model="m")

        self.assertEqual(
            sorted(ChatLog.objects.values_list("question", flat=True)), ["new", "recent"]
        )


class ChatLogAdminTest(TestCase):
    def setUp(self):
        admin_user = User.objects.create_superuser("admin", "admin@example.com", "pw")
        self.client.force_login(admin_user)
        self.log = ChatLog.objects.create(
            conversation_id="c", question="Where is he based?", answer="Trivandrum.", model="m"
        )

    def test_list_and_detail_pages_load(self):
        self.assertEqual(self.client.get(reverse("admin:portfolio_chatlog_changelist")).status_code, 200)
        detail = self.client.get(reverse("admin:portfolio_chatlog_change", args=[self.log.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Trivandrum.")

    def test_logs_cannot_be_added_or_edited(self):
        self.assertEqual(self.client.get(reverse("admin:portfolio_chatlog_add")).status_code, 403)
        response = self.client.post(
            reverse("admin:portfolio_chatlog_change", args=[self.log.pk]),
            {"question": "changed", "answer": "changed"},
        )
        self.assertEqual(response.status_code, 403)
        self.log.refresh_from_db()
        self.assertEqual(self.log.question, "Where is he based?")
