# LMS Lead Management System

A Django-based lead and admissions workflow platform for institutions. The system supports multi-role access (admin, staff, lead), end-to-end lead capture, application review, exam and scholarship tracking, and core payment/notification flows.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Core Features](#core-features)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Domain Model Summary](#domain-model-summary)
6. [Role and Access Model](#role-and-access-model)
7. [Setup and Installation (Windows)](#setup-and-installation-windows)
8. [Run the Application](#run-the-application)
9. [Database and Migrations](#database-and-migrations)
10. [Useful Management Commands](#useful-management-commands)
11. [Static and Media Files](#static-and-media-files)
12. [Password Reset and Email](#password-reset-and-email)
13. [Known Notes](#known-notes)
14. [Recommended Improvements](#recommended-improvements)

## Project Overview

This repository contains a Django project named `lms` with a primary application `core`. It is designed to manage the admissions funnel:

- Capture prospective student leads
- Track follow-ups and status progression
- Create and process program applications
- Record exam outcomes and scholarship decisions
- Track payments and internal notifications

The project includes both server-rendered pages and JSON-based endpoints for dynamic frontend interactions.

## Core Features

- Authentication: login, signup, logout, password reset and change
- Dashboard analytics:
	- lead counts and growth
	- application funnel metrics
	- verified revenue summary
	- source distribution
- Lead lifecycle management:
	- create/update/delete lead records
	- assign counselors
	- track status and follow-up dates
	- upload education documents
- Application management:
	- create/update/delete applications
	- approve/reject/restore flows
	- exam metadata and scholarship fields
- Course catalog management:
	- departments
	- programs
- Notifications API for unread/read state management
- Separate dashboards for admin/staff and lead users

## Tech Stack

- Backend: Django
- Language: Python
- Database: MySQL (configured in settings)
- Templates: Django Templates
- Static assets: CSS/JS under `core/static/core`
- Media uploads: local filesystem (`media/lead_documents/`)

## Project Structure

```text
django/
|-- README.md
|-- package.json
`-- lms/
		|-- manage.py
		|-- core/
		|   |-- models.py
		|   |-- views.py
		|   |-- forms.py
		|   |-- urls.py
		|   |-- middleware.py
		|   |-- signals.py
		|   |-- templates/core/
		|   `-- static/core/
		|-- lms/
		|   |-- settings.py
		|   |-- urls.py
		|   |-- asgi.py
		|   `-- wsgi.py
		|-- media/
		`-- db.sqlite3
```

Important: run Django commands from the `lms/` directory (the one containing `manage.py`).

## Domain Model Summary

Primary entities in `core/models.py`:

- `Department`: academic departments
- `Program`: programs linked to departments, with fees and duration
- `Staff`: counselor/staff profiles linked to Django users
- `Admin`: admin/manager profiles linked to Django users
- `Lead`: prospective student profile and onboarding details
- `FollowUp`: communication history for lead follow-up
- `Application`: program application with status and exam/scholarship fields
- `EntranceExam`: one-to-one exam record for an application
- `Scholarship`: scholarship decision linked to an entrance exam
- `Payment`: payment records by lead/application
- `Notification`: internal notification records

## Role and Access Model

Role checks are handled via Django groups and middleware:

- `admin`: full access
- `staff`: restricted from course-management routes and routed to staff dashboard
- `lead`: constrained to lead-focused routes (`/lead/...`), onboarding, and personal flow

Middleware enforcing behavior:

- `LeadGroupAccessMiddleware`
- `StaffGroupAccessMiddleware`

## Setup and Installation (Windows)

### 1. Create and activate virtual environment

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install Python dependencies

If you maintain a requirements file:

```powershell
pip install -r requirements.txt
```

If not, install required packages manually (minimum):

```powershell
pip install django mysqlclient pillow
```

### 3. Configure MySQL

Current database settings in `lms/lms/settings.py` use:

- Engine: `django.db.backends.mysql`
- Database: `lead_management_system`
- User: `root`
- Password: `lead`
- Host: `localhost`
- Port: `3306`

Create the MySQL database before migrating:

```sql
CREATE DATABASE lead_management_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

If your local credentials differ, update `lms/lms/settings.py` accordingly.

## Run the Application

From the `lms/` directory:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Application URLs:

- Main site: `http://127.0.0.1:8000/`
- Django admin: `http://127.0.0.1:8000/admin/`

## Database and Migrations

Run migrations:

```powershell
python manage.py makemigrations
python manage.py migrate
```

Apply only the `core` app (if needed):

```powershell
python manage.py makemigrations core
python manage.py migrate core
```

## Useful Management Commands

```powershell
# Run tests
python manage.py test

# Check project configuration
python manage.py check

# Open Django shell
python manage.py shell

# Collect static files (production-oriented step)
python manage.py collectstatic
```

## Static and Media Files

- Static URL: `/static/`
- Extra static directory: `lms/core/static`
- Static collect target: `lms/staticfiles`
- Media URL: `/media/`
- Media root: `lms/media`

Lead documents are uploaded to:

- `lms/media/lead_documents/`

## Password Reset and Email

Password reset views are wired through custom templates in `core/templates/core/` and `core/templates/registration/`.

Email backend is configured as console backend by default:

- `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`

This prints reset emails in the server console during development.

## Known Notes

- Use lowercase Django group names (`admin`, `staff`, `lead`) consistently to match role checks.
- Ensure `Pillow` is installed for image/file field compatibility.
- Avoid adding `django.contrib.auth.urls` under `/accounts/` in this project to prevent naming/template conflicts with existing auth routes.

## Recommended Improvements

- Add and maintain a pinned `requirements.txt`
- Move sensitive DB credentials to environment variables
- Add automated tests for role-based permissions and API endpoints
- Add CI checks (lint, test, migration validation)
- Add deployment configuration (e.g., Gunicorn + Nginx + environment-specific settings)

