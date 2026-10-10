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
