"""
URL configuration for portfolio_project.

Public routes live in portfolio.urls; this module wires the admin, the
crawler endpoints, and — in DEBUG only — media file serving.
"""
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from portfolio.sitemaps import sitemaps
from portfolio.views import robots_txt

urlpatterns = [
    path('admin/', admin.site.urls),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('', include('portfolio.urls')),
]

if settings.DEBUG:
    # In production media is served by the same host as static files; this
    # helper is deliberately development-only.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
