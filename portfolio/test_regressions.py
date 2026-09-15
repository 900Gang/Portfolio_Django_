"""
Regression tests added during the refactor.

`portfolio/tests.py` is the pre-existing suite and was deliberately left
untouched: it is the behavioural baseline. Everything here either pins down a
bug that was found and fixed, or locks in a property the refactor relies on so
a future change cannot silently undo it.
"""
import io
import re
from pathlib import Path

from django.conf import settings
from django.contrib.admin.sites import site as admin_site
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from .models import (
    Certification,
    Education,
    JourneyEntry,
    ProfessionalSkill,
    Project,
    Skill,
    SkillCategory,
    SkillStatus,
)

BASE_DIR = Path(settings.BASE_DIR)


class AdminSmokeTest(TestCase):
    """
    The admin had no test coverage at all, which is how a copy-paste bug
    (`ProfessionalSkillAdmin` checking `obj.is_read`, a ContactMessage field)
    survived. These walk every registered model through the admin.
    """

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="pw"
        )
        cls.instances = {
            Skill: Skill.objects.create(name="Python", category=SkillCategory.BACKEND),
            Project: Project.objects.create(title="P", short_description="d"),
            JourneyEntry: JourneyEntry.objects.create(
                date="2025-01-01", title="J", description="d"
            ),
            Education: Education.objects.create(
                institution="U", degree="B.Tech",
                start_date="2022-08-01", end_date="2026-05-31",
            ),
            Certification: Certification.objects.create(name="C", issuer="I"),
            ProfessionalSkill: ProfessionalSkill.objects.create(name="Teamwork"),
        }

    def setUp(self):
        self.client.force_login(self.admin_user)

    def test_every_registered_changelist_loads(self):
        for model in admin_site._registry:
            url = reverse(
                f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"
            )
            with self.subTest(model=model.__name__):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_every_change_page_loads(self):
        """Regression: this returned a 500 (AttributeError) for ProfessionalSkill."""
        for model, instance in self.instances.items():
            url = reverse(
                f"admin:{model._meta.app_label}_{model._meta.model_name}_change",
                args=[instance.pk],
            )
            with self.subTest(model=model.__name__):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_professional_skill_change_permission_does_not_raise(self):
        model_admin = admin_site._registry[ProfessionalSkill]
        instance = self.instances[ProfessionalSkill]
        request = type("Req", (), {"user": self.admin_user})()
        self.assertTrue(model_admin.has_change_permission(request, instance))

    def test_professional_skill_is_addable(self):
        """Regression: has_add_permission was hard-coded False, so the model
        could never be populated through the admin."""
        model_admin = admin_site._registry[ProfessionalSkill]
        request = type("Req", (), {"user": self.admin_user})()
        self.assertTrue(model_admin.has_add_permission(request))

        url = reverse("admin:portfolio_professionalskill_add")
        self.assertEqual(self.client.get(url).status_code, 200)


class ProjectTypeTest(TestCase):
    """
    The 'Academic Project' / 'Personal Project' / 'Project' classification was
    duplicated verbatim in two templates. It now lives on the model; these
    tests pin the original truth table and the card/detail agreement.
    """

    def test_major_project_marker(self):
        p = Project.objects.create(
            title="A", short_description="Major project using ESP32"
        )
        self.assertEqual(p.project_type, "Academic Project")

    def test_personal_project_marker(self):
        p = Project.objects.create(
            title="B", short_description="Personal project building a CNN"
        )
        self.assertEqual(p.project_type, "Personal Project")

    def test_marker_found_in_long_description(self):
        p = Project.objects.create(
            title="C", short_description="Summary", description="A Major project write-up"
        )
        self.assertEqual(p.project_type, "Academic Project")

    def test_default_when_no_marker(self):
        p = Project.objects.create(title="D", short_description="Just a thing")
        self.assertEqual(p.project_type, "Project")

    def test_major_takes_precedence_over_personal(self):
        """Matches the original template's if/elif ordering."""
        p = Project.objects.create(
            title="E",
            short_description="Major project",
            description="Personal project",
        )
        self.assertEqual(p.project_type, "Academic Project")

    def test_card_and_detail_render_the_same_label(self):
        project = Project.objects.create(
            title="Shared Label",
            short_description="Personal project doing things",
            featured=True,
        )
        home = self.client.get(reverse("portfolio:home")).content.decode()
        detail = self.client.get(
            reverse("portfolio:project_detail", kwargs={"slug": project.slug})
        ).content.decode()

        card_label = re.search(r'project-type-badge">\s*(.*?)\s*<', home).group(1)
        detail_label = re.search(
            r'project-detail-type-badge">\s*(.*?)\s*<', detail
        ).group(1)

        self.assertEqual(card_label, "Personal Project")
        self.assertEqual(card_label, detail_label)


class SkillsGroupingTest(TestCase):
    """Regression: the skills headings rendered the raw DB value ('backend')
    rather than the human label ('Backend')."""

    def test_group_heading_uses_human_label(self):
        Skill.objects.create(name="Python", category=SkillCategory.BACKEND)
        Skill.objects.create(name="React", category=SkillCategory.FRONTEND)
        Skill.objects.create(name="Git", category=SkillCategory.TOOLS)

        html = self.client.get(reverse("portfolio:home")).content.decode()
        headings = re.findall(r'skills-group-title">\s*(.*?)\s*</h3>', html, re.S)

        # "&" is HTML-escaped by the template engine, as it should be.
        expected = sorted(
            SkillCategory(value).label.replace("&", "&amp;")
            for value in (
                SkillCategory.BACKEND, SkillCategory.FRONTEND, SkillCategory.TOOLS
            )
        )
        self.assertEqual(sorted(headings), expected)
        for raw in ("backend", "frontend", "tools"):
            self.assertNotIn(f'skills-group-title">\n                    {raw}', html)

    def test_all_skills_still_rendered_under_their_group(self):
        Skill.objects.create(name="Python", category=SkillCategory.BACKEND, order=1)
        Skill.objects.create(name="Django", category=SkillCategory.BACKEND, order=2)
        response = self.client.get(reverse("portfolio:home"))
        self.assertContains(response, "Python")
        self.assertContains(response, "Django")


class ContactFormRenderingTest(TestCase):
    """
    The four hand-written form-group blocks were replaced by a loop over the
    form plus a shared partial. These assert the rendered markup is equivalent.
    """

    def test_all_fields_render_with_label_and_required_marker(self):
        html = self.client.get(reverse("portfolio:home")).content.decode()
        self.assertEqual(html.count('class="form-group"'), 4)
        self.assertEqual(html.count('class="form-required"'), 4)
        for label in ("Name", "Email", "Subject", "Message"):
            self.assertRegex(html, rf'class="form-label">\s*{label}\b')
        for name in ("name", "email", "subject", "message"):
            self.assertIn(f'name="{name}"', html)

    def test_labels_are_bound_to_their_inputs(self):
        html = self.client.get(reverse("portfolio:home")).content.decode()
        for field_id in ("id_name", "id_email", "id_subject", "id_message"):
            self.assertIn(f'for="{field_id}"', html)
            self.assertIn(f'id="{field_id}"', html)

    def test_widget_attrs_from_the_form_survive(self):
        html = self.client.get(reverse("portfolio:home")).content.decode()
        self.assertIn('placeholder="Your name"', html)
        self.assertIn('placeholder="your.email@example.com"', html)
        self.assertIn('autocomplete="email"', html)
        self.assertIn('rows="5"', html)

    def test_errors_render_inside_form_error_block(self):
        response = self.client.post(
            reverse("portfolio:home"),
            {"name": "", "email": "bad", "subject": "s", "message": "m"},
        )
        html = response.content.decode()
        self.assertIn('class="form-error"', html)
        self.assertIn("Enter a valid email address", html)
        self.assertIn("This field is required", html)


class SeedCommandTest(TestCase):
    """Regression: re-running the seed duplicated every record except skills."""

    def _counts(self):
        return {
            m.__name__: m.objects.count()
            for m in (Skill, Project, Education, Certification, ProfessionalSkill)
        }

    def test_seed_is_idempotent(self):
        out = io.StringIO()
        call_command("populate_portfolio", stdout=out)
        first = self._counts()
        call_command("populate_portfolio", stdout=out)
        self.assertEqual(first, self._counts())

    def test_seed_produces_the_expected_content(self):
        call_command("populate_portfolio", stdout=io.StringIO())
        self.assertEqual(
            self._counts(),
            {
                "Skill": 38,
                "Project": 2,
                "Education": 3,
                "Certification": 3,
                "ProfessionalSkill": 7,
            },
        )
        self.assertEqual(JourneyEntry.objects.count(), 0)

    def test_reseeding_does_not_accumulate_technology_links(self):
        out = io.StringIO()
        call_command("populate_portfolio", stdout=out)
        before = sorted(
            (p.title, t.name) for p in Project.objects.all() for t in p.technologies.all()
        )
        call_command("populate_portfolio", stdout=out)
        after = sorted(
            (p.title, t.name) for p in Project.objects.all() for t in p.technologies.all()
        )
        self.assertEqual(before, after)

    def test_prune_removes_skills_outside_the_seed(self):
        Skill.objects.create(name="Obsolete", category=SkillCategory.CONCEPTS)
        call_command("populate_portfolio", "--prune", stdout=io.StringIO())
        self.assertFalse(Skill.objects.filter(name="Obsolete").exists())


class QueryCountTest(TestCase):
    """
    The homepage is already free of N+1s thanks to prefetch_related. These
    lock that in: the query count must not grow with the number of rows.
    """

    def _seed(self, projects, techs_per_project):
        skills = [
            Skill.objects.create(name=f"S{i}", category=SkillCategory.BACKEND)
            for i in range(techs_per_project)
        ]
        for i in range(projects):
            p = Project.objects.create(
                title=f"P{i}", short_description="d", featured=True
            )
            p.technologies.set(skills)

    def test_homepage_query_count_is_constant(self):
        self._seed(2, 2)
        with CaptureQueriesContext(connection) as small:
            self.client.get(reverse("portfolio:home"))

        Project.objects.all().delete()
        Skill.objects.all().delete()
        self._seed(6, 5)
        with CaptureQueriesContext(connection) as large:
            self.client.get(reverse("portfolio:home"))

        self.assertEqual(len(small), len(large))
        self.assertLessEqual(len(large), 8)

    def test_project_detail_query_count_is_constant(self):
        project = Project.objects.create(title="D", short_description="d")
        project.technologies.set(
            [
                Skill.objects.create(name=f"T{i}", category=SkillCategory.BACKEND)
                for i in range(8)
            ]
        )
        with CaptureQueriesContext(connection) as ctx:
            self.client.get(
                reverse("portfolio:project_detail", kwargs={"slug": project.slug})
            )
        self.assertLessEqual(len(ctx), 3)


class SettingsTest(TestCase):
    """Settings now read the environment; these cover the loader and the
    fail-closed defaults."""

    def test_secret_key_is_not_the_committed_placeholder(self):
        leaked = "django-insecure-6yq*5%0jf^#a59#8k7!&+&4c21$ss-ui&l+4=@qn&z)yj)7)r3"
        self.assertNotEqual(settings.SECRET_KEY, leaked)

    def test_env_helpers_parse_types(self):
        import os

        from portfolio_project.env import get_bool, get_list, get_str

        os.environ["_T_BOOL"] = "True"
        os.environ["_T_LIST"] = "a, b ,c"
        try:
            self.assertTrue(get_bool("_T_BOOL"))
            self.assertFalse(get_bool("_T_MISSING"))
            self.assertTrue(get_bool("_T_MISSING", default=True))
            self.assertEqual(get_list("_T_LIST"), ["a", "b", "c"])
            self.assertEqual(get_list("_T_MISSING"), [])
            self.assertEqual(get_str("_T_MISSING", "fallback"), "fallback")
            with self.assertRaises(RuntimeError):
                get_str("_T_MISSING")
        finally:
            del os.environ["_T_BOOL"], os.environ["_T_LIST"]

    def test_real_environment_wins_over_dotenv_file(self):
        import os
        import tempfile

        from portfolio_project.env import load_dotenv

        os.environ["_T_PRESET"] = "from-environ"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("_T_PRESET=from-file\n_T_NEW=from-file\n")
            load_dotenv(path)
            try:
                self.assertEqual(os.environ["_T_PRESET"], "from-environ")
                self.assertEqual(os.environ["_T_NEW"], "from-file")
            finally:
                del os.environ["_T_PRESET"], os.environ["_T_NEW"]

    def test_load_dotenv_tolerates_a_missing_file(self):
        from portfolio_project.env import load_dotenv

        load_dotenv(Path("/nonexistent/.env"))  # must not raise


class StaticAssetTest(TestCase):
    """
    Cheap lints for the CSS/JS bugs found during the refactor. They are static
    checks rather than browser tests, but they are what would have caught the
    original defects.
    """

    def test_no_css_variables_inside_media_query_conditions(self):
        """Regression: `@media (min-width: var(--breakpoint-md))` is invalid,
        so browsers dropped every rule in responsive.css."""
        offenders = []
        for path in (BASE_DIR / "static" / "css").glob("*.css"):
            for number, line in enumerate(path.read_text().splitlines(), 1):
                if line.lstrip().startswith("@media") and "var(" in line:
                    offenders.append(f"{path.name}:{number}: {line.strip()}")
        self.assertEqual(offenders, [])

    def test_button_variants_are_defined_once(self):
        """Regression: .btn-primary/.btn-secondary were byte-identical in both
        base.css and components.css."""
        definitions = {}
        for path in (BASE_DIR / "static" / "css").glob("*.css"):
            text = path.read_text()
            for selector in (".btn-primary", ".btn-secondary"):
                if re.search(rf"^\{selector} \{{", text, re.M):
                    definitions.setdefault(selector, []).append(path.name)
        for selector, files in definitions.items():
            self.assertEqual(files, sorted(set(files)), selector)
            self.assertEqual(len(files), 1, f"{selector} defined in {files}")

    def test_alert_close_button_has_a_handler(self):
        """Regression: the button was rendered and styled but inert."""
        js = (BASE_DIR / "static" / "js" / "navigation.js").read_text()
        self.assertIn("alert-close", js)

    def test_every_stylesheet_linked_in_base_exists(self):
        base = (BASE_DIR / "templates" / "base.html").read_text()
        for name in re.findall(r"static 'css/([^']+)'", base):
            self.assertTrue((BASE_DIR / "static" / "css" / name).is_file(), name)


# ---------------------------------------------------------------------------
# Presentation pass: image fallback, empty-section handling, document head,
# resume gating, and theme tokens.
# ---------------------------------------------------------------------------


class ProjectImageFallbackTest(TestCase):
    """
    Regression: `{% if project.image %}` is truthy for any stored path, so a
    record whose file had been lost rendered a broken <img>. Both project
    images on the live site were 404ing.
    """

    def setUp(self):
        self.project = Project.objects.create(
            title="Imaged", short_description="d", featured=True
        )

    def test_has_image_is_false_when_the_file_is_missing(self):
        self.project.image.name = "projects/gone.png"
        self.project.save()
        self.assertTrue(bool(self.project.image))  # the path is still set
        self.assertFalse(self.project.has_image)   # but the file is not there

    def test_has_image_is_false_when_no_image_is_set(self):
        self.assertFalse(self.project.has_image)

    def test_has_image_is_true_when_the_file_exists(self):
        import tempfile

        from django.test import override_settings

        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                target = Path(tmp) / "projects"
                target.mkdir(parents=True)
                (target / "there.png").write_bytes(b"\x89PNG\r\n\x1a\n")
                self.project.image.name = "projects/there.png"
                self.project.save()
                self.assertTrue(self.project.has_image)

    def test_missing_file_renders_the_placeholder_not_a_broken_image(self):
        self.project.image.name = "projects/gone.png"
        self.project.save()

        for url in (
            reverse("portfolio:home"),
            reverse("portfolio:project_detail", kwargs={"slug": self.project.slug}),
        ):
            with self.subTest(url=url):
                html = self.client.get(url).content.decode()
                self.assertNotIn("projects/gone.png", html)
                self.assertIn("project-image-fallback", html)


class JourneySectionVisibilityTest(TestCase):
    """The section and its nav entry are hidden when there is nothing to show."""

    def test_hidden_when_there_are_no_entries(self):
        html = self.client.get(reverse("portfolio:home")).content.decode()
        self.assertNotIn('id="journey"', html)
        self.assertNotIn('href="#journey"', html)
        self.assertNotIn("No journey entries yet.", html)

    def test_shown_when_entries_exist(self):
        JourneyEntry.objects.create(
            date="2025-01-01", title="Started Django", description="d"
        )
        html = self.client.get(reverse("portfolio:home")).content.decode()
        self.assertIn('id="journey"', html)
        self.assertIn('href="#journey"', html)
        self.assertIn("Started Django", html)

    def test_nav_entry_tracks_the_section_on_detail_pages_too(self):
        project = Project.objects.create(title="P", short_description="d")
        url = reverse("portfolio:project_detail", kwargs={"slug": project.slug})
        self.assertNotIn('href="#journey"', self.client.get(url).content.decode())

        JourneyEntry.objects.create(date="2025-01-01", title="J", description="d")
        self.assertIn('href="#journey"', self.client.get(url).content.decode())


class DocumentHeadTest(TestCase):
    """The head was a bare title and two meta tags; links previewed as nothing."""

    def test_homepage_head_identifies_the_owner(self):
        html = self.client.get(reverse("portfolio:home")).content.decode()
        self.assertIn(f"<title>{settings.SITE_OWNER} — {settings.SITE_ROLE}</title>", html)
        self.assertNotIn("<title>Home - Portfolio</title>", html)

    def test_homepage_has_description_and_link_preview_tags(self):
        html = self.client.get(reverse("portfolio:home")).content.decode()
        for needle in (
            'name="description"',
            'property="og:title"',
            'property="og:description"',
            'property="og:type"',
            'property="og:url"',
            'name="twitter:card"',
            'rel="canonical"',
            'rel="icon"',
            'name="theme-color"',
        ):
            with self.subTest(tag=needle):
                self.assertIn(needle, html)

    def test_detail_page_overrides_title_and_description(self):
        project = Project.objects.create(
            title="Hematology Screening",
            short_description="Personal project classifying blood smear images.",
        )
        html = self.client.get(
            reverse("portfolio:project_detail", kwargs={"slug": project.slug})
        ).content.decode()
        self.assertIn("<title>Hematology Screening — Anand N</title>", html)
        self.assertIn("blood smear images", html)
        self.assertIn('content="article"', html)

    def test_favicon_file_exists(self):
        self.assertTrue((BASE_DIR / "static" / "img" / "favicon.svg").is_file())


class ResumeLinkTest(TestCase):
    """The button appears only once the file is actually present, so the site
    never ships a download link that 404s."""

    def test_the_configured_resume_actually_exists(self):
        """Regression: the résumé was added to static/files/ under one name
        while RESUME_STATIC_PATH still pointed at another, so the download
        button stayed hidden and nothing anywhere said why."""
        self.assertTrue(
            (BASE_DIR / "static" / settings.RESUME_STATIC_PATH).is_file(),
            f"RESUME_STATIC_PATH points at {settings.RESUME_STATIC_PATH!r}, "
            f"which is not in the static tree",
        )

    def test_it_is_offered_under_a_presentable_filename(self):
        """The working filename on disk is not what should land in a
        recruiter's downloads folder."""
        html = self.client.get(reverse("portfolio:home")).content.decode()
        self.assertIn(f'download="{settings.RESUME_DOWNLOAD_NAME}"', html)
        self.assertTrue(settings.RESUME_DOWNLOAD_NAME.endswith(".pdf"))

    def test_hidden_when_the_file_is_absent(self):
        from django.test import override_settings

        with override_settings(RESUME_STATIC_PATH="files/definitely-missing.pdf"):
            html = self.client.get(reverse("portfolio:home")).content.decode()
            self.assertNotIn("definitely-missing.pdf", html)
            self.assertNotIn("download=", html)

    def test_shown_when_the_file_is_present(self):
        from django.test import override_settings

        # favicon.svg is a file that certainly resolves through the finders.
        # Asserted on the href rather than the button copy, so rewording the
        # label is not a test failure.
        with override_settings(RESUME_STATIC_PATH="img/favicon.svg"):
            html = self.client.get(reverse("portfolio:home")).content.decode()
            self.assertIn("img/favicon.svg", html)
            self.assertIn("download=", html)


class ThemeTokenTest(TestCase):
    """Colour lives in tokens only, and every colour token has a dark value."""

    def _variables(self):
        return (BASE_DIR / "static" / "css" / "variables.css").read_text()

    def test_no_hardcoded_colours_outside_the_token_file(self):
        offenders = []
        for path in (BASE_DIR / "static" / "css").glob("*.css"):
            if path.name == "variables.css":
                continue
            for number, line in enumerate(path.read_text().splitlines(), 1):
                if re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(", line):
                    offenders.append(f"{path.name}:{number}: {line.strip()}")
        self.assertEqual(offenders, [])

    def test_every_colour_token_is_redefined_for_dark_mode(self):
        css = self._variables()
        dark = css[css.index("prefers-color-scheme: dark"):]
        light_block = css[: css.index("prefers-color-scheme: dark")]

        light_tokens = set(re.findall(r"(--color-[a-z-]+):", light_block))
        dark_tokens = set(re.findall(r"(--color-[a-z-]+):", dark))

        self.assertTrue(light_tokens, "no colour tokens found")
        self.assertEqual(
            light_tokens - dark_tokens,
            set(),
            "colour tokens with no dark-mode value",
        )

    def test_dark_mode_is_declared(self):
        css = self._variables()
        self.assertIn("prefers-color-scheme: dark", css)
        self.assertIn("color-scheme: dark", css)

    def test_palette_is_no_longer_stock_bootstrap(self):
        css = self._variables()
        for bootstrap_default in ("#0d6efd", "#198754", "#dc3545", "#212529", "#dee2e6"):
            with self.subTest(colour=bootstrap_default):
                self.assertNotIn(bootstrap_default, css)

    def test_fonts_are_declared_with_fallback_stacks(self):
        css = self._variables()
        self.assertIn("IBM Plex Sans", css)
        self.assertIn("IBM Plex Mono", css)
        # A webfont that fails to load must still land on a real stack.
        self.assertIn("system-ui", css)
        self.assertIn("monospace", css)

    def test_stylesheet_link_for_the_webfont_is_present(self):
        html = self.client.get(reverse("portfolio:home")).content.decode()
        self.assertIn("fonts.googleapis.com", html)
        self.assertIn("IBM+Plex+Sans", html)


# ---------------------------------------------------------------------------
# Professional pass: crawler endpoints, link previews, theming, navigation
# wiring, spam protection and error pages.
# ---------------------------------------------------------------------------


class CrawlerEndpointTest(TestCase):
    """robots.txt and sitemap.xml exist and agree with each other."""

    def setUp(self):
        self.project = Project.objects.create(
            title="Indexable Project",
            short_description="Should appear in the sitemap.",
        )

    def test_robots_txt_points_at_the_sitemap(self):
        response = self.client.get("/robots.txt")
        body = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertIn("Disallow: /admin/", body)
        self.assertIn("/sitemap.xml", body)

    def test_sitemap_lists_home_and_every_project(self):
        response = self.client.get("/sitemap.xml")
        body = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn(reverse("portfolio:home"), body)
        self.assertIn(self.project.get_absolute_url(), body)

    def test_sitemap_survives_a_project_with_no_explicit_slug(self):
        """Regression: the sitemap 500'd because Project had no
        get_absolute_url, which only shows up once a project exists."""
        Project.objects.create(title="Another One", short_description="x")
        self.assertEqual(self.client.get("/sitemap.xml").status_code, 200)


class AbsoluteUrlTest(TestCase):
    def test_project_url_is_defined_on_the_model(self):
        project = Project.objects.create(title="Routed", short_description="x")
        self.assertEqual(
            project.get_absolute_url(),
            reverse("portfolio:project_detail", kwargs={"slug": project.slug}),
        )

    def test_card_links_through_the_model_method(self):
        project = Project.objects.create(
            title="Routed", short_description="x", featured=True
        )
        html = self.client.get(reverse("portfolio:home")).content.decode()
        self.assertIn(f'href="{project.get_absolute_url()}"', html)


class LinkPreviewImageTest(TestCase):
    """A portfolio is shared on LinkedIn and Slack; a bare preview card is a
    wasted first impression."""

    def test_og_image_file_exists_in_the_static_tree(self):
        self.assertTrue(
            (BASE_DIR / "static" / settings.OG_IMAGE_STATIC_PATH).is_file(),
            "run `python manage.py make_og_image`",
        )

    def test_og_image_is_absolute_because_scrapers_do_not_resolve_relatives(self):
        html = self.client.get(reverse("portfolio:home")).content.decode()
        match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        self.assertIsNotNone(match, "no og:image tag")
        self.assertRegex(match.group(1), r"^https?://")

    def test_large_summary_card_is_requested_when_an_image_exists(self):
        html = self.client.get(reverse("portfolio:home")).content.decode()
        self.assertIn('name="twitter:card" content="summary_large_image"', html)

    def test_tags_are_dropped_when_the_image_is_missing(self):
        from django.test import override_settings

        with override_settings(OG_IMAGE_STATIC_PATH="img/not-generated-yet.png"):
            html = self.client.get(reverse("portfolio:home")).content.decode()
            self.assertNotIn("og:image", html)
            self.assertIn('name="twitter:card" content="summary"', html)


class StructuredDataTest(TestCase):
    def test_homepage_publishes_a_person_graph(self):
        html = self.client.get(reverse("portfolio:home")).content.decode()
        self.assertIn('type="application/ld+json"', html)
        self.assertIn('"@type": "Person"', html)
        self.assertIn(settings.SITE_OWNER, html)

    def test_project_page_publishes_a_creativework_graph_instead(self):
        project = Project.objects.create(title="Graphed", short_description="x")
        html = self.client.get(project.get_absolute_url()).content.decode()
        self.assertIn('"@type": "CreativeWork"', html)
        # The Person graph belongs on the home page; here the person appears
        # only as the nested author, without the profile fields.
        self.assertNotIn('"jobTitle"', html)


class ThemeToggleTest(TestCase):
    """Dark mode is a manual choice as well as an OS one."""

    def _variables(self):
        return (BASE_DIR / "static" / "css" / "variables.css").read_text()

    def test_toggle_control_is_rendered(self):
        html = self.client.get(reverse("portfolio:home")).content.decode()
        self.assertIn('class="theme-toggle"', html)

    def test_theme_script_runs_before_the_body_to_avoid_a_flash(self):
        html = self.client.get(reverse("portfolio:home")).content.decode()
        script = html.index("js/theme.js")
        self.assertLess(script, html.index("<body>"), "theme.js must be in <head>")
        self.assertNotIn("js/theme.js\" defer", html)

    def test_manual_choice_can_override_the_os_in_both_directions(self):
        """A [data-theme="dark"] block alone cannot force light mode on a
        machine whose OS is dark; the light escape hatch has to exist too."""
        css = self._variables()
        self.assertIn('[data-theme="dark"]', css)
        self.assertIn(':not([data-theme="light"])', css)

    def test_stored_preference_reads_are_guarded(self):
        """localStorage throws in private mode and with site data blocked."""
        js = (BASE_DIR / "static" / "js" / "theme.js").read_text()
        self.assertIn("localStorage", js)
        self.assertIn("catch", js)


class NavigationWiringTest(TestCase):
    def setUp(self):
        JourneyEntry.objects.create(
            date="2025-01-01", title="Entry", description="d"
        )

    def test_every_nav_anchor_resolves_to_a_section_on_the_page(self):
        """A nav link to an id that does not exist is a dead link that no
        amount of CSS will reveal."""
        html = self.client.get(reverse("portfolio:home")).content.decode()
        anchors = re.findall(r'class="nav-link"[^>]*>|href="#([a-z-]+)" class="nav-link"', html)
        targets = re.findall(r'href="#([a-z-]+)" class="nav-link"', html)
        self.assertTrue(targets, "no nav links found")
        for target in targets:
            with self.subTest(anchor=target):
                self.assertIn(f'id="{target}"', html)

    def test_active_state_is_driven_by_script_not_left_dead(self):
        """Regression: .nav-link.active was styled but nothing ever set it."""
        js = (BASE_DIR / "static" / "js" / "navigation.js").read_text()
        css = (BASE_DIR / "static" / "css" / "components.css").read_text()
        self.assertIn(".nav-link.active", css)
        self.assertIn("IntersectionObserver", js)
        self.assertIn("'active'", js)

    def test_anchor_targets_clear_the_sticky_header(self):
        """Without scroll padding, jumping to a section parks its heading
        underneath the fixed nav bar."""
        css = (BASE_DIR / "static" / "css" / "reset.css").read_text()
        self.assertIn("scroll-padding-top", css)


class ContactHoneypotTest(TestCase):
    """Spam protection that costs a visitor nothing."""

    def _payload(self, **overrides):
        payload = {
            "name": "Recruiter",
            "email": "recruiter@example.com",
            "subject": "Role",
            "message": "We have an opening.",
        }
        payload.update(overrides)
        return payload

    def test_a_genuine_submission_still_saves(self):
        from .models import ContactMessage

        response = self.client.post(reverse("portfolio:home"), self._payload())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_a_filled_trap_is_rejected_without_saving(self):
        from .models import ContactMessage

        response = self.client.post(
            reverse("portfolio:home"), self._payload(website="http://spam.example")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_the_trap_is_hidden_from_people_and_from_screen_readers(self):
        html = self.client.get(reverse("portfolio:home")).content.decode()
        self.assertIn('class="form-trap"', html)
        self.assertIn('name="website"', html)
        # Off-screen rather than display:none, which some bots skip.
        css = (BASE_DIR / "static" / "css" / "components.css").read_text()
        trap = css[css.index(".form-trap {"):]
        self.assertIn("position: absolute", trap[: trap.index("}")])

    def test_the_trap_is_not_counted_as_a_visible_required_field(self):
        html = self.client.get(reverse("portfolio:home")).content.decode()
        self.assertEqual(html.count('class="form-group"'), 4)


class ErrorPageTest(TestCase):
    def test_missing_project_renders_the_branded_404(self):
        response = self.client.get("/projects/no-such-project/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(
            response, "This page doesn't exist", status_code=404
        )

    def test_500_template_does_not_depend_on_context_processors(self):
        """handler500 renders with an empty context, so any {{ site_* }} in
        the template would silently render as nothing."""
        html = (BASE_DIR / "templates" / "500.html").read_text()
        self.assertNotIn("{{", html)
        self.assertNotIn("{%", html)


class StylesheetHygieneTest(TestCase):
    def test_no_orphaned_stylesheets_are_left_in_the_tree(self):
        """Regression: utilities.css was 341 lines of rules no template used.
        Every file under static/css must be linked by base.html."""
        linked = set(
            re.findall(r"static 'css/([^']+)'", (BASE_DIR / "templates" / "base.html").read_text())
        )
        on_disk = {path.name for path in (BASE_DIR / "static" / "css").glob("*.css")}
        self.assertEqual(on_disk - linked, set(), "stylesheet on disk but never linked")

    def test_no_session_scratch_files_are_served_from_static(self):
        """Anything under static/ is published by collectstatic."""
        offenders = [
            path.name
            for path in (BASE_DIR / "static").glob("*")
            if path.is_file() and path.suffix in {".txt", ".log", ".bak"}
        ]
        self.assertEqual(offenders, [])
