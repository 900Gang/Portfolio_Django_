"""
Sitemaps for search engines.

The site is two URL shapes — the single-page home and one page per project —
so the map is small, but publishing it is what gets project pages crawled
rather than leaving them reachable only through in-page anchors.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Project


class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'monthly'

    def items(self):
        return ['portfolio:home']

    def location(self, item):
        return reverse(item)


class ProjectSitemap(Sitemap):
    priority = 0.8
    changefreq = 'monthly'

    def items(self):
        return Project.objects.all()

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {
    'static': StaticViewSitemap,
    'projects': ProjectSitemap,
}
