import importlib
from types import SimpleNamespace

from django.apps import apps
from django.test import TestCase

from .models import Certification, Education, JourneyEntry


class ContentMigrationTest(TestCase):
    def test_corrects_existing_seeded_content_without_touching_unrelated_records(self):
        education = Education.objects.create(
            institution="College of Engineering, Muttathara",
            degree="B.Tech",
            start_date="2022-09-01",
            end_date="2026-05-31",
            description="CGPA: 6.82/10.0 — no current backlogs.\n\nCoursework",
        )
        school = Education.objects.create(
            institution="Sree Narayana Public School",
            degree="Class X",
            start_date="2017-06-01",
            end_date="2018-04-30",
            description="CGPA: 8.2",
        )
        journey = JourneyEntry.objects.create(
            date="2026-05-31",
            title="Graduated B.Tech in Computer Science Engineering",
            description="Completed with a CGPA of 6.82/10.0 and no backlogs.",
        )
        cert = Certification.objects.create(name="Basic to Advanced SQL", issuer="LinkedIn")
        unrelated = Certification.objects.create(name="Other", issuer="LinkedIn")
        migration = importlib.import_module("portfolio.migrations.0005_correct_portfolio_details")
        migration.correct_details(apps, SimpleNamespace(connection=SimpleNamespace(alias="default")))
        for item in (education, school, journey, cert, unrelated):
            item.refresh_from_db()
        self.assertIn("CGPA: 6.84/10.0", education.description)
        self.assertIn("Coursework", education.description)
        self.assertEqual(school.description, "Percentage: 82%")
        self.assertIn("CGPA of 6.84/10.0", journey.description)
        self.assertEqual(cert.issuer, "SkillNation")
        self.assertEqual(unrelated.issuer, "LinkedIn")

    def test_does_not_duplicate_an_already_corrected_certification(self):
        Certification.objects.create(name="Basic to Advanced SQL", issuer="SkillNation")
        old = Certification.objects.create(name="Basic to Advanced SQL", issuer="LinkedIn")
        migration = importlib.import_module("portfolio.migrations.0005_correct_portfolio_details")
        migration.correct_details(apps, SimpleNamespace(connection=SimpleNamespace(alias="default")))
        old.refresh_from_db()
        self.assertEqual(old.issuer, "LinkedIn")
