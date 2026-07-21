# Starlet Fitness Backend

Django REST API backend for Starlet Fitness.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root with the required environment variables (database credentials, secret key, etc.).

## Running

```bash
python manage.py migrate
python manage.py runserver
```
