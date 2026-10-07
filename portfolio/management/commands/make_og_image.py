"""
Render the link-preview (Open Graph) image.

Social platforms will not render an SVG og:image and do not execute CSS, so
the card has to exist as a raster file. Generating it from the site's own
identity settings — rather than hand-designing one in an image editor —
means it cannot drift out of date when the name, role or tagline changes.

    python manage.py make_og_image --photo design/photos/1000256302.jpg

The headshot is optional; without it the card is text only. Pillow is
already a dependency (ImageField), so this adds no new packages.
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageDraw, ImageFont, ImageOps

from portfolio.templatetags.portfolio_extras import handle as detection_handle

# Facebook, LinkedIn, Slack and X all crop toward 1.91:1.
WIDTH, HEIGHT = 1200, 630
MARGIN = 72
PHOTO_SIZE = 470
GAP = 48

# Pulled from the dark theme in variables.css. Duplicated deliberately: the
# generator cannot parse CSS custom properties, and a preview that silently
# stopped matching the site would be worse than one that is pinned.
BG = (7, 7, 7)
ACCENT = (239, 59, 66)
ACCENT_FILL = (214, 31, 38)
TEXT = (242, 239, 234)
MUTED = (138, 132, 126)
RULE = (38, 38, 38)
WHITE = (255, 255, 255)

# Where the face sits inside the square headshot crop, as fractions
# (left, top, right, bottom). Tuned for design/photos/1000256302.jpg.
FACE_BOX = (0.27, 0.18, 0.75, 0.70)

# Preference order: the site's own typefaces if installed, then the closest
# common system faces. Impact stands in for Anton on Windows.
FONT_CANDIDATES = {
    'display': [
        '~/Library/Fonts/Anton-Regular.ttf',
        '/Library/Fonts/Anton-Regular.ttf',
        '/usr/share/fonts/truetype/anton/Anton-Regular.ttf',
        'C:/Windows/Fonts/Anton-Regular.ttf',
        '/System/Library/Fonts/Supplemental/Impact.ttf',
        '/usr/share/fonts/truetype/msttcorefonts/Impact.ttf',
        'C:/Windows/Fonts/impact.ttf',
        'C:/Windows/Fonts/ariblk.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    ],
    'regular': [
        '~/Library/Fonts/Archivo-Regular.ttf',
        '/usr/share/fonts/truetype/archivo/Archivo-Regular.ttf',
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


def _fit(draw, text, kind, size, max_width, minimum=40):
    """The largest font of `kind`, from `size` down, that fits `text`."""
    while size > minimum:
        font = _font(kind, size)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 4
    return _font(kind, minimum)


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


def _draw_photo(image, draw, photo_path):
    """The headshot on the right, square-cropped, with the hero's detection box."""
    with Image.open(photo_path) as source:
        photo = ImageOps.fit(
            ImageOps.exif_transpose(source).convert('RGB'),
            (PHOTO_SIZE, PHOTO_SIZE),
            Image.Resampling.LANCZOS,
            centering=(0.5, 0.35),
        )
    left = WIDTH - MARGIN - PHOTO_SIZE
    top = (HEIGHT - PHOTO_SIZE) // 2
    image.paste(photo, (left, top))

    x0 = left + round(PHOTO_SIZE * FACE_BOX[0])
    y0 = top + round(PHOTO_SIZE * FACE_BOX[1])
    x1 = left + round(PHOTO_SIZE * FACE_BOX[2])
    y1 = top + round(PHOTO_SIZE * FACE_BOX[3])
    draw.rectangle([x0, y0, x1, y1], outline=ACCENT, width=2)

    arm = 18
    for corner_x, corner_y, step in ((x0, y0, 1), (x1, y1, -1)):
        draw.line([(corner_x, corner_y), (corner_x + step * arm, corner_y)], fill=ACCENT, width=5)
        draw.line([(corner_x, corner_y), (corner_x, corner_y + step * arm)], fill=ACCENT, width=5)

    label = f'{detection_handle(settings.SITE_OWNER)} · 0.99'
    font = _font('mono', 18)
    label_width = draw.textlength(label, font=font)
    draw.rectangle([x0, y0 - 30, x0 + label_width + 16, y0 - 2], fill=ACCENT_FILL)
    draw.text((x0 + 8, y0 - 26), label, font=font, fill=WHITE)


class Command(BaseCommand):
    help = 'Render the Open Graph link-preview image into the static tree.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            help='Destination path. Defaults to static/<OG_IMAGE_STATIC_PATH>.',
        )
        parser.add_argument(
            '--photo',
            help='Optional headshot placed on the right of the card.',
        )

    def handle(self, *args, **options):
        relative = settings.OG_IMAGE_STATIC_PATH
        if not relative:
            raise CommandError('OG_IMAGE_STATIC_PATH is empty; nothing to render.')

        photo = Path(options['photo']) if options['photo'] else None
        if photo is not None and not photo.is_file():
            raise CommandError(f'{photo} does not exist.')

        destination = Path(options['output']) if options['output'] else (
            Path(settings.BASE_DIR) / 'static' / relative
        )
        destination.parent.mkdir(parents=True, exist_ok=True)

        image = Image.new('RGB', (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(image)

        text_width = WIDTH - 2 * MARGIN
        if photo is not None:
            _draw_photo(image, draw, photo)
            text_width -= PHOTO_SIZE + GAP

        y = MARGIN + 6
        draw.text((MARGIN, y), settings.SITE_ROLE.upper(), font=_font('mono', 24), fill=ACCENT)
        y += 54

        name = settings.SITE_OWNER.upper()
        name_font = _fit(draw, name, 'display', 132, text_width)
        draw.text((MARGIN, y), name, font=name_font, fill=TEXT)
        y += getattr(name_font, 'size', 60) + 26

        draw.rectangle([MARGIN, y, MARGIN + 96, y + 4], fill=ACCENT)
        y += 34

        focus_font = _font('regular', 30)
        for line in _wrap(draw, settings.SITE_FOCUS, focus_font, text_width)[:2]:
            draw.text((MARGIN, y), line, font=focus_font, fill=TEXT)
            y += 42

        y += 10
        description_font = _font('regular', 22)
        for line in _wrap(draw, settings.SITE_DESCRIPTION, description_font, text_width)[:2]:
            draw.text((MARGIN, y), line, font=description_font, fill=MUTED)
            y += 32

        footer_y = HEIGHT - MARGIN - 18
        draw.line(
            [(MARGIN, footer_y - 26), (MARGIN + text_width, footer_y - 26)],
            fill=RULE, width=2,
        )
        footer = ' · '.join(
            part for part in (settings.SITE_LOCATION, settings.SITE_EMAIL) if part
        )
        footer_font = _fit(draw, footer, 'mono', 20, text_width, minimum=12)
        draw.text((MARGIN, footer_y), footer, font=footer_font, fill=MUTED)

        image.save(destination, 'PNG', optimize=True)
        self.stdout.write(self.style.SUCCESS(f'Wrote {destination} ({WIDTH}x{HEIGHT})'))
