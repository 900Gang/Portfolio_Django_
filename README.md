# Developer Portfolio

A database-driven developer portfolio built with Django — content is managed
through the admin, not by editing templates.

Live sections: hero, about, featured projects (with a page per project),
technical skills, journey timeline, education, certifications, professional
skills, and a contact form that stores messages.

## Tech Stack

- **Backend**: Python 3.12, Django 5
- **Frontend**: Hand-written HTML, CSS and vanilla JavaScript — no framework, no build step
- **Database**: SQLite (development)
- **Static files**: WhiteNoise, with hashed + compressed assets in production
- **Images**: Pillow (project screenshots, generated link-preview card)

## Design

The visual layer is a small, explicit design system rather than a CSS
framework:

| File | Responsibility |
|------|----------------|
| `static/css/variables.css` | **Every colour in the project.** Design tokens for colour, type, spacing, shape and motion |
| `static/css/reset.css` | Minimal normalisation |
| `static/css/base.css` | Element-level typography, forms, page scaffolding |
| `static/css/components.css` | Buttons, cards, navigation, every section, project page |
| `static/css/responsive.css` | Mobile navigation, small-screen overrides, reduced-motion and print |

Rules the test suite enforces:

- **Colour lives in one file.** No hex or `rgba()` value may appear outside
  `variables.css`, and every `--color-*` token must have a dark-mode value.
- **Every stylesheet on disk must be linked.** Orphaned CSS fails the build.
- **No CSS custom properties inside media queries** — `@media (min-width: var(--x))`
  is invalid and silently discards the whole at-rule.

Typography is IBM Plex Sans for prose and IBM Plex Mono for labels, metadata
and numbers. Type scales fluidly with `clamp()`, so there are no per-breakpoint
heading overrides.

### Theming

Three states: explicit light, explicit dark, and follow-the-OS (the default).
`static/js/theme.js` is loaded **synchronously in `<head>`** so the stored
choice is applied before first paint — deferring it would flash the light
theme at a dark-mode visitor. Dark values are declared twice, under both
`prefers-color-scheme` and `[data-theme="dark"]`, so the manual toggle can
override the OS in both directions.

## Local Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

4. Apply migrations and load the seed content:
   ```bash
   python manage.py migrate
   python manage.py populate_portfolio
   ```

5. Create a superuser for the admin:
   ```bash
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```bash
   python manage.py runserver
   ```

Visit `http://127.0.0.1:8000/`; the admin is at `/admin/`.

## Content Management

All content is editable in the Django admin. Nothing on the page is hard-coded
except the section copy in `templates/portfolio/home.html`.

| Model | Notes |
|-------|-------|
| `Project` | Set `featured` to show it on the home page (max 6). Slug auto-generates from the title |
| `Skill` | Grouped into DevOps & Cloud, Backend & Data, Web & Frontend, Testing & Process, Tools & Workflow and Core Concepts — mirroring the résumé's own groupings. Status (Learning / Building With / Used in Projects) renders as a coloured dot |
| `Education`, `Certification`, `ProfessionalSkill` | `is_visible` / ordering fields control display |
| `JourneyEntry` | The Journey section **and its nav link** are hidden entirely when there are no entries |
| `ContactMessage` | Read-only in the admin; submissions are stored, not emailed |

`python manage.py populate_portfolio` reloads the seed content. It is
idempotent — every record is matched on its natural key and updated in place —
and `--prune` removes skills that are no longer in the seed data.

## Link Previews

```bash
python manage.py make_og_image
```

Renders `static/img/og-image.png` (1200×630) from the site identity settings,
so the card shared to LinkedIn or Slack cannot drift out of date when the name,
role or tagline changes. The `og:image` tags are emitted only when the file
actually exists, and always as absolute URLs — scrapers do not resolve
relative ones.

`robots.txt` and `sitemap.xml` are served from the app; the sitemap covers the
home page and every project.

## Environment Variables

Settings are read from the environment; a `.env` file at the project root is
loaded automatically, and real environment variables take precedence over it.

### Required in production

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | insecure dev key | Django secret key. Mandatory when `DEBUG=False` |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` in debug | Comma-separated allowed hosts |
| `SITE_URL` | empty | Absolute site URL, used for canonical tags and `og:image` |

### Security

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `False` | Debug mode |
| `CSRF_TRUSTED_ORIGINS` | empty | Comma-separated origins, production only |
| `SECURE_SSL_REDIRECT` | `True` in production | Redirect HTTP to HTTPS |
| `SECURE_HSTS_SECONDS` | `0` | Enables HSTS when greater than zero |

`DEBUG` defaults to `False` and `SECRET_KEY` is mandatory outside debug, so a
misconfigured deployment fails at startup rather than serving insecurely.
Outside debug the project also sets secure cookies, `nosniff`,
`X-Frame-Options: DENY` and a `strict-origin-when-cross-origin` referrer policy.

### Identity

`SITE_OWNER`, `SITE_ROLE`, `SITE_TAGLINE`, `SITE_DESCRIPTION`, `SITE_EMAIL`,
`SITE_PHONE`, `SITE_GITHUB_URL`, `SITE_LINKEDIN_URL`, `SITE_LOCATION`,
`SITE_FOCUS`, `SITE_AVAILABILITY`, `RESUME_STATIC_PATH`,
`RESUME_DOWNLOAD_NAME`, `OG_IMAGE_STATIC_PATH`. See `.env.example`.

Three of these gate UI: `SITE_AVAILABILITY` set to an empty value hides the
"open to opportunities" pill, `SITE_PHONE` set to an empty value drops the
phone row from the contact section, and the résumé button appears only once the
file at `RESUME_STATIC_PATH` actually exists — so the site never ships a
download link that 404s.

### Keeping the site and the résumé in step

Site copy, skills, project technologies and the generated preview card are all
derived from the résumé in `static/files/`. When the résumé changes:

1. Update `SITE_ROLE` / `SITE_DESCRIPTION` / `SITE_FOCUS` if the positioning moved.
2. Update the seed data in `portfolio/management/commands/populate_portfolio.py`
   and re-run `python manage.py populate_portfolio --prune` (`--prune` removes
   skills and professional skills that are no longer in the seed, so a rename
   does not leave both versions on the page).
3. Re-run `python manage.py make_og_image`.

`RESUME_STATIC_PATH` is asserted by the test suite to point at a file that
really exists, so swapping the PDF for one with a different filename fails the
build rather than silently hiding the download button.

## Deployment

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn portfolio_project.wsgi   # or any WSGI server
```

WhiteNoise serves the collected static files from the app server, so no
separate web server or CDN is required. Outside `DEBUG`, assets are hashed and
pre-compressed at collect time and served with immutable cache headers, so a
deploy busts the cache by itself.

### Media

Project screenshots are `ImageField` uploads in `MEDIA_ROOT`, not static files,
so they need two things stock Django does not give them in production:

- `portfolio_project.middleware.WhiteNoiseWithMediaMiddleware` extends
  WhiteNoise to serve `MEDIA_ROOT` under `MEDIA_URL`. Stock WhiteNoise serves
  `STATIC_ROOT` only, and `urls.py` wires media up under `DEBUG` alone, so
  without this every project card fell back to the placeholder on a deployed
  site while looking correct locally.
- The two seeded screenshots are committed (see the exception at the bottom of
  `.gitignore`) and attached by `populate_portfolio`. `db.sqlite3` is not
  tracked, so a fresh deploy seeds an empty database — the images have to be in
  the repo *and* referenced by the seed, or the cards come up blank.

`WHITENOISE_AUTOREFRESH` defaults to `True` so an image uploaded through the
admin appears without a restart. Set it to `False` to trade that for slightly
less filesystem work per request.

Note that SQLite and locally-stored media are fine for a single instance but
do not survive an ephemeral filesystem; on a platform with ephemeral storage,
move `DATABASES` to Postgres and media to object storage.

## Tests

```bash
python manage.py test
```

156 tests across two files:

- `portfolio/tests.py` — the feature suite: models, views, form validation,
  and every section's rendering and empty state.
- `portfolio/test_regressions.py` — tests that pin previously-fixed bugs and
  the properties the design system relies on: admin permissions, skill
  grouping, seed idempotency, **constant query counts**, static-asset lints,
  colour-token discipline, crawler endpoints, link-preview tags, theme
  override behaviour, nav-anchor resolution, honeypot spam protection,
  résumé wiring, project-image delivery and error pages.

The query-count tests assert the home page and project page issue the same
number of queries regardless of how much content exists, so an N+1 introduced
later fails the build.

## Accessibility

Skip link, visible focus rings on every interactive element (never removed),
ARIA labelling on landmarks and icon-only controls, "(opens in a new tab)"
announcements on external links, `prefers-reduced-motion` support that drops
decorative movement, and a print stylesheet that strips the chrome.

## Project Structure

```
Portfolio_Django_/
├── portfolio_project/      # Settings, URLs, WSGI/ASGI, env loader
├── portfolio/              # The app
│   ├── models.py           # Skill, Project, JourneyEntry, Education,
│   │                       # Certification, ProfessionalSkill, ContactMessage
│   ├── views.py            # home, ProjectDetailView, robots.txt
│   ├── sitemaps.py
│   ├── context_processors.py   # Site identity for every template
│   ├── management/commands/     # populate_portfolio, make_og_image
│   ├── tests.py / test_regressions.py
├── templates/              # base, components, pages, 404, 500
├── static/                 # css/, js/, img/, files/
├── media/                  # Admin-uploaded project screenshots
└── manage.py
```

## License

MIT License
