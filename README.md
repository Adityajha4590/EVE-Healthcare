# EVE Healthcare (Phase 1 Foundation)

Backend service for diagnostic test bookings and simulated payments. 

**Current Scope (Phase 1):** This repository currently contains only the core project foundation, including FastAPI, PostgreSQL/SQLAlchemy configuration, Alembic, Docker setup, structured logging, and base testing structure. 
*Note: Business logic including authentication, booking, payments, and webhooks are planned for later phases and are not yet implemented.*
## Quick Start

### Using Docker Compose

```bash
docker compose up -d
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

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

```bash
pytest
```

## Project Structure

```
app/
├── main.py            # Application factory
├── config.py          # Settings from environment
├── database.py        # SQLAlchemy engine and session
├── dependencies.py    # FastAPI dependency injection
├── core/              # Cross-cutting: logging, exceptions
├── models/            # SQLAlchemy ORM models
├── schemas/           # Pydantic request/response schemas
├── routers/           # HTTP route handlers (thin)
└── services/          # Business logic layer
```
