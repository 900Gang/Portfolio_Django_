"""
Tests for the security hardening: the contact-form rate limit, the admin
sign-in lockout, the Content-Security-Policy, HSTS defaults, the patched
dependencies and the pinned CI actions.

The test runner (portfolio_project.test_runner) clears the cache before every
test, so the per-visitor counters never leak from one test into another.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from . import throttle
from .models import ContactMessage

BASE_DIR = Path(settings.BASE_DIR)

FORM = {
    "name": "Priya Recruiter",
    "email": "priya@example.com",
    "subject": "AI internship",
    "message": "We'd like to talk about a role.",
}


class ThrottleTest(TestCase):
    def test_counts_within_each_window_and_reports_the_overflow(self):
        limits = ((2, 60), (5, 3600))
        results = [throttle.exceeded("demo", "203.0.113.9", limits) for _ in range(3)]
        self.assertEqual(results, [False, False, True])
        # Another visitor has their own counters.
        self.assertFalse(throttle.exceeded("demo", "203.0.113.10", limits))

    def test_hit_count_and_reset(self):
        self.assertEqual(throttle.count("k"), 0)
        self.assertEqual(throttle.hit("k", 60), 1)
        self.assertEqual(throttle.hit("k", 60), 2)
        throttle.reset("k")
        self.assertEqual(throttle.count("k"), 0)


@override_settings(RESEND_API_KEY="")
class ContactRateLimitTest(TestCase):
    def test_sixth_message_in_an_hour_is_refused_and_keeps_the_text(self):
        for _ in range(5):
            response = self.client.post(reverse("portfolio:home"), FORM)
            self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse("portfolio:home"), FORM)
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "sent several messages", status_code=429)
        self.assertContains(response, settings.SITE_EMAIL, status_code=429)
        # The visitor's text is still in the form.
        self.assertContains(response, "We&#x27;d like to talk about a role.", status_code=429)
        self.assertEqual(ContactMessage.objects.count(), 5)

    def test_invalid_submissions_count_too(self):
        for _ in range(5):
            self.client.post(reverse("portfolio:home"), {**FORM, "email": "not-an-email"})
        self.assertEqual(self.client.post(reverse("portfolio:home"), FORM).status_code, 429)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_limits_are_per_visitor(self):
        for _ in range(5):
            self.client.post(reverse("portfolio:home"), FORM, HTTP_CF_CONNECTING_IP="203.0.113.1")
        other = self.client.post(reverse("portfolio:home"), FORM, HTTP_CF_CONNECTING_IP="203.0.113.2")
        self.assertEqual(other.status_code, 302)

    def test_viewing_the_page_is_never_limited(self):
        for _ in range(10):
            self.assertEqual(self.client.get(reverse("portfolio:home")).status_code, 200)


class AdminLoginLockoutTest(TestCase):
    password = "a-long-unique-test-password"

    def setUp(self):
        User.objects.create_superuser("owner", "owner@example.com", self.password)
        self.url = reverse("admin:login")

    def login(self, password, **extra):
        return self.client.post(self.url, {"username": "owner", "password": password}, **extra)

    def test_five_failures_lock_the_visitor_out_even_with_the_right_password(self):
        for _ in range(5):
            response = self.login("wrong")
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, "Too many failed sign-in attempts")
        response = self.login(self.password)
        self.assertContains(response, "Too many failed sign-in attempts")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_the_lockout_is_per_visitor(self):
        for _ in range(5):
            self.login("wrong", HTTP_CF_CONNECTING_IP="203.0.113.1")
        response = self.login(self.password, HTTP_CF_CONNECTING_IP="203.0.113.2")
        self.assertEqual(response.status_code, 302)

    def test_a_successful_sign_in_clears_earlier_failures(self):
        for _ in range(4):
            self.login("wrong")
        self.assertEqual(self.login(self.password).status_code, 302)
        self.client.logout()
        for _ in range(4):
            self.login("wrong")
        self.assertEqual(self.login(self.password).status_code, 302)


class ContentSecurityPolicyTest(TestCase):
    def policy(self, response):
        header = response.headers.get("Content-Security-Policy", "")
        return dict(
            (part.split()[0], part.split()[1:]) for part in header.split(";") if part.strip()
        )

    @override_settings(CSP_ENABLED=True)
    def test_pages_send_a_strict_policy(self):
        for url in (reverse("portfolio:home"), "/robots.txt", reverse("admin:login")):
            with self.subTest(url=url):
                policy = self.policy(self.client.get(url))
                self.assertEqual(policy["default-src"], ["'self'"])
                self.assertEqual(policy["script-src"], ["'self'"])
                self.assertEqual(policy["object-src"], ["'none'"])
                self.assertEqual(policy["frame-ancestors"], ["'none'"])
                self.assertEqual(policy["base-uri"], ["'self'"])
                self.assertEqual(policy["form-action"], ["'self'"])
                self.assertIn("https://fonts.googleapis.com", policy["style-src"])
                self.assertIn("https://fonts.gstatic.com", policy["font-src"])
                self.assertNotIn("'unsafe-inline'", policy["style-src"])

    @override_settings(CSP_ENABLED=False)
    def test_can_be_switched_off(self):
        self.assertNotIn("Content-Security-Policy", self.client.get("/robots.txt").headers)

    def test_the_500_page_inline_styles_are_allowed_by_hash(self):
        """templates/500.html is self-contained (it has to render when things
        are broken), so its one <style> block is allowed by its hash. Editing
        that block changes the hash, and the policy follows automatically."""
        import base64
        import hashlib

        html = (BASE_DIR / "templates" / "500.html").read_text(encoding="utf-8")
        blocks = re.findall(r"<style>(.*?)</style>", html, re.S)
        self.assertEqual(len(blocks), 1)
        digest = base64.b64encode(hashlib.sha256(blocks[0].encode()).digest()).decode()
        self.assertIn(f"'sha256-{digest}'", settings.CONTENT_SECURITY_POLICY)

    def test_templates_have_no_inline_scripts_or_handlers(self):
        """script-src 'self' blocks inline JavaScript; keep it out of the
        templates (JSON-LD data blocks are not executed, so they are fine)."""
        for path in (BASE_DIR / "templates").rglob("*.html"):
            html = path.read_text(encoding="utf-8")
            with self.subTest(template=path.name):
                for tag in re.findall(r"<script\b[^>]*>", html):
                    self.assertTrue(
                        "src=" in tag or "application/ld+json" in tag,
                        f"inline script in {path.name}: {tag}",
                    )
                self.assertIsNone(re.search(r"\son[a-z]+=", html), f"inline handler in {path.name}")
                self.assertNotIn(' style="', html)


class ProductionSecuritySettingsTest(TestCase):
    def _production_settings(self, **env):
        overrides = env
        env = dict(os.environ, DEBUG="False", SECRET_KEY="x" * 60, ALLOWED_HOSTS="nanomachine.xyz")
        for name in ("SECURE_HSTS_SECONDS", "SECURE_HSTS_INCLUDE_SUBDOMAINS", "SECURE_HSTS_PRELOAD", "CSP_ENABLED"):
            env.pop(name, None)
        env.update(overrides)
        script = (
            "import json; from portfolio_project import settings as s; "
            "print(json.dumps({k: getattr(s, k) for k in ('SECURE_HSTS_SECONDS', "
            "'SECURE_HSTS_INCLUDE_SUBDOMAINS', 'SECURE_HSTS_PRELOAD', 'CSP_ENABLED')}))"
        )
        result = subprocess.run(
            [sys.executable, "-c", script], cwd=settings.BASE_DIR, env=env,
            capture_output=True, text=True, check=True,
        )
        return json.loads(result.stdout.strip().splitlines()[-1])

    def test_hsts_is_on_by_default_but_subdomains_and_preload_are_opt_in(self):
        values = self._production_settings()
        self.assertGreaterEqual(values["SECURE_HSTS_SECONDS"], 31536000)
        self.assertFalse(values["SECURE_HSTS_INCLUDE_SUBDOMAINS"])
        self.assertFalse(values["SECURE_HSTS_PRELOAD"])
        self.assertTrue(values["CSP_ENABLED"])

    def test_hsts_options_follow_the_environment(self):
        values = self._production_settings(
            SECURE_HSTS_SECONDS="3600", SECURE_HSTS_INCLUDE_SUBDOMAINS="True", SECURE_HSTS_PRELOAD="True",
        )
        self.assertEqual(values["SECURE_HSTS_SECONDS"], 3600)
        self.assertTrue(values["SECURE_HSTS_INCLUDE_SUBDOMAINS"])
        self.assertTrue(values["SECURE_HSTS_PRELOAD"])


class DependencyTest(TestCase):
    def locked(self):
        lock = (BASE_DIR / "requirements.lock").read_text(encoding="utf-8")
        return dict(re.findall(r"^([a-z0-9_.-]+)==([^\s\\]+)", lock, re.M | re.I))

    def test_patched_versions_are_locked(self):
        versions = self.locked()
        self.assertGreaterEqual(int(versions["pillow"].split(".")[0]), 13)
        certifi = tuple(int(part) for part in versions["certifi"].split("."))
        self.assertGreaterEqual(certifi, (2026, 10, 19))


class WorkflowPinningTest(TestCase):
    def test_actions_are_pinned_to_full_commit_hashes(self):
        workflow = (BASE_DIR / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
        uses = re.findall(r"uses:\s*([^\s#]+)", workflow)
        self.assertTrue(uses)
        for action in uses:
            with self.subTest(action=action):
                self.assertRegex(action, r"@[0-9a-f]{40}$")
