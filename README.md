# Breathe ESG Prototype

Breathe ESG Prototype is a full-stack demo for reviewing and approving emissions data. The backend normalizes seeded SAP, utility, and travel records through a Django REST API, and the frontend presents an analyst dashboard built with React and Vite.

The project is designed as a realistic ESG review workflow:

- ingest source data from multiple formats
- normalize records into a common emissions model
- flag suspicious rows for review
- approve, reject, or lock records from the dashboard
- keep a lightweight audit trail in the database

## Tech Stack

- Backend: Django, Django REST Framework, SQLite
- Frontend: React, Vite
- API style: JSON over `/api/`

## How It Works

The backend exposes a small set of authenticated JSON endpoints for login, tenant selection, dashboards, and individual record updates. The frontend uses those endpoints to load the dashboard, display summary metrics, filter records, and submit review actions.

Demo data is automatically seeded on migration. The seed includes:

- demo tenants
- seeded users for analyst and auditor access
- SAP-like fuel and procurement rows
- utility billing rows
- travel rows for flights, hotels, and ground transport

The frontend also auto-signs in with the seeded analyst account so the dashboard opens immediately.

## Repository Layout

```text
backend/
	manage.py
	breathe_esg/          Django project settings and routing
	ingestion/            API, models, auth helpers, seeding, serializers
	db.sqlite3            Local SQLite database used by the demo

frontend/
	src/
		App.jsx             Root React entry point
		pages/Dashboard.jsx Main dashboard and API integration
		styles.css          UI styling
```

## Main Features

- secure demo login and registration
- tenant-aware dashboard
- summary cards for records, flagged items, approved items, and total CO2e
- searchable and filterable review queue
- record detail panel with raw payload inspection
- approve, flag, and reject actions that update the database

## Demo Credentials

The app seeds demo users during migration.

- Analyst: `analyst@breatheesg.com`
- Auditor: `auditor@breatheesg.com`
- Password: `BreatheESG2026!`

The frontend auto-uses the analyst account by default after the backend is running.

## Setup

### Prerequisites

- Python 3.10+ with `pip`
- Node.js 16+ with `npm`

### 1. Start the backend

```powershell
cd backend
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

If you already have a virtual environment at the repo root, activate that instead of creating a new one.

### 2. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, usually `http://localhost:5173`.

## API Overview

The backend serves JSON endpoints under `/api/`.

- `GET /api/health/` - health check
- `POST /api/auth/login/` - obtain a demo token
- `POST /api/auth/register/` - create a demo user
- `GET /api/auth/me/` - current user info
- `GET /api/tenants/` - list tenants
- `GET /api/dashboard/?tenant=...` - dashboard summary
- `GET /api/records/?tenant=...` - record list with filters
- `PATCH /api/records/<id>/` - update review status

## Configuration

The frontend reads `VITE_API_BASE_URL` if you want to point it at a different backend.

Example:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

If unset, it defaults to `http://127.0.0.1:8000/api`.

## Deployment Notes

- The demo uses SQLite by default for simplicity.
- `backend/ingestion/signals.py` seeds demo data after migrations run.
- `render.yaml` is included for deployment configuration.

## Troubleshooting

- If the frontend shows an auth error, make sure the backend is running and `python manage.py migrate` has been executed.
- If you want to reset the demo database, delete `backend/db.sqlite3` and run migrations again.
- If the frontend cannot reach the API, confirm the backend is running on port `8000`.

## Further Reading

- Backend API implementation: [backend/ingestion/views.py](backend/ingestion/views.py)
- Data seeding logic: [backend/ingestion/seed.py](backend/ingestion/seed.py)
- Dashboard UI: [frontend/src/pages/Dashboard.jsx](frontend/src/pages/Dashboard.jsx)
