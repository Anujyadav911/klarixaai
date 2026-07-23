# Notification Service

A centralized, production-grade notification service that delivers notifications across **Email**, **SMS**, and **Push** channels with priority queuing, delivery tracking, user preference management, and automatic retry mechanisms.

## Tech Stack

| Component | Technology | Rationale |
|---|---|---|
| Language | Python 3.12+ | Modern type hints, async/await support |
| Framework | FastAPI | Native async, automatic OpenAPI docs, Pydantic validation |
| Database | PostgreSQL | ACID compliant, JSONB support, robust indexing |
| ORM | SQLAlchemy 2.0 (Async) | Industry standard async ORM |
| Migrations | Alembic | Version-controlled schema changes |
| Queue | Celery + Redis | Priority queues, built-in retry with exponential backoff |
| Rate Limiting | Redis | Fast in-memory counters with TTL |
| Template Engine | Jinja2 | Variable substitution for message templates |
| Logging | structlog | Structured JSON logging for observability |
| Testing | Pytest + HTTPX | Async-native testing with full API coverage |

## Features

- **Multi-Channel Delivery**: Email, SMS, and Push notifications with per-channel delivery tracking
- **User Preferences**: Opt-in/opt-out per channel; service respects preferences before sending
- **Priority Queues**: Critical, High, Normal, Low — higher priority messages are processed first
- **Template Support**: Jinja2-based templates with variable substitution
- **Delivery Tracking**: Full lifecycle tracking (Pending → Queued → Processing → Sent → Delivered / Failed)
- **Retry Mechanism**: Exponential backoff with max 3 retries per delivery
- **Idempotency**: Duplicate requests with the same key return the existing notification
- **Rate Limiting**: Configurable per-user rate limit (default: 100/hour)
- **Structured Logging**: JSON logs for debugging and monitoring

## Setup Instructions

### Prerequisites
- Docker and Docker Compose

### Quick Start (Docker)

This is the recommended way to run and verify the project.

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd klarixaai
   ```

2. **Start all services in the background**:
   ```bash
   docker compose up --build -d
   ```

3. **Wait 10-15 seconds**, then **run database migrations**:
   ```bash
   docker compose exec api alembic upgrade head
   ```
   *(Note: If you ever need to reset the database and start fresh, run `docker compose down -v` before starting again).*

4. **Verify the API**:
   Open your browser and navigate to the interactive Swagger UI:
   - **http://localhost:8000/docs**
   
   This interface allows you to instantly test all endpoints without needing to write terminal commands.

### Local Development (without Docker)

1. **Install dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL and Redis** (must be running locally)

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your local DB/Redis URLs
   ```

4. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Start the API server**:
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Start the Celery worker**:
   ```bash
   celery -A app.worker.celery_app worker --loglevel=info -Q critical,high,normal,low
   ```

## How to Run Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests only
pytest tests/integration/ -v
```

## API Documentation

Interactive documentation is available at `/docs` (Swagger UI) when the server is running.

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/notifications` | Send a new notification |
| `GET` | `/notifications/{id}` | Get notification status and delivery details |
| `GET` | `/users/{user_id}/notifications` | Get notification history (paginated) |
| `POST` | `/users/{user_id}/preferences` | Set channel preferences |
| `GET` | `/users/{user_id}/preferences` | Get channel preferences |
| `GET` | `/health` | Service health check |

### Example: Send a Notification

*(Note: If you are using Windows PowerShell, you must use `curl.exe` instead of `curl`, or use the Swagger UI at `/docs`)*

```bash
curl -X POST http://localhost:8000/notifications \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "channels": ["email", "sms"],
    "priority": "high",
    "payload": {
      "subject": "Order Shipped",
      "body": "Hello {{name}}, your order {{order_id}} has shipped.",
      "variables": {"name": "Anuj", "order_id": "ORD-9876"}
    },
    "idempotency_key": "order-shipped-ORD-9876"
  }'
```

### Example: Set User Preferences

*(Note: If you are using Windows PowerShell, you must use `curl.exe` instead of `curl`)*

```bash
curl -X POST http://localhost:8000/users/user_123/preferences \
  -H "Content-Type: application/json" \
  -d '{
    "email_enabled": true,
    "sms_enabled": false,
    "push_enabled": true
  }'
```

## Assumptions

- Authentication/authorization is handled by an external API gateway; not implemented in this service.
- `user_id` references an external user service. Only the ID is stored.
- Mock providers simulate realistic latency and configurable failure rates but do not call external APIs.
- Templates can be created via migration seed data or direct DB insertion.
- Pagination defaults to 20 items per page.
- The parent notification status is an aggregation of its child delivery statuses.
