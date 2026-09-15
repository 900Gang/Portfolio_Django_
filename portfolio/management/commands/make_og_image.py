"""
Render the link-preview (Open Graph) image.

Social platforms will not render an SVG og:image and do not execute CSS, so
the card has to exist as a raster file. Generating it from the site's own
identity settings — rather than hand-designing one in an image editor — means
it cannot drift out of date when the name, role or tagline changes.

    python manage.py make_og_image

Pillow is already a dependency (ImageField), so this adds no new packages.
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageDraw, ImageFont

# Facebook, LinkedIn, Slack and X all crop toward 1.91:1.
WIDTH, HEIGHT = 1200, 630
MARGIN = 84

# Pulled from the dark theme in variables.css. Duplicated deliberately: the
# generator cannot parse CSS custom properties, and a link preview that
# silently stopped matching the site would be worse than one that is pinned.
BG = (12, 18, 17)
SURFACE = (20, 29, 28)
ACCENT = (86, 200, 192)
TEXT = (232, 239, 236)
MUTED = (134, 150, 146)
RULE = (38, 49, 47)

# Preference order: the site's own typeface if it happens to be installed,
# then a reasonable sans on each platform.
FONT_CANDIDATES = {
    'bold': [
        '/Library/Fonts/IBMPlexSans-Bold.ttf',
        '~/Library/Fonts/IBMPlexSans-Bold.ttf',
        '/usr/share/fonts/truetype/ibm-plex/IBMPlexSans-Bold.ttf',
        '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        'C:/Windows/Fonts/arialbd.ttf',
    ],
    'regular': [
        '/Library/Fonts/IBMPlexSans-Regular.ttf',
        '~/Library/Fonts/IBMPlexSans-Regular.ttf',
        '/usr/share/fonts/truetype/ibm-plex/IBMPlexSans-Regular.ttf',
        '/System/Library/Fonts/Supplemental/Arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        'C:/Windows/Fonts/arial.ttf',
    ],
    'mono': [
        '/Library/Fonts/IBMPlexMono-Medium.ttf',
        '~/Library/Fonts/IBMPlexMono-Medium.ttf',
        '/usr/share/fonts/truetype/ibm-plex/IBMPlexMono-Medium.ttf',
        '/System/Library/Fonts/Supplemental/Courier New Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
        'C:/Windows/Fonts/courbd.ttf',
    ],
}


def _font(kind, size):
    for candidate in FONT_CANDIDATES[kind]:
        path = Path(candidate).expanduser()
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    # Better a legible bitmap card than no preview image at all.
    return ImageFont.load_default()


def _wrap(draw, text, font, max_width):
    """Greedy word wrap against the rendered width of each candidate line."""
    lines, line = [], ''
    for word in text.split():
        trial = f'{line} {word}'.strip()
        if draw.textlength(trial, font=font) <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


class Command(BaseCommand):
    help = 'Render the Open Graph link-preview image into the static tree.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            help='Destination path. Defaults to static/<OG_IMAGE_STATIC_PATH>.',
        )

    def handle(self, *args, **options):
        relative = settings.OG_IMAGE_STATIC_PATH
        if not relative:
            raise CommandError('OG_IMAGE_STATIC_PATH is empty; nothing to render.')

        destination = Path(options['output']) if options['output'] else (
            settings.BASE_DIR / 'static' / relative
        )
        destination.parent.mkdir(parents=True, exist_ok=True)

        image = Image.new('RGB', (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(image)

        # Faint engineering grid, echoing the hero background.
        for x in range(0, WIDTH, 60):
            draw.line([(x, 0), (x, HEIGHT)], fill=SURFACE, width=1)
        for y in range(0, HEIGHT, 60):
            draw.line([(0, y), (WIDTH, y)], fill=SURFACE, width=1)

        # Accent bar down the left edge.
        draw.rectangle([0, 0, 10, HEIGHT], fill=ACCENT)

        eyebrow_font = _font('mono', 24)
        name_font = _font('bold', 92)
        role_font = _font('regular', 36)
        tag_font = _font('regular', 26)

        y = MARGIN

        draw.text((MARGIN, y), settings.SITE_ROLE.upper(), font=eyebrow_font, fill=ACCENT)
        y += 62

        draw.text((MARGIN, y), settings.SITE_OWNER, font=name_font, fill=TEXT)
        y += 118

        draw.line([(MARGIN, y), (MARGIN + 120, y)], fill=ACCENT, width=4)
        y += 44

        for line in _wrap(draw, settings.SITE_FOCUS, role_font, WIDTH - 2 * MARGIN)[:2]:
            draw.text((MARGIN, y), line, font=role_font, fill=TEXT)
            y += 50

        y += 14
        for line in _wrap(draw, settings.SITE_DESCRIPTION, tag_font, WIDTH - 2 * MARGIN)[:2]:
            draw.text((MARGIN, y), line, font=tag_font, fill=MUTED)
            y += 38

        # Footer rule with the contact line.
        footer_y = HEIGHT - MARGIN - 20
        draw.line([(MARGIN, footer_y - 34), (WIDTH - MARGIN, footer_y - 34)], fill=RULE, width=2)
        footer = ' · '.join(
            part for part in (settings.SITE_LOCATION, settings.SITE_EMAIL) if part
        )
        draw.text((MARGIN, footer_y), footer, font=_font('mono', 22), fill=MUTED)

        image.save(destination, 'PNG', optimize=True)
        self.stdout.write(self.style.SUCCESS(f'Wrote {destination} ({WIDTH}x{HEIGHT})'))
