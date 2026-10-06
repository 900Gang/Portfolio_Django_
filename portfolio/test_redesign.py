"""
Tests for the editorial noir redesign
(docs/superpowers/specs/2026-10-06-portfolio-redesign-design.md).

They pin what the new design relies on that the older suites do not cover:
navigation off the home page, the hero, the ticker, the new sections,
motion safety and the image tooling.
"""
import io
import re
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Certification, JourneyEntry, Project, Skill, SkillCategory, SkillStatus

BASE_DIR = Path(settings.BASE_DIR)


def home_html(client):
    return client.get(reverse("portfolio:home")).content.decode()


class ChromeTest(TestCase):
    """Navigation, header and footer shared by every page."""

    def test_nav_links_on_home_stay_on_the_page(self):
        hrefs = re.findall(r'href="([^"]*)" class="nav-link"', home_html(self.client))
        self.assertTrue(hrefs, "no nav links found")
        for href in hrefs:
            with self.subTest(href=href):
                self.assertRegex(href, r"^#[a-z-]+$")

    def test_nav_links_on_other_pages_lead_back_to_home_sections(self):
        project = Project.objects.create(title="P", short_description="d")
        html = self.client.get(project.get_absolute_url()).content.decode()
        hrefs = re.findall(r'href="([^"]*)" class="nav-link"', html)
        self.assertTrue(hrefs, "no nav links found")
        for href in hrefs:
            with self.subTest(href=href):
                self.assertRegex(href, r"^/#[a-z-]+$")

    def test_nav_links_on_the_404_page_lead_back_home_too(self):
        html = self.client.get("/projects/no-such-project/").content.decode()
        hrefs = re.findall(r'href="([^"]*)" class="nav-link"', html)
        self.assertTrue(hrefs, "no nav links found")
        for href in hrefs:
            with self.subTest(href=href):
                self.assertRegex(href, r"^/#[a-z-]+$")

    def test_header_is_transparent_only_over_a_stage_hero(self):
        self.assertIn('<body class="has-stage-hero">', home_html(self.client))
        missing = self.client.get("/projects/no-such-project/").content.decode()
        self.assertNotIn("has-stage-hero", missing)

    def test_header_hides_on_scroll_down_and_returns_on_focus(self):
        js = (BASE_DIR / "static" / "js" / "navigation.js").read_text()
        css = (BASE_DIR / "static" / "css" / "components.css").read_text()
        self.assertIn("'is-hidden'", js)
        self.assertIn(".site-header.is-hidden", css)
        self.assertIn(".site-header:focus-within", css)

    def test_availability_shows_in_the_nav_only_when_set(self):
        self.assertIn('class="nav-status"', home_html(self.client))
        with override_settings(SITE_AVAILABILITY=""):
            self.assertNotIn('class="nav-status"', home_html(self.client))
