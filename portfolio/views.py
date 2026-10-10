import json
import logging

from django.conf import settings
from django.contrib import messages
from django.db.models import Count, IntegerField, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.views.generic import DetailView

from . import chatbot, notifications
from .forms import ContactForm
from .models import (
    SKILL_CATEGORY_DISPLAY_ORDER,
    Certification,
    ChatLog,
    Education,
    JourneyEntry,
    ProfessionalSkill,
    Project,
    Skill,
)

logger = logging.getLogger(__name__)


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
            notifications.notify_new_message(contact_form.save())
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
        #
        # featured_ahead counts the featured projects listed before this one
        # under Project.Meta.ordering, so the page can show the same number
        # as its home-page card (01, 02, ...). It is a subquery inside the
        # same SELECT, so it costs no extra query.
        ahead = (
            Project.objects.filter(featured=True)
            .filter(
                Q(order__lt=OuterRef('order'))
                | Q(order=OuterRef('order'), created_at__gt=OuterRef('created_at'))
                | Q(order=OuterRef('order'), created_at=OuterRef('created_at'), pk__lt=OuterRef('pk'))
            )
            .order_by()
            .values('featured')
            .annotate(count=Count('pk'))
            .values('count')
        )
        return (
            super().get_queryset()
            .prefetch_related('technologies')
            .annotate(featured_ahead=Coalesce(Subquery(ahead, output_field=IntegerField()), Value(0)))
        )

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
        'Disallow: /api/',
        '',
        f'Sitemap: {sitemap_url}',
        '',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


@require_POST
def chat(request):
    """
    Answer one visitor question with the portfolio assistant.

    JSON in ({"message", "history", "conversation_id"}), JSON out
    ({"reply", "conversation_id"} or {"error"}). CSRF-protected like any
    other POST; the widget sends the token in the X-CSRFToken header.
    """
    if not settings.CHATBOT_ENABLED:
        return JsonResponse({"error": "The assistant is not available."}, status=503)

    try:
        payload = json.loads(request.body or b"")
        message, history, conversation_id = chatbot.parse_request(payload)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Send a JSON object."}, status=400)
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)

    if chatbot.rate_limited(chatbot.client_ip(request)):
        return JsonResponse(
            {"error": "You've asked a lot of questions — try again in a few minutes, or use the contact form."},
            status=429,
        )

    try:
        answer = chatbot.ask(message, history)
    except chatbot.ChatbotBusy:
        logger.warning("Portfolio assistant hit Google's rate limit")
        return JsonResponse(
            {"error": f"The assistant is busy right now. Try again in a minute, or email {chatbot.first_name()} at {settings.SITE_EMAIL}."},
            status=503,
        )
    except chatbot.ChatbotUnavailable:
        logger.exception("Portfolio assistant request failed")
        return JsonResponse(
            {"error": f"I can't answer right now. You can email {chatbot.first_name()} at {settings.SITE_EMAIL}."},
            status=502,
        )

    ChatLog.objects.create(
        conversation_id=conversation_id,
        question=message,
        answer=answer.text,
        model=settings.CHATBOT_MODEL,
        input_tokens=answer.input_tokens,
        output_tokens=answer.output_tokens,
        cache_read_tokens=answer.cache_read_tokens,
    )
    return JsonResponse({"reply": answer.text, "conversation_id": conversation_id})
