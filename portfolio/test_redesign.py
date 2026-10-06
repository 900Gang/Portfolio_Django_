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


class HandleFilterTest(SimpleTestCase):
    """The label on the hero's detection box, derived from SITE_OWNER."""

    def test_lowercases_and_joins_words_with_underscores(self):
        from .templatetags.portfolio_extras import handle

        self.assertEqual(handle("Anand N"), "anand_n")
        self.assertEqual(handle("  Mary   Ann Lee "), "mary_ann_lee")
        self.assertEqual(handle(""), "")


class PortraitCommandTest(SimpleTestCase):
    """make_portrait exports the hero photo at the widths the template serves."""

    def _source(self, folder, size=(800, 1400)):
        path = Path(folder) / "source.jpg"
        Image.new("RGB", size, (40, 40, 40)).save(path, "JPEG")
        return path

    def test_writes_both_widths_as_webp_keeping_the_aspect_ratio(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self._source(tmp)
            call_command("make_portrait", str(source), "--output-dir", tmp, stdout=io.StringIO())
            for width in (480, 768):
                with self.subTest(width=width):
                    with Image.open(Path(tmp) / f"portrait-{width}.webp") as image:
                        self.assertEqual(image.format, "WEBP")
                        self.assertEqual(image.size, (width, round(1400 * width / 800)))

    def test_missing_source_is_a_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(CommandError, "does not exist"):
                call_command(
                    "make_portrait", str(Path(tmp) / "nope.jpg"),
                    "--output-dir", tmp, stdout=io.StringIO(),
                )


class LinkPreviewCommandTest(SimpleTestCase):
    """make_og_image draws the card in the new palette, with an optional headshot."""

    def test_renders_at_open_graph_size_on_the_dark_ground(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "og.png"
            call_command("make_og_image", "--output", str(out), stdout=io.StringIO())
            with Image.open(out) as image:
                self.assertEqual(image.size, (1200, 630))
                self.assertEqual(image.convert("RGB").getpixel((4, 4)), (7, 7, 7))

    def test_places_the_headshot_on_the_right_when_given_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            photo = Path(tmp) / "head.jpg"
            Image.new("RGB", (400, 400), (0, 120, 255)).save(photo, "JPEG", quality=95)
            out = Path(tmp) / "og.png"
            call_command(
                "make_og_image", "--photo", str(photo), "--output", str(out),
                stdout=io.StringIO(),
            )
            with Image.open(out) as image:
                # Right edge of the photo, clear of the detection box.
                red, _green, blue = image.convert("RGB").getpixel((1200 - 72 - 30, 315))
                self.assertGreater(blue, 200)
                self.assertLess(red, 40)

    def test_footer_line_never_runs_into_the_headshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            photo = Path(tmp) / "head.jpg"
            Image.new("RGB", (400, 400), (0, 120, 255)).save(photo, "JPEG", quality=95)
            out = Path(tmp) / "og.png"
            call_command(
                "make_og_image", "--photo", str(photo), "--output", str(out),
                stdout=io.StringIO(),
            )
            with Image.open(out) as image:
                rgb = image.convert("RGB")
                # The photo's left edge, level with the footer text.
                for x in range(662, 720, 3):
                    for y in range(538, 550):
                        red, _green, blue = rgb.getpixel((x, y))
                        self.assertTrue(blue > 200 and red < 40, (x, y, rgb.getpixel((x, y))))

    def test_missing_photo_is_a_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(CommandError, "does not exist"):
                call_command(
                    "make_og_image", "--photo", str(Path(tmp) / "nope.jpg"),
                    "--output", str(Path(tmp) / "og.png"), stdout=io.StringIO(),
                )
