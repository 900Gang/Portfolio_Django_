"""
Export the hero portrait as the web-sized WebP files the hero serves.

    python manage.py make_portrait design/photos/1000256303.jpg

The original photo stays outside the static tree: design/ is git-ignored,
and everything under static/ is published. The outputs are committed.
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageOps

# Must match the srcset in templates/portfolio/sections/hero.html.
WIDTHS = (480, 768)


class Command(BaseCommand):
    help = 'Export the hero portrait as WebP at the widths the hero serves.'

    def add_arguments(self, parser):
        parser.add_argument('source', help='Path to the original portrait.')
        parser.add_argument('--output-dir', help='Destination folder. Defaults to static/img.')
        parser.add_argument('--quality', type=int, default=82, help='WebP quality (default 82).')

    def handle(self, *args, **options):
        source = Path(options['source'])
        if not source.is_file():
            raise CommandError(f'{source} does not exist.')

        output_dir = Path(options['output_dir']) if options['output_dir'] else (
            Path(settings.BASE_DIR) / 'static' / 'img'
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        with Image.open(source) as original:
            image = ImageOps.exif_transpose(original).convert('RGB')

        for width in WIDTHS:
            if image.width < width:
                self.stderr.write(self.style.WARNING(
                    f'{source} is only {image.width}px wide; upscaling to {width}px.'
                ))
            height = round(image.height * width / image.width)
            resized = image.resize((width, height), Image.Resampling.LANCZOS)
            destination = output_dir / f'portrait-{width}.webp'
            resized.save(destination, 'WEBP', quality=options['quality'], method=6)
            self.stdout.write(self.style.SUCCESS(
                f'Wrote {destination} ({width}x{height}, {destination.stat().st_size // 1024} KB)'
            ))
