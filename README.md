# Breathe ESG Prototype

Short demo prototype for Breathe ESG — Django backend and Vite + React frontend.

**Prerequisites**
- **Python**: 3.10+ and `pip`
- **Node.js**: 16+ and `npm`

**Backend (Django)**

- Change to the backend folder and create/activate a virtual environment (optional if `.venv` exists):

```powershell
cd backend
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
. .venv\Scripts\Activate.ps1
```

- Install Python dependencies:

```powershell
pip install -r requirements.txt
```

- Run database migrations and start the dev server:

```powershell
python manage.py migrate
python manage.py runserver
```

**Frontend (Vite + React)**

- Install dependencies and start the dev server from the project root or `frontend` folder:

```bash
cd frontend
npm install
npm run dev
```

Open the frontend address shown by Vite (usually http://localhost:5173) and the Django API at http://localhost:8000.

**Notes & troubleshooting**
- If Django errors about missing packages (for example `dj_database_url`), ensure you ran `pip install -r requirements.txt` inside the activated virtualenv.
- If you already have a `.venv` at the repo root, activate it instead of creating a new one.
- To create an admin user:

```powershell
python manage.py createsuperuser
```

If you want, I can also add a `.env` example and more deployment notes. 
