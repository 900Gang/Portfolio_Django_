"""
Django management command to populate the portfolio with real content.

Idempotent: every record is matched on its natural key and updated in place,
so re-running the command refreshes content instead of duplicating it. The
whole run is wrapped in a transaction, so a failure part-way leaves the
database untouched rather than half-populated.
"""
from pathlib import Path

from django.conf import settings
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
from portfolio.models import JourneyEntryType, SkillCategory, SkillStatus


class Command(BaseCommand):
    help = 'Populate portfolio with real content from resume'

    def add_arguments(self, parser):
        parser.add_argument(
            '--prune',
            action='store_true',
            help='Delete skills and professional skills not in the seed data.',
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

        created, updated = self._populate_education(prune=options['prune'])
        self.stdout.write(self.style.SUCCESS(
            f'Education: {created} created, {updated} updated'
        ))

        created, updated = self._populate_certifications(prune=options['prune'])
        self.stdout.write(self.style.SUCCESS(
            f'Certifications: {created} created, {updated} updated'
        ))

        created, updated = self._populate_professional_skills(prune=options['prune'])
        self.stdout.write(self.style.SUCCESS(
            f'Professional skills: {created} created, {updated} updated'
        ))

        created, updated = self._populate_journey()
        self.stdout.write(self.style.SUCCESS(
            f'Journey entries: {created} created, {updated} updated'
        ))

        self.stdout.write(self.style.SUCCESS('\n=== POPULATION COMPLETE ==='))
        self.stdout.write(f'Skills: {Skill.objects.count()}')
        self.stdout.write(f'Projects: {Project.objects.count()}')
        self.stdout.write(f'Education: {Education.objects.count()}')
        self.stdout.write(f'Certifications: {Certification.objects.count()}')
        self.stdout.write(f'Professional Skills: {ProfessionalSkill.objects.count()}')
        self.stdout.write(f'Journey Entries: {JourneyEntry.objects.count()}')

    def _populate_skills(self, prune=False):
        # Sourced from the résumé's Technical Skills list and the LinkedIn
        # profile's Skills section. LinkedIn's list is long and partly
        # endorsement padding (Football, Malayalam, "GitHub Atom"); only
        # entries with real backing in the projects or the résumé are carried
        # over, and each keeps an honest status rather than being levelled up.
        skills_data = [
            # Backend & Data — leads the section; holds the AI stack.
            ('Python', SkillCategory.BACKEND, SkillStatus.USED_IN_PROJECTS, 1),
            ('Machine Learning', SkillCategory.BACKEND, SkillStatus.USED_IN_PROJECTS, 2),
            ('Deep Learning', SkillCategory.BACKEND, SkillStatus.USED_IN_PROJECTS, 3),
            ('TensorFlow', SkillCategory.BACKEND, SkillStatus.USED_IN_PROJECTS, 4),
            ('Keras', SkillCategory.BACKEND, SkillStatus.USED_IN_PROJECTS, 5),
            ('OpenCV', SkillCategory.BACKEND, SkillStatus.USED_IN_PROJECTS, 6),
            ('Pandas', SkillCategory.BACKEND, SkillStatus.USED_IN_PROJECTS, 7),
            ('Django', SkillCategory.BACKEND, SkillStatus.USED_IN_PROJECTS, 8),
            ('Django REST Framework', SkillCategory.BACKEND, SkillStatus.BUILDING_WITH, 9),
            ('REST APIs', SkillCategory.BACKEND, SkillStatus.USED_IN_PROJECTS, 10),
            ('SQL', SkillCategory.BACKEND, SkillStatus.USED_IN_PROJECTS, 11),
            ('MySQL', SkillCategory.BACKEND, SkillStatus.USED_IN_PROJECTS, 12),
            ('PostgreSQL', SkillCategory.BACKEND, SkillStatus.LEARNING, 13),
            ('Firebase Realtime Database', SkillCategory.BACKEND, SkillStatus.USED_IN_PROJECTS, 14),
            ('Java', SkillCategory.BACKEND, SkillStatus.BUILDING_WITH, 15),
            ('C', SkillCategory.BACKEND, SkillStatus.BUILDING_WITH, 16),
            ('Flask', SkillCategory.BACKEND, SkillStatus.LEARNING, 17),
            ('FastAPI', SkillCategory.BACKEND, SkillStatus.LEARNING, 18),
            ('Node.js', SkillCategory.BACKEND, SkillStatus.LEARNING, 19),
            ('Express.js', SkillCategory.BACKEND, SkillStatus.LEARNING, 20),

            # DevOps & Cloud
            ('Linux', SkillCategory.DEVOPS, SkillStatus.BUILDING_WITH, 1),
            ('CI/CD', SkillCategory.DEVOPS, SkillStatus.BUILDING_WITH, 2),
            ('Virtual Machines', SkillCategory.DEVOPS, SkillStatus.BUILDING_WITH, 3),
            ('Docker', SkillCategory.DEVOPS, SkillStatus.LEARNING, 4),
            ('Jenkins', SkillCategory.DEVOPS, SkillStatus.LEARNING, 5),
            ('AWS', SkillCategory.DEVOPS, SkillStatus.LEARNING, 6),

            # Web & Frontend
            ('HTML', SkillCategory.FRONTEND, SkillStatus.USED_IN_PROJECTS, 1),
            ('CSS', SkillCategory.FRONTEND, SkillStatus.USED_IN_PROJECTS, 2),
            ('JavaScript', SkillCategory.FRONTEND, SkillStatus.USED_IN_PROJECTS, 3),
            ('Bootstrap', SkillCategory.FRONTEND, SkillStatus.BUILDING_WITH, 4),
            ('jQuery', SkillCategory.FRONTEND, SkillStatus.BUILDING_WITH, 5),
            ('React', SkillCategory.FRONTEND, SkillStatus.BUILDING_WITH, 6),
            ('Flutter', SkillCategory.FRONTEND, SkillStatus.BUILDING_WITH, 7),

            # Testing & Process
            ('SDLC', SkillCategory.TESTING, SkillStatus.BUILDING_WITH, 1),
            ('STLC', SkillCategory.TESTING, SkillStatus.BUILDING_WITH, 2),
            ('Test Case Design', SkillCategory.TESTING, SkillStatus.BUILDING_WITH, 3),
            ('Bug Reporting', SkillCategory.TESTING, SkillStatus.BUILDING_WITH, 4),
            ('Defect Life Cycle', SkillCategory.TESTING, SkillStatus.BUILDING_WITH, 5),
            ('Agile', SkillCategory.TESTING, SkillStatus.BUILDING_WITH, 6),
            ('Manual Testing', SkillCategory.TESTING, SkillStatus.LEARNING, 7),

            # Tools & Workflow
            ('Git', SkillCategory.TOOLS, SkillStatus.USED_IN_PROJECTS, 1),
            ('GitHub', SkillCategory.TOOLS, SkillStatus.USED_IN_PROJECTS, 2),
            ('ESP32', SkillCategory.TOOLS, SkillStatus.USED_IN_PROJECTS, 3),
            ('Power BI', SkillCategory.TOOLS, SkillStatus.BUILDING_WITH, 4),
            ('Tableau', SkillCategory.TOOLS, SkillStatus.BUILDING_WITH, 5),
            ('Excel', SkillCategory.TOOLS, SkillStatus.BUILDING_WITH, 6),

            # Core Concepts
            ('Data Structures', SkillCategory.CONCEPTS, SkillStatus.USED_IN_PROJECTS, 1),
            ('OOP', SkillCategory.CONCEPTS, SkillStatus.USED_IN_PROJECTS, 2),
            ('DBMS', SkillCategory.CONCEPTS, SkillStatus.USED_IN_PROJECTS, 3),
            ('JSON', SkillCategory.CONCEPTS, SkillStatus.USED_IN_PROJECTS, 4),
            ('Operating Systems', SkillCategory.CONCEPTS, SkillStatus.BUILDING_WITH, 5),
            ('Computer Networks', SkillCategory.CONCEPTS, SkillStatus.BUILDING_WITH, 6),
            ('IoT', SkillCategory.CONCEPTS, SkillStatus.USED_IN_PROJECTS, 7),
            ('Embedded Systems', SkillCategory.CONCEPTS, SkillStatus.USED_IN_PROJECTS, 8),
            ('Prompt Engineering', SkillCategory.CONCEPTS, SkillStatus.BUILDING_WITH, 9),
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
        # Bullets are the résumé's own, so the site and the CV a recruiter is
        # reading alongside it cannot tell different stories.
        projects_data = [
            {
                'title': 'Early Identification of Learning Disabilities Using AI and IoT',
                'short_description': (
                    'Major project pairing ESP32 sensor hardware with a Python backend and '
                    'Firebase, streaming real-time physiological and behavioural data for '
                    'AI-based learning disability detection.'
                ),
                'description': """Developed the Python backend for processing real-time physiological and behavioral sensor data.

Integrated ESP32 with MPU6050 and MAX30100 sensors using I2C communication.

Built a real-time data pipeline to transmit sensor data to Firebase Realtime Database.

Worked with Git and GitHub for source-code management and collaborative development.

Collaborated with a four-member team on system integration, debugging, testing, and deployment.""",
                'featured': True,
                'order': 1,
                'image': 'projects/learning-disabilities-ai-iot.webp',
                'technologies': [
                    'Python', 'ESP32', 'Firebase Realtime Database', 'Git', 'IoT', 'REST APIs',
                ],
            },
            {
                'title': 'AI-Driven Clinical Support for Hematology Screening',
                'short_description': (
                    'Personal project: a Python machine-learning application that classifies '
                    'blood smear images automatically, from dataset preparation through to an '
                    'end-to-end prediction pipeline.'
                ),
                'description': """Developed a Python-based machine learning application for automated blood smear classification.

Prepared and processed image datasets for model training and evaluation.

Implemented a Python prediction pipeline for automated disease classification.

Used Git and GitHub for source-code management and project collaboration.

Tested and evaluated the application through iterative experimentation.""",
                'featured': True,
                'order': 2,
                'image': 'projects/hematology-screening.webp',
                'technologies': [
                    'Python', 'TensorFlow', 'Keras', 'OpenCV', 'Git',
                ],
            },
        ]


        created = updated = 0
        for project_data in projects_data:
            fields = dict(project_data)
            tech_names = fields.pop('technologies')
            title = fields.pop('title')

            # The screenshot is attached only when the file is really in
            # MEDIA_ROOT. A fresh deploy seeds an empty database, so without
            # this the cards fall back to the placeholder even though the
            # images are committed; and pointing the column at a missing file
            # would be worse than leaving it blank.
            image = fields.pop('image', '')
            if image and (Path(settings.MEDIA_ROOT) / image).is_file():
                fields['image'] = image
            elif image:
                self.stdout.write(self.style.WARNING(
                    f'Image "{image}" not found in MEDIA_ROOT for "{title}"'
                ))

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

    def _populate_journey(self):
        """
        The chronology, which the r\u00e9sum\u00e9 alone did not carry \u2014 the dates come
        from the LinkedIn profile's Experience, Education and Projects
        sections. Entries are dated at the point they *completed*, which is
        what the timeline reads as; `order` separates the two that share a
        month.
        """
        journey_data = [
            {
                'date': '2026-09-01',
                'title': 'Artificial Intelligence Intern at Yangtso Four Labs',
                'description': (
                    'Joined Yangtso Four Labs in Bengaluru as an Artificial Intelligence '
                    'Intern, moving from academic AI work into production workflows.'
                ),
                'entry_type': JourneyEntryType.EXPERIENCE,
                'order': 1,
            },
            {
                'date': '2026-05-31',
                'title': 'Graduated B.Tech in Computer Science Engineering',
                'description': (
                    'Completed the B.Tech at College of Engineering Muttathara with a '
                    'CGPA of 6.82/10.0 and no backlogs.'
                ),
                'entry_type': JourneyEntryType.MILESTONE,
                'order': 1,
            },
            {
                'date': '2026-05-31',
                'title': 'Completed the learning-disabilities AI and IoT system',
                'description': (
                    'Five months building the major project with a four-person team: '
                    'ESP32 sensor hardware, a Python backend and a real-time Firebase '
                    'pipeline feeding AI-based detection.'
                ),
                'entry_type': JourneyEntryType.PROJECT,
                'order': 2,
            },
            {
                'date': '2026-03-31',
                'title': 'Built AI-driven hematology screening',
                'description': (
                    'Personal project: a TensorFlow, Keras and OpenCV pipeline that '
                    'classifies blood smear images, from dataset preparation through to '
                    'automated prediction.'
                ),
                'entry_type': JourneyEntryType.PROJECT,
                'order': 1,
            },
            {
                'date': '2022-09-01',
                'title': 'Started B.Tech at College of Engineering Muttathara',
                'description': (
                    'Began the Computer Science Engineering degree, building the '
                    'foundation in data structures, DBMS, operating systems and networks.'
                ),
                'entry_type': JourneyEntryType.MILESTONE,
                'order': 1,
            },
        ]

        created = updated = 0
        for entry_data in journey_data:
            fields = dict(entry_data)
            title = fields.pop('title')
            _, was_created = JourneyEntry.objects.update_or_create(
                title=title, defaults=fields,
            )
            created, updated = (created + 1, updated) if was_created else (created, updated + 1)
        return created, updated

    def _populate_education(self, prune=False):
        education_data = [
            {
                'institution': 'College of Engineering, Muttathara',
                'degree': 'Bachelor of Technology (B.Tech) in Computer Science Engineering',
                'field_of_study': 'Computer Science Engineering',
                'start_date': '2022-09-01',
                'end_date': '2026-05-31',
                'is_current': False,
                'description': 'CGPA: 6.82/10.0 — no current backlogs.\n\nRelevant Coursework: Data Structures, DBMS, Operating Systems, Computer Networks, Software Testing, Data Mining',
                'order': 1,
            },
            {
                'institution': 'SNGHSS Chempazhanthy',
                'degree': 'Higher Secondary Education (Class XII)',
                'field_of_study': 'Science',
                'start_date': '2018-06-01',
                'end_date': '2020-05-31',
                'is_current': False,
                'description': 'Percentage: 88%',
                'order': 2,
            },
            {
                'institution': 'Sree Narayana Public School',
                'degree': 'Secondary Education (Class X)',
                'field_of_study': 'CBSE',
                'start_date': '2017-06-01',
                'end_date': '2018-04-30',
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

        if prune:
            # Matched on (institution, degree), so renaming a school — as
            # LinkedIn's "SNGHSS Chempazhanthy" does — adds a row rather than
            # renaming one, leaving the same schooling listed twice.
            seeded = {(e['institution'], e['degree']) for e in education_data}
            stale = [e.pk for e in Education.objects.all()
                     if (e.institution, e.degree) not in seeded]
            if stale:
                Education.objects.filter(pk__in=stale).delete()
                self.stdout.write(self.style.WARNING(
                    f'Pruned {len(stale)} stale education records'
                ))

        return created, updated

    def _populate_certifications(self, prune=False):
        # The seven certifications listed on LinkedIn, plus the NPTEL course
        # the résumé carries. Ordered strongest-first for an AI/Python role
        # rather than in LinkedIn's own (reverse-chronological) order.
        certifications_data = [
            {
                'name': 'The Complete Python Bootcamp From Zero to Hero in Python',
                'issuer': 'Udemy',
                'issue_year': None,
                'credential_url': '',
                'display_order': 1,
            },
            {
                'name': 'Python and Django Full Stack Web Developer Bootcamp',
                'issuer': 'Udemy',
                'issue_year': None,
                'credential_url': '',
                'display_order': 2,
            },
            {
                'name': 'Python for Data Science',
                'issuer': 'NPTEL',
                'issue_year': None,
                'credential_url': '',
                'display_order': 3,
            },
            {
                'name': 'Basic to Advanced SQL',
                'issuer': 'LinkedIn',
                'issue_year': None,
                'credential_url': '',
                'display_order': 4,
            },
            {
                'name': 'Basic to Advanced Power BI Certificate',
                'issuer': 'LinkedIn',
                'issue_year': None,
                'credential_url': '',
                'display_order': 5,
            },
            {
                'name': 'Basic to Advanced Tableau Dashboard',
                'issuer': 'LinkedIn',
                'issue_year': None,
                'credential_url': '',
                'display_order': 6,
            },
            {
                'name': 'Basic to Advanced Microsoft Excel',
                'issuer': 'LinkedIn',
                'issue_year': None,
                'credential_url': '',
                'display_order': 7,
            },
            {
                'name': 'Basic to Advanced PowerPoint',
                'issuer': 'LinkedIn',
                'issue_year': None,
                'credential_url': '',
                'display_order': 8,
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

        if prune:
            # Certifications are matched on (name, issuer), so correcting
            # either — "Python Bootcamp" to its full Udemy title, or the SQL
            # course's issuer — inserts a new row and strands the old one.
            seeded = {(c['name'], c['issuer']) for c in certifications_data}
            stale = [c.pk for c in Certification.objects.all()
                     if (c.name, c.issuer) not in seeded]
            if stale:
                Certification.objects.filter(pk__in=stale).delete()
                self.stdout.write(self.style.WARNING(
                    f'Pruned {len(stale)} stale certifications'
                ))

        return created, updated

    def _populate_professional_skills(self, prune=False):
        professional_skills_data = [
            ('Problem Solving', 1),
            ('Communication', 2),
            ('Team Collaboration', 3),
            ('Quick Learner', 4),
            ('Adaptability', 5),
            ('Time Management', 6),
            ('Critical Thinking', 7),
            ('Leadership', 8),
        ]


        created = updated = 0
        for name, order in professional_skills_data:
            _, was_created = ProfessionalSkill.objects.update_or_create(
                name=name, defaults={'display_order': order},
            )
            created, updated = (created + 1, updated) if was_created else (created, updated + 1)

        if prune:
            # Without this, renaming an entry (e.g. "Quick Learning" ->
            # "Quick Learner") leaves both versions on the page.
            seeded = {name for name, _ in professional_skills_data}
            stale = ProfessionalSkill.objects.exclude(name__in=seeded)
            count = stale.count()
            if count:
                stale.delete()
                self.stdout.write(self.style.WARNING(
                    f'Pruned {count} stale professional skills'
                ))

        return created, updated
