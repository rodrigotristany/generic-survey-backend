# generic-survey-backend

A REST API for creating and running surveys, built with **FastAPI**, **SQLAlchemy 2.0 (async)**, and **PostgreSQL**.

## Stack

- **Python 3.12+**
- **FastAPI** — HTTP framework
- **SQLAlchemy 2.0 async** + **asyncpg** — async ORM + PostgreSQL driver
- **Alembic** — database migrations
- **Pydantic v2** — request/response validation
- **PyJWT** + **bcrypt** — auth tokens and password hashing

## Features

- **Admin auth** — login, logout, OTP 2FA, password recovery, JWT + server-side refresh tokens
- **User auth** — register, login, logout, OTP, password recovery (with password strength enforcement)
- **Survey management** — admins create surveys with typed questions and options; lifecycle `draft → published → closed`
- **Public survey access** — published surveys browsable by slug, no auth required
- **Response collection** — anonymous or authenticated, `start → submit` flow

## Project Structure

```
app/
├── main.py               # FastAPI app factory + router registration
├── config.py             # Pydantic settings from .env
├── database.py           # Async engine, session factory, Base
├── dependencies.py       # Depends() helpers: get_db, get_current_admin, get_current_user
├── models/               # SQLAlchemy ORM models
├── schemas/              # Pydantic request/response schemas
├── routers/              # Route handlers grouped by domain
│   ├── admin_auth.py     # /admin/auth/*
│   ├── user_auth.py      # /auth/*
│   ├── admin_surveys.py  # /admin/surveys/* (protected)
│   ├── public_surveys.py # /surveys/* (public)
│   └── responses.py      # /responses/*
├── services/             # Business logic (all DB calls live here)
└── utils/                # password hashing, JWT, OTP helpers
alembic/                  # Migrations
docs/
└── spec.md               # Full API spec, endpoint table, env vars
```

## Getting Started

### 1. Clone and set up the environment

```bash
cp .env.example .env
# Edit .env with your DATABASE_URL and SECRET_KEY
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run migrations

```bash
alembic upgrade head
```

### 4. Start the server

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive docs available at `http://localhost:8000/docs`.

## Docker Compose (recommended)

```bash
cp .env.example .env
# Set SECRET_KEY to a long random string in .env

# Local development (hot-reload, code mounted as volume)
docker compose up

# Production-like (no volume mount, no reload)
docker compose -f docker-compose.yml up --build
```

The app container runs `alembic upgrade head` automatically before starting the server.

Postgres data is persisted in the `postgres_data` Docker volume.

| Service | Port |
|---------|------|
| API | `http://localhost:8000` |
| Postgres | `localhost:5432` |

Interactive docs at `http://localhost:8000/docs`.

### Override file

`docker-compose.override.yml` is picked up automatically by `docker compose up` and enables hot-reload by mounting the project directory into the container. Remove or ignore it for CI/production builds.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENV` | Runtime environment | `local` |
| `DATABASE_URL` | `postgresql+asyncpg://...` connection string | required |
| `SECRET_KEY` | JWT signing secret | required |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |
| `OTP_EXPIRE_MINUTES` | OTP code TTL | `10` |

## API Overview

See [`docs/spec.md`](docs/spec.md) for the full endpoint reference, auth flows, and request/response shapes.

| Domain | Base path | Auth |
|--------|-----------|------|
| Admin auth | `/admin/auth` | — / Admin JWT |
| User auth | `/auth` | — / User JWT |
| Survey management | `/admin/surveys` | Admin JWT |
| Public surveys | `/surveys` | None |
| Responses | `/responses` | Optional / Admin JWT |

## Database Migrations

```bash
# After changing a model, generate a migration
alembic revision --autogenerate -m "describe change"

# Apply
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

## Tests

```bash
pytest
```
