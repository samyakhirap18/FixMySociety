# FixMySociety

FixMySociety is a small society maintenance portal built with Django REST Framework, React, and MySQL. Residents report and upvote issues, managers coordinate work, and workers update assigned tasks. Complaint status changes are recorded as history and residents can confirm a fix or reopen the issue.

## Roles

- **Resident:** register, report a complaint, attach an image, upvote society complaints, and verify or reopen their resolved complaints.
- **Society manager:** accounts are created in Django admin; review complaints, set priority, assign in-society workers, and update progress.
- **Maintenance worker:** managers create worker accounts; workers can see their assigned tasks and mark them in progress or resolved.

Public registration always creates a resident. Society and manager accounts are provisioned by an administrator. Backend querysets and permissions enforce society boundaries.

## Stack

- Python, Django, Django REST Framework, Simple JWT, MySQL
- React, JavaScript, Vite, Axios, React Router, CSS

## Local setup

### 1. MySQL and environment

Create a MySQL database and user, then copy `backend/.env.example` to `backend/.env` and set its values. Copy `frontend/.env.example` to `frontend/.env` if the API is not at `http://localhost:8000/api`.

### 2. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `/admin/` and add society records and manager users (choose the manager role and society). Common maintenance categories are added by the initial data migration.

### 3. Frontend

Use Node.js 22.22.2 or newer.

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal. Residents can register after an administrator has added at least one society.

## API overview

- `POST /api/auth/register/`, `POST /api/auth/login/`, `GET /api/auth/users/me/`
- `GET /api/societies/`, `GET /api/categories/`
- `GET|POST /api/complaints/`, `GET /api/complaints/{id}/`
- `POST /api/complaints/{id}/upvote/`
- `PATCH /api/complaints/{id}/assign/`, `PATCH /api/complaints/{id}/priority/`
- `PATCH /api/complaints/{id}/status/`
- `GET|POST /api/workers/`, `GET /api/dashboard/`

Status workflow: `open → assigned → in_progress → resolved → verified`. A resident who reported a resolved complaint can reopen it if the fix did not work. Upvotes are unique per resident and complaint.

Automatic priority uses severity, every three upvotes, and complaint age in weeks. Managers can adjust the resulting priority when local conditions need it.

## Tests

```powershell
cd backend
$env:DB_ENGINE='django.db.backends.sqlite3'
$env:DB_NAME=':memory:'
pytest
```

The test suite covers resident registration and login, manager and worker login, complaint creation, voting, worker creation and assignment, status progression, resident verification and reopening, and society/role access controls.

## Notes

Never commit `.env` files or real credentials. The `.env.example` files contain placeholders only. The repository's existing [LICENSE](LICENSE) remains in place.
