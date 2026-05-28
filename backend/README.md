# Backend Setup

## Install
pip install -r requirements.txt

## Run
python manage.py migrate
python manage.py runserver

## Notes
- The demo data seeds automatically on migrate.
- The backend serves JSON only.
- Default API base: `http://127.0.0.1:8000/api`