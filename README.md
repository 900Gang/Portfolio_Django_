# Developer Portfolio

A professional developer portfolio built with Django.

## Overview

This portfolio demonstrates software engineering skills through actual projects, code, and professional experience rather than being just a static visual website.

## Tech Stack

- **Backend**: Python, Django
- **Frontend**: HTML5, CSS3, JavaScript, jQuery
- **Database**: SQLite (development)
- **Version Control**: Git, GitHub

## Features

- Single-page portfolio homepage with dedicated project detail pages
- Database-driven projects, skills, education, and journey entries
- Django admin for content management
- Contact form with message storage
- Responsive design

## Project Structure

```
my_portfolio/
├── portfolio_project/     # Django project configuration
├── portfolio/             # Main Django app
├── templates/             # HTML templates
├── static/                # CSS, JavaScript, images
├── media/                 # Admin-uploaded files
├── manage.py
├── requirements.txt
└── README.md
```

## Local Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

5. Apply migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser (optional, for admin access):
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

8. Visit `http://127.0.0.1:8000/` in your browser.

## Environment Variables

Settings are read from the environment; a `.env` file at the project root is
loaded automatically, and real environment variables take precedence over it.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | When `DEBUG=False` | insecure dev key | Django secret key |
| `DEBUG` | No | `False` | Debug mode (True/False) |
| `ALLOWED_HOSTS` | When `DEBUG=False` | `localhost,127.0.0.1` in debug | Comma-separated allowed hosts |
| `CSRF_TRUSTED_ORIGINS` | No | empty | Comma-separated origins, production only |
| `SECURE_SSL_REDIRECT` | No | `True` in production | Redirect HTTP to HTTPS |
| `SECURE_HSTS_SECONDS` | No | `0` | Enables HSTS when greater than zero |

`DEBUG` defaults to `False` and `SECRET_KEY` is mandatory outside debug, so a
misconfigured deployment fails at startup rather than serving insecurely.

## Tests

```bash
python manage.py test
```

`portfolio/tests.py` holds the feature suite; `portfolio/test_regressions.py`
holds tests pinning previously-fixed bugs (admin permissions, skill grouping,
seed idempotency, query counts, and static-asset lints).

## License

MIT License
