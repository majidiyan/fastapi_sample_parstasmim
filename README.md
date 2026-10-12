# FastAPI + PostgreSQL (Docker Compose)

## Requirements

- Docker Desktop with the WSL 2 backend enabled
- Git (if cloning this repository)

## 1. Configure environment variables

In the repository root, copy the example file:

PowerShell:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set three different secret values:
- `POSTGRES_PASSWORD`: a long random password made of letters/numbers (hex is convenient for a database URL).
- `SECRET_KEY`: a separate, long random secret for JWT signing.
- `ADMIN_PASSWORD`: the password for the initial `admin` account.

Do not commit `.env` to GitHub. It is excluded by `.dockerignore`, but also add it to `.gitignore` if it is not already ignored.

## 2. Start the containers

Run these commands in PowerShell from the repository root:

```powershell
docker compose config
docker compose up --build -d
docker compose ps
```

The FastAPI container waits for PostgreSQL's health check before starting.

## 3. Open the API

Visit <http://localhost:8000/docs>.

The initial account username is `admin`; its password is the value you set as `ADMIN_PASSWORD` in `.env`.

## Useful commands

```powershell
docker compose logs -f fastapi
docker compose logs -f db
docker compose restart fastapi
docker compose down
```

To open PostgreSQL's shell:

```powershell
docker compose exec db psql -U ali -d mydb
```

Inside psql, run `SELECT current_database(), current_user;` and then `\\q` to exit.

**Data warning:** PostgreSQL data is stored in the named volume `postgres_data`. `docker compose down` keeps it. Do not run `docker compose down -v` unless you intend to delete the database volume.

## Notes

- Inside Docker, the application connects to PostgreSQL using hostname `db`, not `localhost`.
- Tables and initial roles/admin user are created by `app/main.py` when the API starts.
- This project currently uses `Base.metadata.create_all()`; Alembic migrations are not automatically applied by this Compose setup.
