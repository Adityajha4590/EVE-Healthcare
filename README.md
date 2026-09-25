# EVE Healthcare

Backend service for diagnostic test bookings and simulated payments.

**Current Scope:** Foundation + Authentication (Phases 1–2).
Booking, payment, and webhook functionality are planned for later phases and are not yet implemented.

## Quick Start

### Using Docker Compose

```bash
docker compose up -d
docker compose exec app alembic upgrade head
```

The API will be available at `http://localhost:8000`.

### Local Development

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[dev]"

# Copy environment config
copy .env.example .env

# Start PostgreSQL (via Docker or locally)
docker compose up db -d

# Run migrations
alembic upgrade head

# Start the dev server
uvicorn app.main:app --reload
```

## API Endpoints

### Health

| Method | Path      | Auth     | Description         |
|--------|-----------|----------|---------------------|
| GET    | `/health` | No       | Health check        |

### Authentication

| Method | Path           | Auth     | Description              |
|--------|----------------|----------|--------------------------|
| POST   | `/auth/signup`  | No       | Register a new user      |
| POST   | `/auth/login`   | No       | Obtain a JWT access token|
| GET    | `/auth/me`      | Bearer   | Get current user profile |

#### Signup

```
POST /auth/signup
Content-Type: application/json

{"email": "user@example.com", "password": "securepassword"}
```

Response (201):
```json
{"id": "...", "email": "user@example.com", "is_active": true, "created_at": "..."}
```

#### Login

```
POST /auth/login
Content-Type: application/json

{"email": "user@example.com", "password": "securepassword"}
```

Response (200):
```json
{"access_token": "eyJ...", "token_type": "bearer"}
```

#### Protected Endpoint

```
GET /auth/me
Authorization: Bearer <token>
```

Response (200):
```json
{"id": "...", "email": "user@example.com", "is_active": true, "created_at": "..."}
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

```bash
pytest
```

## Environment Variables

| Variable                         | Description                    | Default                  |
|----------------------------------|--------------------------------|--------------------------|
| `DATABASE_URL`                   | PostgreSQL connection string   | `postgresql+psycopg2://...` |
| `JWT_SECRET_KEY`                 | Secret for signing JWTs        | *(change in production)* |
| `JWT_ALGORITHM`                  | JWT signing algorithm          | `HS256`                  |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`| Token expiry in minutes        | `30`                     |
| `DEBUG`                          | Enable debug mode              | `false`                  |

See `.env.example` for all variables.

## Project Structure

```
app/
├── main.py            # Application factory
├── config.py          # Settings from environment
├── database.py        # SQLAlchemy engine and session
├── dependencies.py    # FastAPI dependency injection (DB + auth)
├── core/
│   ├── exceptions.py  # Domain exception classes
│   ├── logging.py     # Structured logging setup
│   └── security.py    # Password hashing + JWT utilities
├── models/
│   └── user.py        # User ORM model
├── schemas/
│   └── auth.py        # Auth request/response schemas
├── routers/
│   ├── health.py      # Health check endpoint
│   └── auth.py        # Auth endpoints (signup, login, me)
└── services/
    └── auth.py        # Auth business logic
```
