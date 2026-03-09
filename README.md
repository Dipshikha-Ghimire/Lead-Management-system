# LMS Lead Management System

Web-based lead and admission workflow system built with Django.

## Overview

This project manages the admission lifecycle for an educational institution, including:

- Department and program setup
- Lead capture and counselor assignment
- Follow-up tracking
- Application and entrance exam flow
- Scholarship decisions
- Payment tracking
- User authentication (login/signup/logout)
- Password reset flow

The main app is `core`, mounted in the `lms` Django project.

## Tech Stack

- Python
- Django 6.0
- MySQL (configured in `lms/lms/settings.py`)
- HTML/CSS/JavaScript templates and static assets

## Current Database Configuration

`lms/lms/settings.py` is currently configured for MySQL:

- Database name: `lead_management_system`
- User: `root`
- Password: `lead`
- Host: `localhost`
- Port: `3306`

Update these values before running if your local setup is different.

## Project Structure

```text
README.md
lms/
	manage.py
	core/
		models.py
		views.py
		forms.py
		urls.py
		admin.py
		templates/core/
		static/core/
		migrations/
	lms/
		settings.py
		urls.py
```

## Core Modules

Implemented models in `lms/core/models.py`:

- `Department`
- `Program`
- `Staff`
- `Lead`
- `FollowUp`
- `Application`
- `EntranceExam`
- `Scholarship`
- `Payment`

These are registered in Django admin (`lms/core/admin.py`) with custom list/search/filter support for leads.

## URL Endpoints

Defined in `lms/core/urls.py`:

- `/` -> homepage
- `/login/`
- `/signup/`
- `/logout/`
- `/password-reset/`
- `/password-reset/done/`
- `/password-reset-confirm/<uidb64>/<token>/`
- `/password-reset-complete/`
- `/dashboard/`
- `/leads/`
- `/applications/`
- `/exams/`
- `/finance/`
- `/settings/`
- `/admin/` (from project urls)

## Local Setup (Windows)

1. Go to the Django project folder (where `manage.py` exists):

```powershell
cd lms
```

2. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install Django mysqlclient
```

4. Apply migrations:

```powershell
python manage.py migrate
```

5. Create an admin user:

```powershell
python manage.py createsuperuser
```

6. Run the development server:

```powershell
python manage.py runserver
```

Open:

- App: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

## Password Reset Email Behavior

This project uses Django console email backend:

- `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`

Password reset emails are printed in terminal during development.

## Running Tests

From `lms/`:

```powershell
python manage.py test
```

## Notes

- `db.sqlite3` exists in the repository, but active settings point to MySQL.
- For production, use environment variables for secrets and database credentials.
