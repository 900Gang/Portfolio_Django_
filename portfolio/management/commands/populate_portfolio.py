"""
Django management command to populate the portfolio with real content.

Idempotent: every record is matched on its natural key and updated in place,
so re-running the command refreshes content instead of duplicating it. The
whole run is wrapped in a transaction, so a failure part-way leaves the
database untouched rather than half-populated.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from portfolio.models import (
    Certification,
    Education,
    JourneyEntry,
    Project,
    ProfessionalSkill,
    Skill,
)
from portfolio.models import SkillCategory, SkillStatus


class Command(BaseCommand):
    help = 'Populate portfolio with real content from resume'

    def add_arguments(self, parser):
        parser.add_argument(
            '--prune',
            action='store_true',
            help='Delete skills that are not part of the seed data.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Populating portfolio with real content...')

        created, updated = self._populate_skills(prune=options['prune'])
        self.stdout.write(self.style.SUCCESS(
            f'Skills: {created} created, {updated} updated'
        ))

        created, updated = self._populate_projects()
        self.stdout.write(self.style.SUCCESS(
            f'Projects: {created} created, {updated} updated'
        ))

        created, updated = self._populate_education()
        self.stdout.write(self.style.SUCCESS(
            f'Education: {created} created, {updated} updated'
        ))

        created, updated = self._populate_certifications()
        self.stdout.write(self.style.SUCCESS(
            f'Certifications: {created} created, {updated} updated'
        ))

        created, updated = self._populate_professional_skills()
        self.stdout.write(self.style.SUCCESS(
            f'Professional skills: {created} created, {updated} updated'
        ))

        self.stdout.write(self.style.WARNING(
            'Journey entries not populated - no chronological journey data provided in resume'
        ))

        self.stdout.write(self.style.SUCCESS('\n=== POPULATION COMPLETE ==='))
        self.stdout.write(f'Skills: {Skill.objects.count()}')
        self.stdout.write(f'Projects: {Project.objects.count()}')
        self.stdout.write(f'Education: {Education.objects.count()}')
        self.stdout.write(f'Certifications: {Certification.objects.count()}')
        self.stdout.write(f'Professional Skills: {ProfessionalSkill.objects.count()}')
        self.stdout.write(f'Journey Entries: {JourneyEntry.objects.count()} (intentionally empty)')

    def _populate_skills(self, prune=False):
        skills_data = [
            # Frontend
            ('HTML5', SkillCategory.FRONTEND, SkillStatus.USED_IN_PROJECTS, 1),
            ('CSS3', SkillCategory.FRONTEND, SkillStatus.USED_IN_PROJECTS, 2),
            ('JavaScript', SkillCategory.FRONTEND, SkillStatus.USED_IN_PROJECTS, 3),
            ('React', SkillCategory.FRONTEND, SkillStatus.BUILDING_WITH, 4),

            # Backend
            ('Python', SkillCategory.BACKEND, SkillStatus.USED_IN_PROJECTS, 1),
            ('Django', SkillCategory.BACKEND, SkillStatus.USED_IN_PROJECTS, 2),
            ('REST APIs', SkillCategory.BACKEND, SkillStatus.USED_IN_PROJECTS, 3),
            ('Node.js', SkillCategory.BACKEND, SkillStatus.LEARNING, 4),
            ('Express.js', SkillCategory.BACKEND, SkillStatus.LEARNING, 5),

            # Databases (using BACKEND category as there's no DATABASES category)
            ('MySQL', SkillCategory.BACKEND, SkillStatus.USED_IN_PROJECTS, 6),
            ('Firebase Realtime Database', SkillCategory.BACKEND, SkillStatus.USED_IN_PROJECTS, 7),

            # Tools & Workflow
            ('Git', SkillCategory.TOOLS, SkillStatus.USED_IN_PROJECTS, 1),
            ('GitHub', SkillCategory.TOOLS, SkillStatus.USED_IN_PROJECTS, 2),
            ('Git Workflow', SkillCategory.TOOLS, SkillStatus.USED_IN_PROJECTS, 3),

            # Testing (using TOOLS category)
            ('Manual Testing', SkillCategory.TOOLS, SkillStatus.LEARNING, 4),
            ('SDLC', SkillCategory.TOOLS, SkillStatus.BUILDING_WITH, 5),
            ('STLC', SkillCategory.TOOLS, SkillStatus.BUILDING_WITH, 6),
            ('Test Case Design', SkillCategory.TOOLS, SkillStatus.BUILDING_WITH, 7),
            ('Bug Reporting', SkillCategory.TOOLS, SkillStatus.BUILDING_WITH, 8),
            ('Defect Life Cycle', SkillCategory.TOOLS, SkillStatus.BUILDING_WITH, 9),
            ('Debugging', SkillCategory.TOOLS, SkillStatus.USED_IN_PROJECTS, 10),
            ('Agile', SkillCategory.TOOLS, SkillStatus.BUILDING_WITH, 11),

            # DevOps (using TOOLS category)
            ('Linux', SkillCategory.TOOLS, SkillStatus.BUILDING_WITH, 12),
            ('CI/CD', SkillCategory.TOOLS, SkillStatus.BUILDING_WITH, 13),
            ('Virtual Machines', SkillCategory.TOOLS, SkillStatus.BUILDING_WITH, 14),
            ('Docker', SkillCategory.TOOLS, SkillStatus.LEARNING, 15),
            ('Jenkins', SkillCategory.TOOLS, SkillStatus.LEARNING, 16),
            ('AWS', SkillCategory.TOOLS, SkillStatus.LEARNING, 17),

            # Concepts
            ('Data Structures', SkillCategory.CONCEPTS, SkillStatus.USED_IN_PROJECTS, 1),
            ('OOP', SkillCategory.CONCEPTS, SkillStatus.USED_IN_PROJECTS, 2),
            ('DBMS', SkillCategory.CONCEPTS, SkillStatus.USED_IN_PROJECTS, 3),
            ('Operating Systems', SkillCategory.CONCEPTS, SkillStatus.BUILDING_WITH, 4),
            ('Computer Networks', SkillCategory.CONCEPTS, SkillStatus.BUILDING_WITH, 5),
            ('JSON', SkillCategory.CONCEPTS, SkillStatus.USED_IN_PROJECTS, 6),
            ('AI & Machine Learning', SkillCategory.CONCEPTS, SkillStatus.BUILDING_WITH, 7),
            ('IoT', SkillCategory.CONCEPTS, SkillStatus.USED_IN_PROJECTS, 8),
        ]


        created = updated = 0
        for name, category, status, order in skills_data:
            # (name, category) is the model's unique constraint.
            _, was_created = Skill.objects.update_or_create(
                name=name,
                category=category,
                defaults={'status': status, 'order': order},
            )
            created, updated = (created + 1, updated) if was_created else (created, updated + 1)

        if prune:
            seeded = {(name, category) for name, category, _, _ in skills_data}
            stale = [s.pk for s in Skill.objects.all() if (s.name, s.category) not in seeded]
            if stale:
                Skill.objects.filter(pk__in=stale).delete()
                self.stdout.write(self.style.WARNING(f'Pruned {len(stale)} stale skills'))

        return created, updated

    def _populate_projects(self):
        projects_data = [
            {
                'title': 'Early Identification of Learning Disabilities Using AI and IoT',
                'short_description': 'Major project using ESP32, Firebase, and Python for real-time physiological and behavioral data processing to support AI-based learning disability detection.',
                'description': '''Developed the Python backend for processing real-time physiological and behavioral data.

Integrated ESP32 with MPU6050 and MAX30100 sensors using I2C communication.

Implemented a real-time data pipeline to transmit sensor data to Firebase Realtime Database.

Contributed to preprocessing multimodal sensor data for AI-based learning disability detection.

Collaborated with a four-member team on system integration, debugging, testing, and deployment.''',
                'featured': True,
                'order': 1,
                'technologies': ['Python', 'Firebase Realtime Database'],
            },
            {
                'title': 'AI-Driven Clinical Support for Hematology Screening',
                'short_description': 'Personal project building a CNN-based deep learning model for automated blood smear image classification into four categories: Normal, Anemia, Thalassemia, and Sickle Cell Disease.',
                'description': '''Built a CNN-based deep learning model for automated blood smear image classification.

Performed image preprocessing, normalization, and dataset preparation.

Implemented an automated prediction pipeline using Python.

Classified blood smear images into four categories: Normal, Anemia, Thalassemia, Sickle Cell Disease.

Evaluated model performance through iterative experimentation and testing.''',
                'featured': True,
                'order': 2,
                'technologies': ['Python'],
            },
        ]


        created = updated = 0
        for project_data in projects_data:
            fields = dict(project_data)
            tech_names = fields.pop('technologies')
            title = fields.pop('title')

            project, was_created = Project.objects.update_or_create(
                title=title, defaults=fields,
            )
            created, updated = (created + 1, updated) if was_created else (created, updated + 1)

            technologies = []
            for tech_name in tech_names:
                # Skill names are unique per category, so a bare name can match
                # more than one row; take the first deterministically.
                skill = Skill.objects.filter(name=tech_name).first()
                if skill is None:
                    self.stdout.write(self.style.WARNING(
                        f'Skill "{tech_name}" not found for project "{project.title}"'
                    ))
                    continue
                technologies.append(skill)
            # set() rather than add() so re-runs do not accumulate stale links.
            project.technologies.set(technologies)

        return created, updated

    def _populate_education(self):
        education_data = [
            {
                'institution': 'College of Engineering, Muttathara',
                'degree': 'Bachelor of Technology (B.Tech) in Computer Science Engineering',
                'field_of_study': 'Computer Science Engineering',
                'start_date': '2022-08-01',
                'end_date': '2026-05-31',
                'is_current': False,
                'description': 'CGPA: 6.84\n\nRelevant Coursework: Data Structures, DBMS, Operating Systems, Computer Networks, Software Testing, Data Mining',
                'order': 1,
            },
            {
                'institution': 'Sree Narayana Guru Higher Secondary School',
                'degree': 'Higher Secondary Education (Class XII)',
                'field_of_study': 'Science',
                'start_date': '2018-06-01',
                'end_date': '2020-03-31',
                'is_current': False,
                'description': 'CGPA: 8.8',
                'order': 2,
            },
            {
                'institution': 'Sree Narayana Public School',
                'degree': 'Secondary Education (Class X)',
                'field_of_study': 'General',
                'start_date': '2017-06-01',
                'end_date': '2018-03-31',
                'is_current': False,
                'description': 'CGPA: 8.2',
                'order': 3,
            },
        ]


        created = updated = 0
        for edu_data in education_data:
            fields = dict(edu_data)
            institution = fields.pop('institution')
            degree = fields.pop('degree')
            _, was_created = Education.objects.update_or_create(
                institution=institution, degree=degree, defaults=fields,
            )
            created, updated = (created + 1, updated) if was_created else (created, updated + 1)
        return created, updated

    def _populate_certifications(self):
        certifications_data = [
            {
                'name': 'Python for Data Science',
                'issuer': 'NPTEL',
                'issue_year': None,
                'credential_url': '',
                'display_order': 1,
            },
            {
                'name': 'Python Bootcamp',
                'issuer': 'Udemy',
                'issue_year': None,
                'credential_url': '',
                'display_order': 2,
            },
            {
                'name': 'Basic to Advanced SQL',
                'issuer': 'Skill Nation',
                'issue_year': None,
                'credential_url': '',
                'display_order': 3,
            },
        ]


        created = updated = 0
        for cert_data in certifications_data:
            fields = dict(cert_data)
            name = fields.pop('name')
            issuer = fields.pop('issuer')
            _, was_created = Certification.objects.update_or_create(
                name=name, issuer=issuer, defaults=fields,
            )
            created, updated = (created + 1, updated) if was_created else (created, updated + 1)
        return created, updated

    def _populate_professional_skills(self):
        professional_skills_data = [
            ('Problem Solving', 1),
            ('Communication', 2),
            ('Team Collaboration', 3),
            ('Adaptability', 4),
            ('Quick Learning', 5),
            ('Critical Thinking', 6),
            ('Time Management', 7),
        ]


        created = updated = 0
        for name, order in professional_skills_data:
            _, was_created = ProfessionalSkill.objects.update_or_create(
                name=name, defaults={'display_order': order},
            )
            created, updated = (created + 1, updated) if was_created else (created, updated + 1)
        return created, updated
