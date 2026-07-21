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

## Deploying with Docker (EC2)

The app connects to an external RDS Postgres instance — no database container is included.

1. On the EC2 instance, install Docker and the Compose plugin, then clone this repo.
2. Create a `.env` file (see `.env.example`) with production values:
   - `DEBUG=False`
   - `ALLOWED_HOSTS=<ec2-public-dns-or-domain>`
   - `SECRET_KEY=<a real production secret key>`
   - `DB_HOST=<your-rds-endpoint>` and the matching `DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_PORT`
   - Ensure the RDS security group allows inbound connections from the EC2 instance.
3. Build and start the stack:
   ```bash
   docker compose up -d --build
   ```
   This runs migrations and `collectstatic` automatically on startup, then serves the app via Gunicorn behind an Nginx container on port 80.
4. Check logs / status:
   ```bash
   docker compose logs -f
   docker compose ps
   ```
5. To redeploy after a code change:
   ```bash
   git pull
   docker compose up -d --build
   ```

Make sure the EC2 instance's security group allows inbound traffic on port 80 (and 443 if you add TLS later).
