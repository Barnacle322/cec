# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flask-based Learning Management System (LMS) for Makerspace AUCA (Bishkek, Kyrgyzstan). Manages courses, TOEFL registrations, events, teachers/staff, blog posts, and student feedback. Supports three languages: Russian (default), English, and Kyrgyz.

## Commands

### Development

```bash
# Run development server (loads .env automatically)
./start.sh

# Or manually
flask run
```

### CSS (Tailwind)

```bash
# Watch and compile CSS
npm run css

# Format HTML templates with Prettier + Tailwind plugin
npm run html
```

### Database Migrations

```bash
flask db migrate -m "description"
flask db upgrade
```

### Translations (Flask-Babel)

```bash
# Extract strings
pybabel extract -F babel.cfg -o messages.pot .

# Update existing translations
pybabel update -i messages.pot -d src/project/translations

# Compile translations
pybabel compile -d src/project/translations
```

### Linting

```bash
ruff check .
ruff format .
```

## Architecture

### Application Structure

- **`src/project/__init__.py`** — Flask app factory (`create_app`). Registers blueprints, extensions, and locale selector.
- **`src/project/main.py`** — Public-facing blueprint (`/`). All public routes including login/logout.
- **`src/project/admin.py`** — Admin blueprint (`/admin`). All admin CRUD routes; every route uses `@admin_required`.
- **`src/project/views/`** — Modular admin view files imported into `admin.py`: `course.py`, `event.py`, `feedback.py`, `people.py`, `blog.py`, `application.py`.
- **`src/project/models.py`** — All SQLAlchemy models (~945 lines).
- **`src/project/extenstions.py`** — Extension singletons (db, cache, login_manager, migrate, babel, csrf).
- **`src/project/utils/decor.py`** — `@admin_required` decorator.
- **`src/project/utils/storage.py`** — Cloudflare R2 (S3-compatible) image upload with resizing to 1280×720 JPEG.

### Multi-language Content

Content fields (names, descriptions, etc.) are stored as JSON dicts with language keys: `{"ru": "...", "en": "...", "ky": "..."}`. The active language is stored in session (default: `"ru"`). Flask-Babel handles UI string translations via `gettext`.

### Authentication

Single admin user via Flask-Login. `@admin_required` redirects non-admins to the index. CSRF protection on all forms via Flask-WTF. 30-day remember-me cookie on login.

### Key Models

| Model | Purpose |
|---|---|
| `CourseGroup` | Course categories (many `Course`s) |
| `Course` | Individual course with slug, image, timetables |
| `Timetable` | Schedule entry with multi-lang name, price, duration |
| `Teacher` / `Staff` | Personnel with bios and photos |
| `Event` / `EventType` | Calendar events with color-coded types |
| `Blog` | Articles with EditorJS JSON content |
| `Feedback` | Testimonials with verified/unverified status |
| `Toefl` | TOEFL result lookup table |
| `ToeflRegistration` / `Registration` | Form submissions |

### Frontend

Server-side rendered Jinja2 templates with Tailwind CSS 3. No JS framework — vanilla JS for AJAX (calendar loading, timetable reordering, application management). EditorJS for the blog editor. CSS source: `src/project/static/src/input.css` → compiled to `src/project/static/css/main.css`.

### Cloud Storage

Cloudflare R2 bucket `mldc-pictures`, served publicly via the custom domain `https://mldc.assets.arstan.page` (mapped to the bucket root). Configured via `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT_URL`, `R2_PUBLIC_URL` env vars. R2 uses `region="auto"` with SigV4; objects are public via the custom domain so no per-object ACL is set. Images are processed with Pillow before upload. (Previously DigitalOcean Spaces; migrated to R2.)

### Deployment

Production runs on Granian ASGI server (`granian --interface wsgi --workers 3`). Dockerized with Alpine Linux. Environment variables loaded from `.env` in development.
