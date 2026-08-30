from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Project, Skill, JourneyEntry, Education


def home(request):
    """
    Homepage view displaying featured projects, skills, journey entries, and education.
    """
    context = {
        'featured_projects': Project.objects.filter(featured=True)[:6],
        'skills': Skill.objects.all(),
        'journey_entries': JourneyEntry.objects.all()[:10],
        'education': Education.objects.all(),
    }
    return render(request, 'portfolio/home.html', context)


class ProjectDetailView(DetailView):
    """
    Project detail view showing a single project with its technologies.
    """
    model = Project
    template_name = 'portfolio/project_detail.html'
    context_object_name = 'project'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Prefetch technologies to avoid N+1 queries
        context['technologies'] = self.object.technologies.all()
        return context