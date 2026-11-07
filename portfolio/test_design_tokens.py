"""Guard the semantic colour pairs used by the portfolio's two themes."""

import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


CSS = Path(settings.BASE_DIR) / "static" / "css" / "variables.css"

# Text pairs are checked at the normal-text threshold, including small labels.
TEXT_PAIRS = (
    ("text-primary", "bg"),
    ("text-secondary", "bg"),
    ("text-muted", "bg"),
    ("accent", "bg"),
    ("text-primary", "surface"),
    ("text-secondary", "surface"),
    ("text-muted", "surface"),
    ("accent", "surface"),
    ("error", "surface"),
    ("on-stage", "stage"),
    ("on-stage-secondary", "stage"),
    ("on-stage-muted", "stage"),
    ("stage-accent", "stage"),
    ("on-stage", "stage-raised"),
    ("on-stage-secondary", "stage-raised"),
    ("on-stage-muted", "stage-raised"),
    ("stage-accent", "stage-raised"),
    ("on-accent", "accent-fill"),
    ("on-accent", "accent-fill-hover"),
    ("on-accent", "accent-deep"),
    ("text-primary", "success-bg"),
    ("text-primary", "error-bg"),
    ("error", "error-bg"),
)

# Status dots carry meaning but are not text; their legend supplies labels.
NON_TEXT_PAIRS = (
    ("status-used", "bg"),
    ("status-building", "bg"),
    ("status-learning", "bg"),
    ("status-used", "surface"),
    ("status-building", "surface"),
    ("status-learning", "surface"),
    ("accent", "bg"),
    ("accent", "surface"),
    ("accent", "success-bg"),
    ("accent", "error-bg"),
    ("stage-accent", "stage"),
    ("stage-accent", "stage-raised"),
    ("on-accent", "accent-fill"),
)


def theme_tokens(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    dark = re.search(r":root\s*\{([^}]*)\}", css).group(1)
    light = re.search(r':root\[data-theme="light"\]\s*\{([^}]*)\}', css).group(1)
    return {
        name: dict(re.findall(r"--color-([\w-]+):\s*(#[0-9a-fA-F]{6})\s*;", block))
        for name, block in (("dark", dark), ("light", light))
    }


def luminance(value):
    channels = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast(foreground, background):
    lighter, darker = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


class DesignTokenContrastTest(SimpleTestCase):
    def test_semantic_pairs_in_both_themes(self):
        for theme, tokens in theme_tokens(CSS.read_text(encoding="utf-8")).items():
            for minimum, pairs in ((4.5, TEXT_PAIRS), (3.0, NON_TEXT_PAIRS)):
                for foreground, background in pairs:
                    with self.subTest(theme=theme, foreground=foreground, background=background):
                        self.assertIn(foreground, tokens)
                        self.assertIn(background, tokens)
                        ratio = contrast(tokens[foreground], tokens[background])
                        self.assertGreaterEqual(ratio, minimum, f"{ratio:.2f}:1 is below {minimum}:1")

    def test_smallest_text_token_is_at_least_twelve_pixels(self):
        css = CSS.read_text(encoding="utf-8")
        size = float(re.search(r"--text-2xs:\s*([\d.]+)rem", css).group(1))
        self.assertGreaterEqual(size, 0.75)
