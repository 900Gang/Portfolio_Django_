from django.contrib import admin
from .models import Skill, Project, JourneyEntry, Education, ContactMessage, Certification, ProfessionalSkill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "status", "order"]
    list_filter = ["category", "status"]
    search_fields = ["name"]
    ordering = ["category", "order", "name"]
    list_editable = ["order"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "featured", "order", "created_at", "updated_at"]
    list_filter = ["featured", "technologies__category"]
    search_fields = ["title", "short_description"]
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ["technologies"]
    ordering = ["-featured", "order", "-created_at"]
    list_editable = ["featured", "order"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(JourneyEntry)
class JourneyEntryAdmin(admin.ModelAdmin):
    list_display = ["date", "title", "entry_type", "order"]
    list_filter = ["entry_type"]
    search_fields = ["title", "description"]
    ordering = ["-date", "order"]
    list_editable = ["order"]


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ["degree", "institution", "start_date", "end_date", "is_current", "order"]
    list_filter = ["is_current"]
    search_fields = ["degree", "institution", "field_of_study"]
    ordering = ["-start_date", "order"]
    list_editable = ["order"]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "subject", "created_at", "is_read"]
    list_filter = ["is_read", "created_at"]
    search_fields = ["name", "email", "subject", "message"]
    ordering = ["-created_at"]
    readonly_fields = ["name", "email", "subject", "message", "created_at"]
    list_editable = ["is_read"]


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ["name", "issuer", "issue_year", "display_order", "is_visible"]
    list_filter = ["is_visible", "issuer"]
    search_fields = ["name", "issuer"]
    ordering = ["display_order", "-issue_year"]
    list_editable = ["display_order", "is_visible"]


@admin.register(ProfessionalSkill)
class ProfessionalSkillAdmin(admin.ModelAdmin):
    list_display = ["name", "display_order", "is_visible"]
    list_filter = ["is_visible"]
    search_fields = ["name"]
    ordering = ["display_order", "name"]
    list_editable = ["display_order", "is_visible"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return obj is None or obj.is_read is False or request.user.is_superuser