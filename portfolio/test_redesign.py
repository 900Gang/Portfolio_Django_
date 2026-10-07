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


class HeroTest(TestCase):
    """The first screen: portrait, giant role word, detection box, stats."""

    def _hero(self):
        html = home_html(self.client)
        start = html.index('<section id="home"')
        return html[start:html.index("</section>", start)]

    def test_portrait_files_exist_in_the_static_tree(self):
        """A missing file would make {% static %} raise under the manifest
        storage in production, taking the whole home page down."""
        for width in (480, 768):
            with self.subTest(width=width):
                self.assertTrue((BASE_DIR / "static" / "img" / f"portrait-{width}.webp").is_file())

    def test_portrait_is_responsive_and_loaded_first(self):
        img = re.search(r'<img class="hero-portrait"[^>]*>', self._hero(), re.S).group(0)
        self.assertRegex(img, r'srcset="[^"]*portrait-480\.webp 480w, [^"]*portrait-768\.webp 768w"')
        self.assertIn('fetchpriority="high"', img)
        self.assertIn('width="768" height="1344"', img)
        self.assertNotIn('loading="lazy"', img)
        self.assertIn(f'alt="Portrait of {settings.SITE_OWNER}"', img)

    def test_decorative_layers_are_hidden_from_assistive_tech(self):
        hero = self._hero()
        self.assertIn('class="hero-word-wrap" aria-hidden="true"', hero)
        self.assertIn('class="hero-detect" aria-hidden="true"', hero)

    def test_detection_label_uses_the_owner_handle(self):
        handle = "_".join(settings.SITE_OWNER.lower().split())
        self.assertIn(f"{handle} · ", self._hero())

    def test_one_h1_and_it_is_the_name(self):
        html = home_html(self.client)
        self.assertEqual(html.count("<h1"), 1)
        self.assertIn(f'<h1 class="hero-title">{settings.SITE_OWNER}</h1>', html)

    def test_stats_count_the_objects_the_page_renders(self):
        for i in range(2):
            Project.objects.create(title=f"P{i}", short_description="d", featured=True)
        for i in range(3):
            Skill.objects.create(name=f"S{i}", category=SkillCategory.BACKEND)
        Certification.objects.create(name="C", issuer="I")
        hero = self._hero()
        for value in (2, 3, 1):
            with self.subTest(value=value):
                self.assertIn(f'data-count="{value}">0{value}</dd>', hero)

    def test_a_long_role_cannot_cause_horizontal_scrolling(self):
        css = (BASE_DIR / "static" / "css" / "sections.css").read_text()
        hero_rule = re.search(r"^\.hero \{([^}]*)\}", css, re.M).group(1)
        self.assertIn("overflow: hidden", hero_rule)
        word_rule = re.search(r"^\.hero-word \{([^}]*)\}", css, re.M).group(1)
        self.assertIn("white-space: nowrap", word_rule)
        with override_settings(SITE_ROLE="Machine Learning Engineer"):
            self.assertIn(
                '<p class="hero-word">Machine Learning Engineer</p>', home_html(self.client)
            )

    def test_hero_rules_use_only_stage_colours(self):
        """In the light theme the page turns light but the hero stays dark, so
        hero rules must never use the page's text, ground or accent tokens."""
        css = (BASE_DIR / "static" / "css" / "sections.css").read_text()
        rules = re.findall(r"^(\.hero[^{]*)\{([^}]*)\}", css, re.M)
        self.assertTrue(rules, "no hero rules found")
        for selector, body in rules:
            with self.subTest(selector=selector.strip()):
                self.assertNotRegex(body, r"var\(--color-(text-|accent\)|bg\)|surface|border)")


class TickerTest(TestCase):
    """The red band of technologies under the hero."""

    def test_used_in_projects_come_first_and_the_list_is_capped(self):
        from .templatetags.portfolio_extras import ticker_skills

        skills = [Skill(name=f"L{i}", status=SkillStatus.LEARNING) for i in range(10)]
        skills += [Skill(name=f"U{i}", status=SkillStatus.USED_IN_PROJECTS) for i in range(10)]
        picked = [skill.name for skill in ticker_skills(skills)]
        self.assertEqual(len(picked), 16)
        self.assertEqual(picked[:10], [f"U{i}" for i in range(10)])

    def test_empty_input_gives_an_empty_ticker(self):
        from .templatetags.portfolio_extras import ticker_skills

        self.assertEqual(ticker_skills([]), [])

    def test_second_copy_is_hidden_from_assistive_tech(self):
        Skill.objects.create(
            name="TensorFlow", category=SkillCategory.BACKEND,
            status=SkillStatus.USED_IN_PROJECTS,
        )
        html = home_html(self.client)
        self.assertEqual(html.count('class="ticker-list"'), 2)
        self.assertIn('class="ticker-list" aria-hidden="true"', html)

    def test_no_band_without_skills(self):
        self.assertNotIn('class="ticker"', home_html(self.client))


class AboutAndProjectsTest(TestCase):
    def test_about_leads_with_a_statement_and_keeps_the_highlights(self):
        html = home_html(self.client)
        self.assertIn('class="about-statement"', html)
        titles = re.findall(r'class="highlight-title">(.*?)</h3>', html)
        self.assertEqual(
            titles,
            ["AI &amp; Machine Learning", "Python Development", "Real-Time &amp; IoT Data"],
        )

    def test_project_cards_are_numbered_in_order(self):
        for i in range(2):
            Project.objects.create(title=f"P{i}", short_description="d", featured=True, order=i)
        numbers = re.findall(
            r'class="project-number" aria-hidden="true">(\d+)<', home_html(self.client)
        )
        self.assertEqual(numbers, ["01", "02"])

    def test_card_shows_at_most_four_technologies(self):
        project = Project.objects.create(title="Many", short_description="d", featured=True)
        project.technologies.set(
            [Skill.objects.create(name=f"T{i}", category=SkillCategory.BACKEND) for i in range(6)]
        )
        html = home_html(self.client)
        card = html[html.index('class="project-card"'):]
        card = card[: card.index("</article>")]
        self.assertEqual(card.count('class="tech-badge"'), 4)


class ProcessSectionTest(TestCase):
    def test_four_steps_render_in_order(self):
        titles = re.findall(r'class="process-title">(.*?)</h3>', home_html(self.client))
        self.assertEqual(titles, ["Data", "Train", "Evaluate", "Deploy"])

    def test_step_copy_matches_the_spec(self):
        html = home_html(self.client)
        for line in (
            "Collect, clean and label image and sensor data.",
            "Build and train models with TensorFlow and Keras.",
            "Measure accuracy, inspect failure cases, iterate.",
            "Wrap models in Python pipelines and real-time backends.",
        ):
            with self.subTest(line=line):
                self.assertIn(line, html)

    def test_process_is_linked_from_the_nav(self):
        html = home_html(self.client)
        self.assertIn('href="#process" class="nav-link"', html)
        self.assertIn('<section id="process"', html)


class SkillsAndJourneyTest(TestCase):
    def test_skill_status_is_a_dot_plus_text_for_assistive_tech(self):
        Skill.objects.create(
            name="Keras", category=SkillCategory.BACKEND, status=SkillStatus.USED_IN_PROJECTS
        )
        html = home_html(self.client)
        self.assertIn('<span class="skill-dot is-used_in_projects" aria-hidden="true"></span>', html)
        self.assertIn('<span class="visually-hidden">(Used in Projects)</span>', html)

    def test_journey_entries_sit_on_a_timeline(self):
        JourneyEntry.objects.create(date="2025-03-01", title="Joined lab", description="d")
        html = home_html(self.client)
        self.assertIn('<ol class="timeline">', html)
        self.assertIn("March 2025", html)


class CredentialsTest(TestCase):
    def test_quote_card_renders_the_agreed_line(self):
        html = home_html(self.client)
        self.assertIn("A model is only as good as the data it learns from.", html)
        self.assertIn('href="#contact" class="quote-cta"', html)

    def test_certifications_live_inside_the_education_section(self):
        html = home_html(self.client)
        education = html.index('<section id="education"')
        certifications = html.index('id="certifications"')
        contact = html.index('<section id="contact"')
        self.assertLess(education, certifications)
        self.assertLess(certifications, contact)


class ContactTest(TestCase):
    def _contact(self):
        html = home_html(self.client)
        return html[html.index('<section id="contact"'):]

    def test_eyebrow_and_heading(self):
        contact = self._contact()
        self.assertIn("07 — Get In Touch", contact)
        self.assertIn("Let's work", contact)

    def test_channel_icons_are_decorative(self):
        self.assertGreaterEqual(
            self._contact().count('class="icon" viewBox="0 0 24 24" aria-hidden="true"'), 4
        )

    def test_phone_row_only_when_configured(self):
        self.assertIn('href="tel:', self._contact())
        with override_settings(SITE_PHONE=""):
            self.assertNotIn('href="tel:', self._contact())


class EmptyDatabaseTest(TestCase):
    """A fresh deploy, before seeding, still renders a complete page."""

    def test_every_section_renders_its_empty_state(self):
        response = self.client.get(reverse("portfolio:home"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        for text in (
            "No featured projects yet. Check back soon!",
            "No skills listed.",
            "No education records.",
            "No certifications listed.",
            "No professional skills listed.",
        ):
            with self.subTest(text=text):
                self.assertIn(text, html)
        self.assertNotIn('class="ticker"', html)
        self.assertNotIn('id="journey"', html)
        self.assertEqual(html.count('data-count="0">00</dd>'), 3)


class ProjectPageTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            title="Hematology", short_description="Blood smear classifier."
        )

    def _html(self):
        return self.client.get(self.project.get_absolute_url()).content.decode()

    def test_title_sits_in_the_dark_hero_band(self):
        html = self._html()
        start = html.index('class="project-detail-hero"')
        band = html[start:html.index("</header>", start)]
        self.assertIn('<h1 class="project-detail-title">Hematology</h1>', band)
        self.assertIn('<body class="has-stage-hero">', html)

    def test_back_link_returns_to_the_projects_section(self):
        self.assertIn('href="/#projects" class="project-breadcrumb-link"', self._html())


class ErrorPagesTest(TestCase):
    def test_404_shows_the_code_large(self):
        response = self.client.get("/projects/missing/")
        self.assertContains(response, 'class="error-code"', status_code=404)

    def test_500_uses_the_new_palette(self):
        html = (BASE_DIR / "templates" / "500.html").read_text()
        self.assertIn("#070707", html)
        self.assertIn("Anton", html)


def _strip_keyframes(css):
    """Remove every @keyframes block (balanced braces) from a stylesheet."""
    out, position = [], 0
    while True:
        start = css.find("@keyframes", position)
        if start == -1:
            out.append(css[position:])
            return "".join(out)
        out.append(css[position:start])
        depth, index = 0, css.index("{", start)
        while True:
            if css[index] == "{":
                depth += 1
            elif css[index] == "}":
                depth -= 1
                if depth == 0:
                    break
            index += 1
        position = index + 1


class MotionTest(TestCase):
    """Motion must never cost a visitor content or comfort."""

    def _css(self):
        return (BASE_DIR / "static" / "css" / "motion.css").read_text()

    def test_reduced_motion_switches_animation_off(self):
        css = self._css()
        block = css[css.index("@media (prefers-reduced-motion: reduce)"):]
        self.assertIn("animation-duration: 0.01ms !important", block)
        self.assertIn("transition-duration: 0.01ms !important", block)

    def test_hidden_states_only_apply_once_motion_is_ready(self):
        """With JavaScript off, or motion.js blocked, nothing may stay hidden."""
        css = _strip_keyframes(self._css())
        hidden = [
            selector
            for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css)
            if re.search(r"opacity:\s*0\s*;", body)
        ]
        self.assertTrue(hidden, "expected at least one hidden-before-reveal rule")
        for selector in hidden:
            for part in selector.split(","):
                with self.subTest(selector=part.strip()):
                    self.assertIn(".motion-ready", part)

    def test_keyframes_animate_only_transform_and_opacity(self):
        frames = re.findall(
            r"@keyframes\s+([\w-]+)\s*\{((?:[^{}]*\{[^{}]*\})*)\s*\}", self._css()
        )
        self.assertTrue(frames, "no keyframes found")
        for name, body in frames:
            with self.subTest(keyframes=name):
                self.assertLessEqual(
                    set(re.findall(r"([a-z-]+)\s*:", body)), {"opacity", "transform"}
                )

    def test_motion_flag_is_withdrawn_if_motion_js_never_runs(self):
        theme = (BASE_DIR / "static" / "js" / "theme.js").read_text()
        motion = (BASE_DIR / "static" / "js" / "motion.js").read_text()
        self.assertIn("motion-ready", theme)
        self.assertIn("prefers-reduced-motion: reduce", theme)
        self.assertIn("window.portfolioMotion", theme)
        self.assertIn("window.portfolioMotion = true", motion)

    def test_motion_assets_are_wired_into_every_page(self):
        html = home_html(self.client)
        self.assertIn("css/motion.css", html)
        self.assertIn('js/motion.js" defer', html)
