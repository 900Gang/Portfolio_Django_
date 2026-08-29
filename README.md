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

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Debug mode (True/False) |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts |

## License

MIT License
