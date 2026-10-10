# Developer Portfolio

A database-driven developer portfolio built with Django — content is managed
through the admin, not by editing templates.

Live sections: hero, about, featured projects (with a page per project),
technical skills, journey timeline, education, certifications, professional
skills, and a contact form that stores messages.

## Tech Stack

- **Backend**: Python 3.13 (pinned in `.python-version`), Django 5
- **Frontend**: Hand-written HTML, CSS and vanilla JavaScript — no framework, no build step
- **Database**: SQLite by default; PostgreSQL when `DATABASE_URL` is set
- **Static files**: WhiteNoise, with hashed + compressed assets in production
- **Images**: Pillow (project screenshots, generated link-preview card)

## Design

"Editorial noir": near-black and red, huge condensed display type, and a
spotlight portrait with a computer-vision detection box drawn over the face.
The visual layer is a small, explicit design system rather than a CSS
framework:

| File | Responsibility |
|------|----------------|
| `static/css/variables.css` | **Every colour in the project.** Design tokens for colour, type, spacing, shape, motion and the film-grain texture |
| `static/css/reset.css` | Minimal normalisation |
| `static/css/base.css` | Element typography, page scaffolding, section headings, grain overlay |
| `static/css/components.css` | Header and navigation, buttons, chips, project cards, form, alerts, footer |
| `static/css/sections.css` | Every page section in order — hero, ticker, about, projects, process, skills, journey, credentials, contact — then the project page and the error page, each with its own breakpoints |
| `static/css/motion.css` | Keyframes, the hero intro, scroll reveals and the reduced-motion switch |
| `static/css/responsive.css` | Mobile navigation, page-wide small-screen overrides and print |

The home page is one Django partial per section, in `templates/portfolio/sections/`.

Rules the test suite enforces:

- **Colour lives in one file.** No hex or `rgba()` value may appear outside
  `variables.css`, every `--color-*` token must exist in both themes, and the
  `--color-stage*` tokens must be identical in both.
- **Every stylesheet on disk must be linked.** Orphaned CSS fails the build.
- **No CSS custom properties inside media queries** — `@media (min-width: var(--x))`
  is invalid and silently discards the whole at-rule.
- **Motion is safe by default.** Every hidden-before-reveal state is scoped
  under `.motion-ready`, keyframes animate only `transform` and `opacity`, and
  `prefers-reduced-motion` switches animation off.

Typography is Anton for display type and numbers, Archivo for prose, and IBM
Plex Mono for labels and metadata. Type scales fluidly with `clamp()`, so
there are no per-breakpoint heading overrides.

The red has two values on purpose: `#ef3b42` for red text and `#d61f26` for
button fills. The reference red, `#e5292f`, measures about 4.5:1 against both
black and white — right on the accessibility line — so it is used for neither.

### Theming

Dark is the default for every visitor. The operating-system preference is
deliberately not followed: the design, and the portrait, are built for black.
The toggle switches to a light "paper" theme and the choice is stored.
`static/js/theme.js` is loaded **synchronously in `<head>`** so the stored
choice applies before first paint.

The navigation, the hero and the project page's title band are "stages": they
stay dark in the light theme and use only the `--color-stage*` and
`--color-on-stage*` tokens.

### Motion

`theme.js` adds `.motion-ready` to `<html>` before first paint unless the
visitor asked for reduced motion; `motion.css` scopes every hidden state under
it. `static/js/motion.js` adds the detection-box counter, scroll reveals, the
stats count-up and the hero parallax. If `motion.js` has not run within three
seconds, `theme.js` withdraws the class, so content can never stay invisible.
With JavaScript off, the page is static and complete.

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
| `JourneyEntry` | The Journey timeline **and its nav link** are hidden entirely when there are no entries. Dates render as month + year, so entries only need to be accurate to the month |
| `ContactMessage` | Read-only in the admin; submissions are stored, not emailed |

`python manage.py populate_portfolio` reloads the seed content. It is
idempotent — every record is matched on its natural key and updated in place —
and `--prune` removes skills, professional skills, certifications and education
records that are no longer in the seed data. Pruning matters whenever a natural
key itself changes: records are matched on (name, category), (name, issuer) and
(institution, degree), so a rename inserts a new row and strands the old one.

## Images

```bash
python manage.py make_portrait design/photos/1000256303.jpg
python manage.py make_og_image --photo design/photos/1000256302.jpg
```

`make_portrait` exports the hero portrait as `static/img/portrait-480.webp`
and `static/img/portrait-768.webp`, the two widths the hero's `srcset` serves.
`make_og_image` renders `static/img/og-image.png` (1200×630) from the site
identity settings, with the headshot and the same detection box on the right,
so the card shared to LinkedIn or Slack cannot drift out of date when the
name, role or tagline changes. The original photos live in `design/`, which is
git-ignored (everything under `static/` is published); only the generated
files are committed.

The `og:image` tags are emitted only when the file actually exists, and always
as absolute URLs — scrapers do not resolve relative ones.

`robots.txt` and `sitemap.xml` are served from the app; the sitemap covers the
home page and every project.

## Portfolio assistant

A chat widget ("Ask about Anand") answers visitors' questions from the site's
own data, using Gemini 3.5 Flash-Lite through Google's official
`google-genai` SDK.

- `portfolio/chatbot.py` builds the profile on every request (identity, the
  About text, skills, projects, journey, education, visible certifications
  and professional skills) in a fixed order, so Gemini can cache the system
  prompt, then asks Gemini. The phone number is deliberately left out.
- `POST /api/chat/` (CSRF-protected JSON) validates the question (500
  characters at most, with up to the last three exchanges as history),
  limits each visitor to 8 questions per 10 minutes and 40 per day, and
  returns the reply. When Google's own rate limit is hit it answers 503 with
  a "busy" message.
- Every answer is saved as a `ChatLog`, read-only in the admin. Logs older
  than 90 days are deleted automatically when a new one is saved.
- The widget (`templates/components/chatbot.html`, `static/js/chatbot.js`,
  `static/css/chatbot.css`) shows replies as text with a small safe Markdown
  subset; only `https://`, `mailto:` and site links become links. Its
  footnote tells visitors that questions are processed by Google Gemini.
- With no `GEMINI_API_KEY` set, the widget is hidden and the endpoint
  returns 503, so local development and the tests need no key.

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | empty | Gemini API key from Google AI Studio. Turns the assistant on. Secret: environment only |
| `CHATBOT_MODEL` | `gemini-3.5-flash-lite` | Model used for answers |

The key runs on Gemini's free tier: no billing, Google's rate limits apply,
and Google may use prompts to improve its products. In production start
gunicorn with `--threads 4` so a chat request never blocks page loads.

## Contact alerts

Each new contact message is saved first and then emailed to the owner by
`portfolio/notifications.py`, through Resend's HTTP API. Render's free plan
blocks outbound SMTP (ports 25, 465 and 587), so Gmail SMTP and Django's
SMTP backend cannot work there.

- The email names the visitor and includes their email, subject, message and
  a link to the message in the admin; pressing Reply answers the visitor.
- With no `RESEND_API_KEY` set, nothing is sent, so local development and the
  tests need no key.
- A failed alert is logged and never shown to the visitor: the message is
  already in the database.

Setup: create a free account at [resend.com](https://resend.com) **with the
address that should receive the alerts**, create an API key with "Sending
access", and set it as `RESEND_API_KEY`. Until a domain is verified in Resend,
the test sender `onboarding@resend.dev` can only send to the account's own
address, so `CONTACT_ALERT_TO` must stay equal to it.

| Variable | Default | Description |
|----------|---------|-------------|
| `RESEND_API_KEY` | empty | Resend API key. Turns the alerts on. Secret: environment only |
| `CONTACT_ALERT_TO` | `SITE_EMAIL` | Where alerts are sent |
| `CONTACT_ALERT_FROM` | `Portfolio <onboarding@resend.dev>` | Sender; change after verifying a domain in Resend |

## Environment Variables

Settings are read from the environment; a `.env` file at the project root is
loaded automatically, and real environment variables take precedence over it.

### Required in production

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | insecure dev key | Django secret key. Mandatory when `DEBUG=False` |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` in debug | Comma-separated allowed hosts |
| `SITE_URL` | empty | Absolute site URL, used for canonical tags and `og:image` |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | empty | e.g. `postgres://user:pass@host:5432/dbname`. Parsed by `dj-database-url` with persistent connections (`conn_max_age=600`); SSL is required when `DEBUG=False`. When unset, the project uses `db.sqlite3` at the project root |

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
availability marker in the navigation and the contact section, `SITE_PHONE`
set to an empty value drops the phone row from the contact section, and the
résumé button appears only once the file at `RESUME_STATIC_PATH` actually
exists — so the site never ships a download link that 404s.

### Keeping the site, the résumé and LinkedIn in step

Site copy, skills, project technologies and the generated preview card are
derived from two sources: the résumé in `static/files/` and the LinkedIn
profile (experience, the journey dates, certifications and the About text).
A recruiter usually has all three open at once, so they need to agree. When any
of them changes:

1. Update `SITE_ROLE` / `SITE_DESCRIPTION` / `SITE_FOCUS` if the positioning moved.
2. Update the seed data in `portfolio/management/commands/populate_portfolio.py`
   and re-run `python manage.py populate_portfolio --prune` (`--prune` removes
   skills, professional skills, certifications and education records that are no
   longer in the seed, so a rename does not leave both versions on the page).
   To update the live site, run it with `DATABASE_URL` set to the production
   database — deploys no longer run it (see Deployment).
3. Re-run `python manage.py make_og_image --photo design/photos/1000256302.jpg`.

Two résumé variants are kept in `static/files/`:
`Resume_Anand_Final_ATS_Python_AI_ML.pdf` (served — "Python Developer | AI/ML
Enthusiast", matching how the site positions itself) and
`Anand_SE_FSD_Dev_Final.pdf` ("Software Engineer | Full Stack Developer"). Only
the one named by `RESUME_STATIC_PATH` is linked, but **every file under
`static/` is collected and publicly reachable by URL**, linked or not.

> **Known divergences** between the served PDF and this site, all in the PDF's
> favour to fix:
>
> - The PDF has no Experience section, so the Yangtso Four Labs AI internship
>   is missing from it entirely.
> - B.Tech CGPA reads 6.84; LinkedIn and this site say 6.82.
> - Class XII reads "Sree Narayana Guru Higher Secondary School — CGPA: 8.8";
>   LinkedIn gives "SNGHSS Chempazhanthy — 88%" (a percentage, not a CGPA).
> - The PDF lists 3 certifications; LinkedIn and this site carry 8, and the SQL
>   course's issuer differs (Skill Nation vs LinkedIn).

`RESUME_STATIC_PATH` is asserted by the test suite to point at a file that
really exists, so swapping the PDF for one with a different filename fails the
build rather than silently hiding the download button.

## Deployment

The live site runs on **Render** (web service, Singapore region) with a
**Neon** PostgreSQL database in the same region. Render deploys every push to
`main`; set its auto-deploy to **After CI checks pass** so the GitHub Actions
tests (see [Tests](#tests)) gate each deploy.

| Render setting | Value |
|----------------|-------|
| Build command | `./build.sh` (installs dependencies, `collectstatic`, `migrate`) |
| Start command | `gunicorn portfolio_project.wsgi:application --threads 4` |
| Environment | `DATABASE_URL` (Neon **pooled** connection string), `SECRET_KEY`, `ALLOWED_HOSTS`, `SITE_URL`, `CSRF_TRUSTED_ORIGINS`, `GEMINI_API_KEY`, `RESEND_API_KEY` |

Environment changes only take effect on the next deploy — use **Save, rebuild
and deploy**, not plain Save.

`build.sh` deliberately does **not** run `populate_portfolio`. It used to, which
meant every push reset any admin edit to a seeded record back to the seed. Seed
a new database once by hand, and re-run it only when the seed data changes:

```bash
DATABASE_URL='<neon pooled string>' python manage.py migrate
DATABASE_URL='<neon pooled string>' python manage.py populate_portfolio
DATABASE_URL='<neon pooled string>' python manage.py createsuperuser
```

On Render's free plan the service sleeps after about 15 minutes without
traffic, so the first request after that takes 30–60 seconds.

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
  `.gitignore`) and attached by `populate_portfolio`. The images have to be in
  the repo *and* referenced by the seed, or the cards come up blank.

`WHITENOISE_AUTOREFRESH` defaults to `True` so an image uploaded through the
admin appears without a restart. Set it to `False` to trade that for slightly
less filesystem work per request.

Render's filesystem is ephemeral, which is why the database lives in Neon.
Media has no such home yet: images uploaded through the admin are lost on the
next deploy or sleep, and only the committed seed screenshots come back. Commit
new screenshots to `media/projects/` and reference them from the seed, or move
media to object storage.

## Tests

```bash
python manage.py test
```

272 tests across five files:

- `portfolio/tests.py` — the feature suite: models, views, form validation,
  and every section's rendering and empty state.
- `portfolio/test_regressions.py` — tests that pin previously-fixed bugs and
  the properties the design system relies on: admin permissions, skill
  grouping, seed idempotency, **constant query counts**, static-asset lints,
  colour-token discipline, crawler endpoints, link-preview tags, theme
  behaviour, nav-anchor resolution, honeypot spam protection, résumé wiring,
  project-image delivery and error pages.
- `portfolio/test_redesign.py` — the editorial noir design: navigation off the
  home page, the hero and its portrait files, the ticker, the process and
  credentials sections, the empty-database page, motion safety, and the
  portrait and link-preview commands.
- `portfolio/test_chatbot.py` — the portfolio assistant: the profile and
  system prompt, the request sent to Gemini (with a fake client, so no key or
  network is needed), validation, rate limiting, logging, the admin and the
  widget's safety rules.
- `portfolio/test_notifications.py` — the contact alert: the email's
  contents, the request sent to Resend, and that a failed alert never breaks
  the contact form.

GitHub Actions (`.github/workflows/tests.yml`) runs the Django system checks
with production settings, `collectstatic`, a missing-migrations check and the
whole suite on every pull request and every push to `main`.

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
├── portfolio_project/      # Settings, URLs, WSGI/ASGI, env loader, middleware
├── portfolio/              # The app
│   ├── models.py           # Skill, Project, JourneyEntry, Education,
│   │                       # Certification, ProfessionalSkill, ContactMessage
│   ├── views.py            # home, ProjectDetailView, robots.txt
│   ├── sitemaps.py
│   ├── context_processors.py    # Site identity for every template
│   ├── templatetags/            # handle, ticker_skills filters
│   ├── management/commands/     # populate_portfolio, make_portrait, make_og_image
│   ├── tests.py / test_regressions.py / test_redesign.py
├── templates/              # base, components, portfolio/sections/, pages, 404, 500
├── static/                 # css/, js/, img/, files/
├── media/                  # Admin-uploaded project screenshots
├── design/                 # Original photos and mockups (git-ignored)
└── manage.py
```

## License

MIT License
