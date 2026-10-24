"""
The site's Content-Security-Policy.

Everything the pages load is listed here: the site's own scripts, styles,
images and API, plus Google Fonts. No inline JavaScript is allowed. The only
inline CSS is the <style> block in templates/500.html, which must render when
the rest of the site is broken; it is allowed by its SHA-256 hash, read from
the template at start-up, so editing that block keeps the policy in step.
"""
import base64
import hashlib
import re
from pathlib import Path


def _style_hashes(template: Path):
    try:
        html = template.read_text(encoding="utf-8")
    except OSError:
        return []
    return [
        "'sha256-" + base64.b64encode(hashlib.sha256(block.encode()).digest()).decode() + "'"
        for block in re.findall(r"<style>(.*?)</style>", html, re.S)
    ]


def build_policy(error_template: Path) -> str:
    directives = {
        "default-src": ["'self'"],
        "script-src": ["'self'"],
        "style-src": ["'self'", "https://fonts.googleapis.com", *_style_hashes(error_template)],
        "font-src": ["'self'", "https://fonts.gstatic.com"],
        "img-src": ["'self'", "data:"],
        "connect-src": ["'self'"],
        "object-src": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
        "frame-ancestors": ["'none'"],
    }
    return "; ".join(f"{name} {' '.join(values)}" for name, values in directives.items())
