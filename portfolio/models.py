from django.db import models
from django.utils.text import slugify
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError


class SkillCategory(models.TextChoices):
    FRONTEND = "frontend", "Frontend"
    BACKEND = "backend", "Backend"
    TOOLS = "tools", "Tools & Workflow"
    CONCEPTS = "concepts", "Concepts"


class SkillStatus(models.TextChoices):
    LEARNING = "learning", "Learning"
    BUILDING_WITH = "building_with", "Building With"
    USED_IN_PROJECTS = "used_in_projects", "Used in Projects"


class Skill(models.Model):
    name = models.CharField(max_length=60)
    category = models.CharField(
        max_length=20,
        choices=SkillCategory.choices,
        default=SkillCategory.CONCEPTS,
    )
    status = models.CharField(
        max_length=20,
        choices=SkillStatus.choices,
        default=SkillStatus.LEARNING,
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["category", "order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "category"],
                name="unique_skill_per_category",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Project(models.Model):
    title = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    short_description = models.TextField(max_length=300)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="projects/", blank=True, null=True)
    github_url = models.URLField(blank=True, validators=[URLValidator()])
    live_demo_url = models.URLField(blank=True, validators=[URLValidator()])
    featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    technologies = models.ManyToManyField(
        Skill,
        related_name="projects",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-featured", "order", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class JourneyEntryType(models.TextChoices):
    LEARNING = "learning", "Learning"
    PROJECT = "project", "Project"
    MILESTONE = "milestone", "Milestone"
    EXPERIENCE = "experience", "Experience"


class JourneyEntry(models.Model):
    date = models.DateField()
    title = models.CharField(max_length=150)
    description = models.TextField()
    entry_type = models.CharField(
        max_length=20,
        choices=JourneyEntryType.choices,
        default=JourneyEntryType.LEARNING,
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-date", "order"]
        verbose_name = "Journey Entry"
        verbose_name_plural = "Journey Entries"

    def __str__(self):
        return f"{self.date.year} — {self.title}"


class Education(models.Model):
    institution = models.CharField(max_length=150)
    degree = models.CharField(max_length=120)
    field_of_study = models.CharField(max_length=120, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-start_date", "order"]
        verbose_name = "Education"
        verbose_name_plural = "Education"

    def __str__(self):
        return f"{self.degree} — {self.institution}"

    def clean(self):
        if self.is_current and self.end_date:
            raise ValidationError("Current education should not have an end date.")
        if not self.is_current and not self.end_date:
            raise ValidationError("Past education must have an end date.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"{self.name} — {self.subject} ({self.created_at.strftime('%Y-%m-%d')})"


class Certification(models.Model):
    """Model for professional certifications."""
    name = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200)
    issue_year = models.PositiveIntegerField(blank=True, null=True)
    credential_url = models.URLField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "-issue_year", "name"]
        verbose_name = "Certification"
        verbose_name_plural = "Certifications"

    def __str__(self):
        return f"{self.name} — {self.issuer}"


class ProfessionalSkill(models.Model):
    """Model for professional/soft skills."""
    name = models.CharField(max_length=100)
    display_order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "Professional Skill"
        verbose_name_plural = "Professional Skills"

    def __str__(self):
        return self.name