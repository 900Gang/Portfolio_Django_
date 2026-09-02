from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib import messages
from .models import Project, Skill, JourneyEntry, Education, Certification, ProfessionalSkill
from .forms import ContactForm


def home(request):
    """
    Homepage view displaying featured projects, skills, journey entries, education,
    certifications, professional skills, and handling contact form submissions.
    """
    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            contact_form.save()
            messages.success(request, 'Your message has been sent successfully.')
            return redirect('portfolio:home')
    else:
        contact_form = ContactForm()

    context = {
        'featured_projects': Project.objects.filter(featured=True).prefetch_related(
            'technologies'
        )[:6],
        'skills': Skill.objects.all(),
        'journey_entries': JourneyEntry.objects.all()[:10],
        'education': Education.objects.all(),
        'certifications': Certification.objects.filter(is_visible=True),
        'professional_skills': ProfessionalSkill.objects.filter(is_visible=True),
        'contact_form': contact_form,
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