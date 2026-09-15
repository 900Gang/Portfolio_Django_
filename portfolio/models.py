from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError


class SkillCategory(models.TextChoices):
    """
    Skill groupings, mirroring how the résumé itself splits them.

    DevOps and Testing used to live inside TOOLS, which left one seventeen-item
    bucket holding version control, CI/CD and QA process side by side.
    """

    DEVOPS = "devops", "DevOps & Cloud"
    BACKEND = "backend", "Backend & Data"
    FRONTEND = "frontend", "Web & Frontend"
    TESTING = "testing", "Testing & Process"
    TOOLS = "tools", "Tools & Workflow"
    CONCEPTS = "concepts", "Core Concepts"


# The order the groups are presented in, strongest first. `Meta.ordering`
# sorts on the stored value, which is alphabetical and therefore arbitrary;
# this is the editorial order the Skills section actually uses. Backend & Data
# leads because it holds the AI stack (TensorFlow, Keras, OpenCV) the site is
# positioned on; DevOps & Cloud stays, one rung down.
SKILL_CATEGORY_DISPLAY_ORDER = [
    SkillCategory.BACKEND,
    SkillCategory.DEVOPS,
    SkillCategory.FRONTEND,
    SkillCategory.TESTING,
    SkillCategory.TOOLS,
    SkillCategory.CONCEPTS,
]


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

    def get_absolute_url(self):
        """
        Canonical URL for this project.

        Defined on the model so the sitemap, the admin's "view on site"
        link and the templates all resolve the same route from one place.
        """
        return reverse('portfolio:project_detail', kwargs={'slug': self.slug})

    @property
    def project_type(self):
        """
        Human label for the project's provenance.

        Derived by matching marker phrases in the descriptions, which is how
        both the card and detail templates used to classify projects inline.
        Kept in one place so the two templates cannot drift apart.
        """
        haystack = f"{self.short_description} {self.description}"
        if "Major project" in haystack:
            return "Academic Project"
        if "Personal project" in haystack:
            return "Personal Project"
        return "Project"

    @property
    def has_image(self):
        """
        True only when an image is set *and* the file is actually present.

        `bool(self.image)` is true for any non-empty path, so a record whose
        file has been lost (or which was restored from a database backup
        without its media directory) would otherwise render a broken <img>
        instead of falling back to the placeholder.
        """
        if not self.image:
            return False
        try:
            return self.image.storage.exists(self.image.name)
        except (OSError, ValueError, NotImplementedError):
            return False

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