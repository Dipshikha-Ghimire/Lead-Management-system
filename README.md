# Lead-Management-system
lead management system
# Project: lms (Django)

Overview
--------

This repository contains a small Django project named "lms" (Learning Management System) using SQLite for local development. It includes a single app, `core`, basic models and views, and the standard Django project layout (`manage.py`, `lms/`, `core/`).

Quick start (Windows)
----------------------

- Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # or use activate.bat for cmd
```

- Install dependencies (if you have a `requirements.txt`) or install Django directly:

```powershell
pip install -r requirements.txt
# or
pip install Django
```

- Apply migrations and create a superuser:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

- Run the development server:

```powershell
python manage.py runserver
```

Access the site at `http://127.0.0.1:8000/` and the admin at `http://127.0.0.1:8000/admin/`.

Running tests
-------------

Run the Django test suite with:

```powershell
python manage.py test
```

Project structure
-----------------

- `manage.py`: Django management script.
- `db.sqlite3`: SQLite database used for development.
- `lms/`: Django project configuration (settings, urls, wsgi, asgi).
- `core/`: Main app for the project (models, views, admin, migrations).

Notes
-----

- This project uses SQLite by default. For production use, switch to PostgreSQL or another production-ready DB and update `lms/settings.py`.
- If there is no `requirements.txt`, create one with `pip freeze > requirements.txt` after installing required packages.
- To inspect the models and admin configuration, see the `core` app files: `core/models.py` and `core/admin.py`.

Next steps
----------

- Run the migrations and start the server locally.
- Create initial data or a fixtures file if needed.
- Consider adding a `requirements.txt`, Dockerfile, and CI configuration for reproducible builds.

License
-------

Add a license file if this project is intended for public distribution.
