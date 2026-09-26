# FINAL SUBMISSION DOCUMENTATION

## 1. Cover / Project Information
**Project Name:** EVE Healthcare Backend
**Assignment Name:** EVE Healthcare — SDE Intern — Backend Engineering Assignment
**Technology Stack:** Python, FastAPI, SQLAlchemy, PostgreSQL, Alembic, Pydantic, PyJWT, passlib (bcrypt), Docker, Docker Compose, pytest, structlog, slowapi, tenacity
**Submission Status:** Final Submission - All requirements completed.

## 2. Executive Summary
The EVE Healthcare Backend is a RESTful API service built for managing diagnostic test bookings and processing simulated payments. The primary engineering objective of this project is to demonstrate robust backend engineering practices, API design, database schema management, and secure system design. The service provides user authentication, a catalogue for diagnostic centres and tests, a booking engine, and a simulated payment service that relies on asynchronous, idempotent webhooks to update booking statuses safely.

## 3. Requirements Analysis
Based on the `PROJECT_SPEC.md`, the assignment separates requirements into core functionality and bonus additions.

**Required:**
- User signup and login with JWT authentication
- Request validation
- Diagnostic centres, tests, and prices
- Booking creation (patient, test, centre, appointment date/time, status)
- Simulated payment processing (success/failure)
- Payment webhook handling
- Idempotent webhook processing
- Authorization and invalid request/booking handling
- Failed payment handling

**Bonus:**
- Docker and PostgreSQL integration
- Swagger/OpenAPI documentation
- Unit and integration tests
- Structured logging
- Pagination
- Rate limiting
- Retry handling

All required and bonus requirements listed above have been mapped directly to implemented features in this submission.

## 4. Requirement Compliance Matrix

| Requirement | Required/Bonus | Implementation | Relevant Files | API Endpoint | Test Coverage | Status |
|---|---|---|---|---|---|---|
| User signup | Required | Implemented | `auth.py` | `POST /auth/signup` | `test_auth.py` | Verified |
| User login | Required | Implemented | `auth.py` | `POST /auth/login` | `test_auth.py` | Verified |
| JWT auth | Required | Implemented | `security.py`, `dependencies.py` | `GET /auth/me` | `test_auth.py` | Verified |
| Request validation | Required | Implemented | `schemas/` | All Endpoints | Suite-wide | Verified |
| Diagnostic centres | Required | Implemented | `models/centre.py`, `routers/centres.py` | `GET /centres` | `test_centres.py` | Verified |
| Diagnostic tests | Required | Implemented | `models/test.py`, `routers/centres.py` | `GET /centres/{id}/tests`| `test_centres.py` | Verified |
| Booking creation | Required | Implemented | `models/booking.py`, `routers/bookings.py`| `POST /bookings` | `test_bookings.py` | Verified |
| Simulated payments | Required | Implemented | `services/payment.py` | `POST /payments/` | `test_payments.py` | Verified |
| Payment webhooks | Required | Implemented | `services/webhook.py` | `POST /payments/webhook/`| `test_webhooks.py` | Verified |
| Idempotency | Required | Implemented | `services/webhook.py` | `POST /payments/webhook/`| `test_webhooks.py` | Verified |
| Docker / Postgres | Bonus | Implemented | `Dockerfile`, `docker-compose.yml` | N/A | N/A | Verified |
| Testing | Bonus | Implemented | `tests/` | N/A | Suite-wide | Verified (88) |
| Rate limiting | Bonus | Implemented | `limiter.py` | `/auth/*` | `test_auth.py` | Verified |
| Retry handling | Bonus | Implemented | `services/payment.py` | N/A | `test_retry.py` | Verified |

## 5. System Architecture
- **Client:** Interacts with the API via standard HTTP requests.
- **FastAPI:** Handles request routing, parameter parsing, and auto-generates OpenAPI documentation.
- **Routers:** Endpoints are logically grouped into separate files (`auth.py`, `bookings.py`, `centres.py`, etc.) inside the `routers/` directory.
- **Services:** Business logic is decoupled from HTTP handlers and placed in `services/`.
- **SQLAlchemy & PostgreSQL:** The ORM handles database operations securely via parameterized queries.
- **Alembic:** Manages database schema migrations.
- **Authentication:** Managed via JWT tokens and bcrypt password hashing.
- **Payment Simulator & Background Processing:** Payments are initiated via a FastAPI `BackgroundTasks` function which sleeps to simulate latency, randomizes success/failure, and fires a POST request back to the webhook endpoint.
- **Webhook:** A dedicated route that validates HMAC signatures before processing state changes idempotently.
- **Logging & Rate Limiting:** Global middleware intercepts requests for `structlog` formatting and `slowapi` rate limiting.

## 6. Project Structure
```text
├── alembic/                  # Database migrations
├── app/
│   ├── core/                 # Core configuration, security, logging
│   ├── models/               # SQLAlchemy ORM models
│   ├── routers/              # FastAPI endpoint definitions
│   ├── schemas/              # Pydantic validation schemas
│   └── services/             # Business logic layer
│   ├── config.py             # Environment configuration mapping
│   ├── database.py           # DB connection setup
│   ├── dependencies.py       # FastAPI dependency injection (e.g., Auth, DB)
│   ├── limiter.py            # Rate limiting configuration
│   └── main.py               # Application entry point
├── tests/                    # Pytest test suite
├── .env.example              # Example environment variables
├── .gitignore                # Git exclusions
├── alembic.ini               # Alembic configuration
├── docker-compose.yml        # Docker composition file
├── Dockerfile                # Application container definition
├── pyproject.toml            # Python dependencies and build config
├── PROJECT_SPEC.md           # Assignment specification
└── README.md                 # Project documentation
```

## 7. Authentication and Authorization
- **Signup:** Accepts email and password. Normalizes the email, validates the password byte length, hashes it via bcrypt, and stores it.
- **Login:** Compares hashed credentials and returns a short-lived JWT upon success.
- **JWT:** Contains standard claims (`sub`, `exp`, `iat`) signed with `HS256`.
- **Protected Endpoints:** Routes are protected via the `get_current_user` FastAPI dependency, ensuring a valid and unexpired JWT is present.
- **User Ownership / IDOR:** Service functions (like `get_booking`) explicitly query filtering by `current_user.id` to prevent Insecure Direct Object Reference vulnerabilities.
- **JWT Secret:** Configured dynamically via environment variables (`JWT_SECRET_KEY`) to keep secrets out of source control.

## 8. Diagnostic Centre and Test Management
- Exposes GET endpoints to list paginated diagnostic centres and their associated tests.
- Uses `is_active` boolean flags for soft-deletion, ensuring historical booking references remain intact while removing inactive entities from public APIs.

## 9. Booking System
- **Creation:** A user submits a booking for a specific test at a specific centre.
- **Validation:** The service confirms the test belongs to the centre and is active. Appointment dates must not be in the past.
- **Price Snapshot:** The current price of the test is copied to the `Booking.amount` to protect historical records against future price changes.
- **Duplicate Prevention:** The database enforces a `UNIQUE` constraint on `(user_id, centre_id, test_id, appointment_date, appointment_time)` to prevent accidental double bookings.
- **Status:** Initialized as `PENDING`. Transitions to `CONFIRMED` upon successful webhook payment validation.

## 10. Payment System
- **Initiation:** The authenticated user requests a payment via `POST /bookings/{booking_id}/pay` (or the aliased `POST /payments/`).
- **State:** The payment record is created in a `PENDING` state with a unique `transaction_id`.
- **Simulated Gateway:** A background task sleeps for 1 second and then generates a webhook payload determining success or failure (80% success probability).

## 11. Webhook Security
- **Route:** Processed at `POST /webhooks/payments` (and aliased at `POST /payments/webhook/`).
- **HMAC SHA-256:** The raw request body is verified against the `X-Webhook-Signature` header using the `WEBHOOK_SECRET` before parsing JSON. This prevents payload tampering and malformed JSON crash attacks.
- **Idempotency:** A `webhook_events` table enforces unique constraint checking on `event_id`. Duplicate incoming payloads are caught via `IntegrityError` and silently returned as processed.
- **Transaction Locking:** Uses `SELECT ... FOR UPDATE` when querying the `Payment` to prevent concurrent webhook deliveries from causing race conditions on state updates.

## 12. Retry Handling
- **Tenacity:** The simulated gateway uses the `tenacity` library to manage retry logic.
- **Handling:** Outbound HTTP requests encountering transient network errors or HTTP 5xx responses are retried up to 3 times.
- **Backoff:** Uses exponential backoff (starting at 1 second, up to 10 seconds). Permanent 4xx errors are not retried.

## 13. Rate Limiting
- **slowapi:** In-memory rate limiting implementation.
- **Configuration:** Restricts authentication endpoints (`/auth/login`, `/auth/signup`) to 5 requests per minute to prevent brute-forcing. Global routes are restricted to 100 requests per minute. Returns standard HTTP 429 status codes upon limit violation.

## 14. Database Design
- **Tables:** `users`, `diagnostic_centres`, `diagnostic_tests`, `bookings`, `payments`, `webhook_events`.
- **Primary Keys:** UUID v4 strings for all tables.
- **Relationships:** Foreign keys correctly establish one-to-many relationships (e.g., `centres` to `tests`, `users` to `bookings`).
- **Monetary Fields:** Uses `Numeric(10,2)` for prices and amounts to guarantee fixed-point precision, avoiding floating point drift.
- **Constraints:** Unique indexes on `users.email`, `payments.transaction_id`, and `webhook_events.event_id`.
- **Migrations:** Fully managed by Alembic, enabling synchronized schema updates.

## 15. API Documentation
Key endpoints include:

- **POST /auth/signup**: No auth. Body: `SignupRequest`. Response: 201 `UserResponse`.
- **POST /auth/login**: No auth. Body: `LoginRequest`. Response: 200 `TokenResponse`.
- **GET /auth/me**: JWT required. Response: 200 `UserResponse`.
- **GET /centres**: No auth. Query: `page`, `page_size`. Response: 200 list of `CentreResponse`.
- **GET /centres/{id}/tests**: No auth. Response: 200 list of `TestResponse`.
- **POST /bookings**: JWT required. Body: `BookingCreateRequest`. Response: 201 `BookingResponse`.
- **POST /payments/**: JWT required. Body: `{"booking_id": "string"}`. Response: 202 `PaymentResponse`. (Compatibility alias for `/bookings/{id}/pay`).
- **POST /payments/webhook/**: HMAC Signature required. Body: `WebhookPaymentPayload`. Response: 200 `{"status": "ok"}`. (Compatibility alias).

## 16. Error Handling
- Pydantic strictly validates all incoming request models, returning structured `422 Unprocessable Entity` arrays on failure.
- A global exception handler catches custom domain exceptions (e.g., `NotFoundException`, `UnauthorizedException`) and maps them to clean `404`, `401`, `403`, and `409` HTTP JSON responses.

## 17. Security Review
*Implemented controls:*
- **Password Hashing:** `bcrypt` with max-byte checks.
- **JWT:** Used for sessionless authentication with expiration limits.
- **HMAC:** Constant-time `hmac.compare_digest` used for webhook signature verification.
- **Authorization & IDOR:** Explicit service-level checks filtering by JWT `sub`.
- **SQL Injection:** Mitigated entirely by SQLAlchemy ORM.
- **Idempotency & Concurrency:** Database `UNIQUE` constraints and `FOR UPDATE` locks.
- **Rate Limiting:** IP-based request throttling.

## 18. Testing Strategy
- **Framework:** `pytest` utilizing FastAPI's `TestClient`.
- **Isolation:** Tests run against an isolated SQLite in-memory/file database. SQLAlchemy `create_savepoint` wraps each test to ensure transactions are rolled back cleanly.
- **Coverage:** Extensive integration coverage for authentication (`test_auth.py`), bookings (`test_bookings.py`), catalogue (`test_centres.py`), webhooks (`test_webhooks.py`), payments (`test_payments.py`), payment aliases (`test_payment_aliases.py`), and retry behavior (`test_retry.py`).

## 19. Test Results
- **88 / 88 tests passed successfully.**
- Categories validated: Authentication logic, database constraints, JWT boundaries, rate-limit triggers, booking creation rules, payment generation, webhook signatures, idempotency, simulated concurrent failures, and alias routing.

## 20. Docker and Deployment
- **Dockerfile:** Utilizes the lightweight `python:3.12-slim` image. Installs OS dependencies required for `psycopg2`.
- **docker-compose.yml:** Defines `app` and `db` (postgres:16-alpine) services.
- **Integration:** The `app` service depends on `db` and uses a `pg_isready` healthcheck to ensure the database is fully initialized before starting the web server on port 8000.
- **Environment:** Configured seamlessly via `.env` variable ingestion.

## 21. Logging and Observability
- Implemented via `structlog`. Outputs contextual JSON logs in production for machine parsing (e.g., Elasticsearch, Datadog) and colorized output in development for readability. Logs capture events such as `payment_initiated` and `webhook_already_processed`.

## 22. Pagination
- Implemented directly on the `GET /centres` and `GET /bookings` endpoints. Accepts `page` and `page_size` query parameters, translated into SQLAlchemy `.offset()` and `.limit()` queries.

## 23. OpenAPI / Swagger
- Auto-generated interactive API documentation is available at `/docs` (Swagger UI) and `/redoc`. Pydantic models automatically populate the expected request schemas and response formats.

## 24. Configuration and Secrets
- **Implementation:** `pydantic-settings` maps environment variables to application configuration.
- **Secrets:** `JWT_SECRET_KEY` and `WEBHOOK_SECRET` are strictly excluded from source code tracking via `.gitignore`.
- **Template:** A safe `.env.example` file is provided to document necessary variables for new developers.

## 25. Limitations
- **Rate Limiting:** Built using `slowapi`, which stores state in application memory. This functions perfectly for a single node but does not share state across horizontally scaled pods.
- **Payments:** Purely simulated logic. Does not feature actual ledger accounting, real payment provider SDKs, or refund workflows.

## 26. Scalability Considerations
*(Future improvements, not currently implemented)*
- **Distributed Caching/Limiting:** Introduce Redis to back rate limiting and session validation across multiple worker nodes.
- **Durable Queues:** Move the `BackgroundTasks` gateway simulator to a durable message broker like RabbitMQ or Celery to ensure webhook generation survives application restarts.

## 27. Verification Checklist
- `git diff --check`: Clean (No whitespace errors).
- `pytest`: 88/88 passing.
- `docker compose build / up`: Successful.
- `alembic current`: Schema fully synchronized.
- `GET /docs`: Accessible and rendering properly.
- `Git status`: Clean, with `.env` correctly ignored.

## 28. Final Requirement Compliance
| Requirement | Status |
|---|---|
| Signup/Login & JWT | Implemented |
| Diagnostic Centres & Tests | Implemented |
| Booking Creation & Status | Implemented |
| Simulated Payments | Implemented |
| Idempotent Webhooks | Implemented |
| Docker & DB Setup | Implemented |
| Tests & Swagger | Implemented |
| Rate Limiting & Pagination | Implemented |

## 29. Conclusion
The EVE Healthcare Backend satisfies all core and bonus specifications defined in the assignment. The service exhibits strong software engineering principles, employing layered business logic, rigorous data validation, isolated integration testing, and defensive programming techniques. Features such as HMAC signature verification and row-level locking for webhook idempotency demonstrate an understanding of resilient, asynchronous systems design.

## 30. Submission Checklist
- [x] Application source code (`app/`)
- [x] Test suite (`tests/`)
- [x] Database migrations (`alembic/`)
- [x] Docker files (`Dockerfile`, `docker-compose.yml`)
- [x] Documentation (`README.md`, `FINAL_SUBMISSION_DOCUMENTATION.md`)
- [x] Original specification (`PROJECT_SPEC.md`)
- [x] Example configuration (`.env.example`)
- [x] GitHub repository tracking
- [x] Final verification and testing completed
