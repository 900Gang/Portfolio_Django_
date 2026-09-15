from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods
from django.views.generic import DetailView

from .forms import ContactForm
from .models import (
    SKILL_CATEGORY_DISPLAY_ORDER,
    Certification,
    Education,
    JourneyEntry,
    ProfessionalSkill,
    Project,
    Skill,
)


@require_http_methods(["GET", "HEAD", "POST"])
def home(request):
    """
    The single-page portfolio: featured work, skills, journey, education,
    credentials, and the contact form.

    Methods are declared explicitly. Without this, a PUT or DELETE to `/`
    fell through to the GET branch and rendered the page rather than being
    rejected with 405.
    """
    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            contact_form.save()
            messages.success(request, 'Your message has been sent successfully.')
            # Redirect after a successful POST so a refresh cannot resubmit.
            return redirect('portfolio:home')
        messages.error(
            request,
            'Your message could not be sent. Please check the highlighted fields.',
        )
    else:
        contact_form = ContactForm()

    # Sorted in Python rather than the database: the editorial group order is
    # not the alphabetical order of the stored category values, and the list is
    # a few dozen rows fetched in one query either way.
    category_rank = {value: index for index, value in enumerate(SKILL_CATEGORY_DISPLAY_ORDER)}
    skills = sorted(
        Skill.objects.all(),
        key=lambda skill: (
            category_rank.get(skill.category, len(category_rank)),
            skill.order,
            skill.name,
        ),
    )

    context = {
        'featured_projects': Project.objects.filter(featured=True).prefetch_related(
            'technologies'
        )[:6],
        'skills': skills,
        'journey_entries': JourneyEntry.objects.all()[:10],
        'education': Education.objects.all(),
        'certifications': Certification.objects.filter(is_visible=True),
        'professional_skills': ProfessionalSkill.objects.filter(is_visible=True),
        'contact_form': contact_form,
    }
    # The hero's headline figures are counted in the template from these same
    # objects (`|length`), not re-queried here: every one of them is rendered
    # further down the page anyway, so the counts cost no extra queries and
    # cannot disagree with what the visitor can actually see.
    return render(request, 'portfolio/home.html', context)


class ProjectDetailView(DetailView):
    """A single project, with its technology list."""

    model = Project
    template_name = 'portfolio/project_detail.html'
    context_object_name = 'project'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        # Prefetch here rather than in get_context_data, so the M2M is
        # fetched with the object instead of on first template access.
        return super().get_queryset().prefetch_related('technologies')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['technologies'] = self.object.technologies.all()
        return context


@require_GET
def robots_txt(request):
    """
    Allow everything and point crawlers at the sitemap.

    Served from a view rather than a static file so the sitemap URL is
    reversed, and so it keeps working under a hashed-static deployment.
    """
    sitemap_url = request.build_absolute_uri(reverse('django.contrib.sitemaps.views.sitemap'))
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
        '',
        f'Sitemap: {sitemap_url}',
        '',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')
