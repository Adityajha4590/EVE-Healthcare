# EVE Healthcare

Backend service for diagnostic test bookings and simulated payments, built strictly in Python.

**Current Scope:** All Phases (1-5) are complete. This includes Foundation, Authentication, Diagnostics & Bookings, Simulated Payments & Webhooks, and Rate Limiting & Retry Handling.

## Features Implemented

1. **User Management:** Secure user signup and login with JWT authentication and bcrypt password hashing.
2. **Diagnostic Catalogue:** Browse diagnostic centres and their associated diagnostic tests (paginated).
3. **Bookings:** Authenticated users can create bookings for diagnostic tests at specific centres with exact time slots.
4. **Simulated Payments:** Background tasks simulate a payment gateway network delay and a 80% success rate.
5. **Idempotent Webhooks:** Gateway callbacks are securely validated (via HMAC SHA256) and applied exactly once using database locking (`SELECT ... FOR UPDATE`).
6. **Rate Limiting:** Protects `/auth` endpoints with strict in-memory sliding windows (`slowapi`), scaling globally for all other routes.
7. **Retry Mechanisms:** Transient network errors during async webhook dispatch are intelligently retried via `tenacity` with exponential backoff.
8. **Engineering Quality:** Fully Dockerized, robust structured logging (`structlog`), OpenAPI docs, robust data validation (Pydantic), and extensive integration testing.

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
# or source .venv/bin/activate on Mac/Linux

# Install dependencies
pip install -e ".[dev]"

# Copy environment config
copy .env.example .env
# or cp .env.example .env on Mac/Linux

# Start PostgreSQL (via Docker or locally)
docker compose up db -d

# Run migrations
alembic upgrade head

# Start the dev server
uvicorn app.main:app --reload
```

## API Documentation

Once running, visit:
- Swagger UI (Interactive Docs): `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints (Highlights)

### Authentication
- `POST /auth/signup` - Register a new user
- `POST /auth/login` - Obtain a JWT access token
- `GET /auth/me` - Get current user profile (Protected)

### Catalogue & Bookings
- `GET /centres` - List active diagnostic centres
- `GET /centres/{centre_id}/tests` - List tests for a centre
- `POST /bookings` - Book an appointment (Protected)

#### Example Booking Request
```http
POST /bookings
Authorization: Bearer <token>
Content-Type: application/json

{
  "centre_id": "uuid-here",
  "test_id": "uuid-here",
  "appointment_date": "2024-12-01",
  "appointment_time": "10:00:00"
}
```

### Payments
- `POST /bookings/{booking_id}/pay` - Initiate simulated payment (Protected)
- `POST /payments/` - Alias for payment initiation (Protected, expects `{"booking_id": "uuid"}`)
- `POST /payments/webhook/` - Simulated gateway callback (Protected by HMAC)
- `POST /webhooks/payments` - Alias for the webhook callback

## Database / Schema Design

The backend utilizes PostgreSQL managed by SQLAlchemy and Alembic.

- **Users**: Central identity table storing hashed credentials and activation states.
- **DiagnosticCentres**: Physical locations where tests are performed.
- **DiagnosticTests**: The catalogue of available tests per centre, strictly enforcing a `Decimal` price.
- **Bookings**: A joining entity associating a User, Centre, and Test with a distinct temporal appointment. Snapshots the price at the time of booking.
- **Payments**: Represents the transaction attempt. State transitions (`PENDING`, `SUCCESS`, `FAILED`) are decoupled from initial request and purely driven by the Webhook.

## Security Assumptions

- **Idempotency**: Webhook payloads process serially via Postgres Row-Level Locks ensuring race conditions cannot double-confirm a single payment.
- **HMAC Signatures**: Payment callbacks strictly mandate an `X-Webhook-Signature` matching a locally signed hash of the raw body payload *before* JSON parsing, completely eliminating malicious impersonation or malformed JSON crash attacks.
- **Boundary Isolation**: No user can query or mutate another user's Bookings or Payments. `IDOR` protections are built into the foundational SQLAlchemy query clauses (`.filter(user_id=current_user.id)`).
- **In-Memory Limits**: Rate limits are bounded locally to memory to satisfy architectural constraints. In a production cluster, a remote KV store like Redis would replace this.

## Future Improvements

- Distribute rate limiting state (e.g. Redis).
- Move async simulated background tasks into a dedicated worker queue (e.g. Celery / RabbitMQ).
- Introduce a robust refund mechanism and double-entry accounting ledger.

## Testing

Run the exhaustive 81-test suite locally to verify rate-limits, idempotency, retries, and core logic:

```bash
pytest
```
