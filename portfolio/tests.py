from datetime import date

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.text import slugify

from .models import Skill, Project, JourneyEntry, Education, ContactMessage
from .models import SkillCategory, SkillStatus, JourneyEntryType


class SkillModelTest(TestCase):
    def test_create_skill(self):
        skill = Skill.objects.create(
            name="Python",
            category=SkillCategory.BACKEND,
            status=SkillStatus.USED_IN_PROJECTS,
            order=1,
        )
        self.assertEqual(skill.name, "Python")
        self.assertEqual(skill.category, SkillCategory.BACKEND)
        self.assertEqual(skill.status, SkillStatus.USED_IN_PROJECTS)
        self.assertEqual(skill.order, 1)

    def test_skill_str(self):
        skill = Skill.objects.create(name="Django", category=SkillCategory.BACKEND)
        self.assertEqual(str(skill), "Django (Backend)")

    def test_skill_unique_constraint(self):
        Skill.objects.create(name="Python", category=SkillCategory.BACKEND)
        with self.assertRaises(Exception):
            Skill.objects.create(name="Python", category=SkillCategory.BACKEND)

    def test_skill_ordering(self):
        Skill.objects.create(name="Zebra", category=SkillCategory.FRONTEND, order=2)
        Skill.objects.create(name="Alpha", category=SkillCategory.FRONTEND, order=1)
        skills = list(Skill.objects.all())
        self.assertEqual(skills[0].name, "Alpha")
        self.assertEqual(skills[1].name, "Zebra")


class ProjectModelTest(TestCase):
    def setUp(self):
        self.python = Skill.objects.create(
            name="Python", category=SkillCategory.BACKEND
        )
        self.django = Skill.objects.create(
            name="Django", category=SkillCategory.BACKEND
        )

    def test_create_project(self):
        project = Project.objects.create(
            title="Test Project",
            short_description="A test project",
            description="Full description here",
            github_url="https://github.com/test/project",
        )
        self.assertEqual(project.title, "Test Project")
        self.assertTrue(project.slug)
        self.assertEqual(project.slug, "test-project")

    def test_project_str(self):
        project = Project.objects.create(
            title="My Project", short_description="Desc"
        )
        self.assertEqual(str(project), "My Project")

    def test_project_slug_unique(self):
        Project.objects.create(title="Same Title", short_description="Desc 1")
        project2 = Project.objects.create(title="Same Title", short_description="Desc 2")
        self.assertNotEqual(project2.slug, "same-title")
        self.assertTrue(project2.slug.startswith("same-title-"))

    def test_project_technologies_many_to_many(self):
        project = Project.objects.create(
            title="Tech Project", short_description="Desc"
        )
        project.technologies.add(self.python, self.django)
        self.assertEqual(project.technologies.count(), 2)
        self.assertIn(self.python, project.technologies.all())
        self.assertIn(self.django, project.technologies.all())
        self.assertIn(project, self.python.projects.all())

    def test_project_ordering_featured_first(self):
        Project.objects.create(
            title="Regular Project", short_description="Desc", featured=False, order=1
        )
        featured = Project.objects.create(
            title="Featured Project", short_description="Desc", featured=True, order=2
        )
        projects = list(Project.objects.all())
        self.assertEqual(projects[0], featured)

    def test_project_image_upload_path(self):
        project = Project.objects.create(
            title="Image Project", short_description="Desc"
        )
        self.assertTrue(project.image.field.upload_to == "projects/")

    def test_project_blank_urls_allowed(self):
        project = Project.objects.create(
            title="No URLs", short_description="Desc"
        )
        self.assertEqual(project.github_url, "")
        self.assertEqual(project.live_demo_url, "")


class JourneyEntryModelTest(TestCase):
    def test_create_journey_entry(self):
        entry = JourneyEntry.objects.create(
            date="2025-06-15",
            title="Started learning Django",
            description="Began building web applications with Django",
            entry_type=JourneyEntryType.LEARNING,
        )
        self.assertEqual(entry.title, "Started learning Django")
        self.assertEqual(entry.entry_type, JourneyEntryType.LEARNING)

    def test_journey_entry_str(self):
        entry = JourneyEntry.objects.create(
            date=date(2025, 1, 1),
            title="New Year Goal",
            description="Learn web development",
        )
        expected = f"{entry.date.year} — {entry.title}"
        self.assertEqual(str(entry), expected)

    def test_journey_entry_ordering(self):
        JourneyEntry.objects.create(
            date="2025-01-01", title="Later", description="Desc"
        )
        JourneyEntry.objects.create(
            date="2024-01-01", title="Earlier", description="Desc"
        )
        entries = list(JourneyEntry.objects.all())
        self.assertEqual(entries[0].title, "Later")
        self.assertEqual(entries[1].title, "Earlier")


class EducationModelTest(TestCase):
    def test_create_education(self):
        edu = Education.objects.create(
            institution="Test University",
            degree="B.Tech",
            field_of_study="Computer Science",
            start_date="2022-08-01",
            end_date="2026-05-31",
        )
        self.assertEqual(edu.institution, "Test University")
        self.assertFalse(edu.is_current)

    def test_education_str(self):
        edu = Education.objects.create(
            institution="College",
            degree="B.Tech",
            start_date="2022-08-01",
            end_date="2026-05-31",
        )
        self.assertEqual(str(edu), "B.Tech — College")

    def test_current_education_no_end_date(self):
        edu = Education.objects.create(
            institution="Current College",
            degree="M.Tech",
            start_date="2026-08-01",
            is_current=True,
        )
        self.assertTrue(edu.is_current)
        self.assertIsNone(edu.end_date)

    def test_past_education_requires_end_date(self):
        edu = Education(
            institution="Past College",
            degree="B.Sc",
            start_date="2020-08-01",
            is_current=False,
        )
        with self.assertRaises(ValidationError):
            edu.full_clean()

    def test_current_education_rejects_end_date(self):
        edu = Education(
            institution="Current College",
            degree="M.Tech",
            start_date="2026-08-01",
            end_date="2027-05-31",
            is_current=True,
        )
        with self.assertRaises(ValidationError):
            edu.full_clean()


class ContactMessageModelTest(TestCase):
    def test_create_contact_message(self):
        msg = ContactMessage.objects.create(
            name="John Doe",
            email="john@example.com",
            subject="Inquiry",
            message="Hello, I'd like to connect.",
        )
        self.assertEqual(msg.name, "John Doe")
        self.assertEqual(msg.email, "john@example.com")
        self.assertFalse(msg.is_read)
        self.assertIsNotNone(msg.created_at)

    def test_contact_message_str(self):
        msg = ContactMessage.objects.create(
            name="Jane",
            email="jane@example.com",
            subject="Question",
            message="Hi",
        )
        expected = f"Jane — Question ({msg.created_at.strftime('%Y-%m-%d')})"
        self.assertEqual(str(msg), expected)

    def test_contact_message_ordering(self):
        msg1 = ContactMessage.objects.create(
            name="First", email="a@b.com", subject="Sub", message="Msg"
        )
        msg2 = ContactMessage.objects.create(
            name="Second", email="c@d.com", subject="Sub", message="Msg"
        )
        messages = list(ContactMessage.objects.all())
        self.assertEqual(messages[0], msg2)
        self.assertEqual(messages[1], msg1)

    def test_contact_message_email_validation(self):
        msg = ContactMessage(
            name="Test", email="not-an-email", subject="Sub", message="Msg"
        )
        with self.assertRaises(ValidationError):
            msg.full_clean()


class HomePageViewTest(TestCase):
    def setUp(self):
        self.skill = Skill.objects.create(
            name="Python", category=SkillCategory.BACKEND
        )
        self.skill2 = Skill.objects.create(
            name="Django", category=SkillCategory.BACKEND
        )
        self.featured_project = Project.objects.create(
            title="Featured Project",
            short_description="A featured project desc",
            description="Full description of featured project",
            featured=True,
        )
        self.featured_project.technologies.add(self.skill, self.skill2)
        self.regular_project = Project.objects.create(
            title="Regular Project",
            short_description="A regular project desc",
            featured=False,
        )
        self.journey = JourneyEntry.objects.create(
            date=date(2025, 1, 1), title="Started learning", description="Description"
        )
        self.education = Education.objects.create(
            institution="University",
            degree="B.Tech",
            field_of_study="Computer Science",
            start_date=date(2022, 8, 1),
            end_date=date(2026, 5, 31),
        )

    def test_homepage_returns_200(self):
        response = self.client.get(reverse("portfolio:home"))
        self.assertEqual(response.status_code, 200)

    def test_homepage_uses_correct_template(self):
        response = self.client.get(reverse("portfolio:home"))
        self.assertTemplateUsed(response, "portfolio/home.html")

    def test_homepage_context_featured_projects(self):
        response = self.client.get(reverse("portfolio:home"))
        self.assertEqual(list(response.context["featured_projects"]), [self.featured_project])

    
    def test_homepage_empty_database_returns_200(self):
        # Remove all records to simulate an empty database
        Skill.objects.all().delete()
        Project.objects.all().delete()
        JourneyEntry.objects.all().delete()
        Education.objects.all().delete()
        response = self.client.get(reverse("portfolio:home"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["featured_projects"]), 0)
        self.assertEqual(len(response.context["skills"]), 0)
        self.assertEqual(len(response.context["journey_entries"]), 0)
        self.assertEqual(len(response.context["education"]), 0)
        # Check that About section content is still present even with empty DB
        self.assertContains(response, "About Me")
        self.assertContains(response, "Computer Science Engineering student")

    def test_homepage_about_section_present(self):
        response = self.client.get(reverse("portfolio:home"))
        self.assertContains(response, "About Me")
        self.assertContains(response, "Computer Science Engineering student")
        self.assertContains(response, "Web Development")
        self.assertContains(response, "Backend Development")
        self.assertContains(response, "Database Applications")

    def test_homepage_skills_section_present(self):
        response = self.client.get(reverse("portfolio:home"))
        self.assertContains(response, "Technical Skills")
        # Check that skills are grouped by category
        self.assertContains(response, "Backend")
        # Check that skill names appear
        self.assertContains(response, "Python")
        self.assertContains(response, "Django")

    def test_homepage_skills_show_status_badges(self):
        response = self.client.get(reverse("portfolio:home"))
        # Check for status badges (based on test setup skills)
        self.assertContains(response, "Learning")

    def test_homepage_projects_section_displays_featured_project(self):
        response = self.client.get(reverse("portfolio:home"))
        detail_url = reverse(
            "portfolio:project_detail", kwargs={"slug": self.featured_project.slug}
        )

        self.assertContains(response, 'id="projects"')
        self.assertContains(response, "Featured Projects")
        self.assertContains(response, self.featured_project.title)
        self.assertContains(response, self.skill.name)
        self.assertContains(response, detail_url)
        self.assertNotContains(response, self.regular_project.title)

    def test_homepage_projects_empty_state_renders_without_projects(self):
        Project.objects.all().delete()

        response = self.client.get(reverse("portfolio:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="projects"')
        self.assertContains(response, "No featured projects yet. Check back soon!")


class ProjectDetailViewTest(TestCase):
    def setUp(self):
        self.python = Skill.objects.create(
            name="Python", category=SkillCategory.BACKEND
        )
        self.django = Skill.objects.create(
            name="Django", category=SkillCategory.BACKEND
        )
        self.project = Project.objects.create(
            title="Detail Project",
            short_description="A project to view in detail",
            description="Full description here",
            github_url="https://github.com/example/detail-project",
            live_demo_url="https://example.com/detail-project",
            featured=True,
        )
        self.project.technologies.add(self.python, self.django)

    def test_valid_slug_returns_200(self):
        response = self.client.get(
            reverse("portfolio:project_detail", kwargs={"slug": self.project.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_correct_project_displayed(self):
        response = self.client.get(
            reverse("portfolio:project_detail", kwargs={"slug": self.project.slug})
        )
        self.assertEqual(response.context["project"], self.project)
        self.assertContains(response, self.project.title)

    def test_invalid_slug_returns_404(self):
        response = self.client.get(
            reverse("portfolio:project_detail", kwargs={"slug": "non-existent-slug"})
        )
        self.assertEqual(response.status_code, 404)

    def test_project_technologies_available(self):
        response = self.client.get(
            reverse("portfolio:project_detail", kwargs={"slug": self.project.slug})
        )
        # Technologies are ordered by the Skill model's default ordering: category, order, name
        expected_technologies = sorted([self.python, self.django], key=lambda s: (s.category, s.order, s.name))
        self.assertEqual(list(response.context["technologies"]), expected_technologies)
        self.assertContains(response, self.python.name)
        self.assertContains(response, self.django.name)

    def test_project_detail_displays_summary_description_and_links(self):
        response = self.client.get(
            reverse("portfolio:project_detail", kwargs={"slug": self.project.slug})
        )

        self.assertContains(response, self.project.title)
        self.assertContains(response, self.project.short_description)
        self.assertContains(response, self.project.description)
        self.assertContains(response, self.project.github_url)
        self.assertContains(response, self.project.live_demo_url)
        self.assertContains(response, 'rel="noopener noreferrer"')
        self.assertContains(
            response, f'{reverse("portfolio:home")}#projects'
        )

    def test_project_detail_does_not_render_blank_external_links(self):
        project = Project.objects.create(
            title="No Link Project",
            short_description="A project without external links",
            description="",
        )

        response = self.client.get(
            reverse("portfolio:project_detail", kwargs={"slug": project.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Project links")
        self.assertNotContains(response, 'class="project-detail-actions"')
        self.assertNotContains(response, "Project details")