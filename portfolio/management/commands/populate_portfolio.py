"""
Django management command to populate portfolio with real content.
Removes test data and populates real skills, projects, education, certifications, and professional skills.
"""
from django.core.management.base import BaseCommand
from portfolio.models import Skill, Project, JourneyEntry, Education, Certification, ProfessionalSkill
from portfolio.models import SkillCategory, SkillStatus


class Command(BaseCommand):
    help = 'Populate portfolio with real content from resume'

    def handle(self, *args, **options):
        self.stdout.write('Populating portfolio with real content...')

        # Step 1: Clear test data
        self.stdout.write('Removing test skill data...')
        Skill.objects.all().delete()

        # Step 2: Populate Skills
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

        for name, category, status, order in skills_data:
            Skill.objects.create(
                name=name,
                category=category,
                status=status,
                order=order
            )

        self.stdout.write(self.style.SUCCESS(f'Created {len(skills_data)} skills'))

        # Step 3: Populate Projects
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

        for project_data in projects_data:
            tech_names = project_data.pop('technologies')
            project = Project.objects.create(**project_data)

            # Add technologies
            for tech_name in tech_names:
                try:
                    skill = Skill.objects.get(name=tech_name)
                    project.technologies.add(skill)
                except Skill.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Skill "{tech_name}" not found for project "{project.title}"'))

            self.stdout.write(self.style.SUCCESS(f'Created project: {project.title}'))

        # Step 4: Populate Education
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

        for edu_data in education_data:
            Education.objects.create(**edu_data)

        self.stdout.write(self.style.SUCCESS(f'Created {len(education_data)} education records'))

        # Step 5: Populate Certifications
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

        for cert_data in certifications_data:
            Certification.objects.create(**cert_data)

        self.stdout.write(self.style.SUCCESS(f'Created {len(certifications_data)} certifications'))

        # Step 6: Populate Professional Skills
        professional_skills_data = [
            ('Problem Solving', 1),
            ('Communication', 2),
            ('Team Collaboration', 3),
            ('Adaptability', 4),
            ('Quick Learning', 5),
            ('Critical Thinking', 6),
            ('Time Management', 7),
        ]

        for name, order in professional_skills_data:
            ProfessionalSkill.objects.create(name=name, display_order=order)

        self.stdout.write(self.style.SUCCESS(f'Created {len(professional_skills_data)} professional skills'))

        # Step 7: Report Journey status
        self.stdout.write(self.style.WARNING('Journey entries not populated - no chronological journey data provided in resume'))

        self.stdout.write(self.style.SUCCESS('\n=== POPULATION COMPLETE ==='))
        self.stdout.write(f'Skills: {Skill.objects.count()}')
        self.stdout.write(f'Projects: {Project.objects.count()}')
        self.stdout.write(f'Education: {Education.objects.count()}')
        self.stdout.write(f'Certifications: {Certification.objects.count()}')
        self.stdout.write(f'Professional Skills: {ProfessionalSkill.objects.count()}')
        self.stdout.write(f'Journey Entries: {JourneyEntry.objects.count()} (intentionally empty)')
