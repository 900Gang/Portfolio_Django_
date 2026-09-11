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
        self.assertEqual(
            sorted(headings), ["Backend", "Frontend", "Tools &amp; Workflow"]
        )
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
                "Skill": 36,
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
