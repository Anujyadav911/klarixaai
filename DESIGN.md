# Design Document

## High-Level Architecture

```
┌─────────────┐       ┌──────────────────────────────────────────────┐
│   Client     │──────▶│              FastAPI Application             │
└─────────────┘       │                                              │
                      │  ┌──────────┐  ┌───────────┐  ┌───────────┐ │
                      │  │  Input   │  │   Rate    │  │Idempotency│ │
                      │  │Validation│─▶│  Limiter  │─▶│  Check    │ │
                      │  └──────────┘  └───────────┘  └───────────┘ │
                      │        │                            │        │
                      │        ▼                            ▼        │
                      │  ┌───────────────────────────────────────┐   │
                      │  │         Notification Service          │   │
                      │  │  - Create notification record         │   │
                      │  │  - Check user preferences             │   │
                      │  │  - Create delivery records            │   │
                      │  │  - Dispatch to priority queue         │   │
                      │  └───────────────────────────────────────┘   │
                      └──────────────┬───────────────────────────────┘
                                     │
                      ┌──────────────┼──────────────────┐
                      │              │                  │
                      ▼              ▼                  ▼
               ┌──────────┐  ┌──────────────┐  ┌──────────────┐
               │PostgreSQL │  │    Redis     │  │    Redis     │
               │  (Data)   │  │  (Queues)   │  │(Rate Limits) │
               └──────────┘  └──────┬───────┘  └──────────────┘
                                     │
                      ┌──────────────┼──────────────────┐
                      │              │                  │
                      ▼              ▼                  ▼
               ┌──────────┐  ┌──────────────┐  ┌──────────────┐
               │ Critical  │  │    High      │  │ Normal/Low   │
               │  Queue    │  │   Queue      │  │   Queue      │
               └─────┬─────┘  └──────┬───────┘  └──────┬───────┘
                     │               │                  │
                     └───────────────┼──────────────────┘
                                     │
                              ┌──────┴───────┐
                              │Celery Workers│
                              │              │
                              │ ┌──────────┐ │
                              │ │ Template │ │
                              │ │ Render   │ │
                              │ └────┬─────┘ │
                              │      ▼       │
                              │ ┌──────────┐ │
                              │ │ Provider │ │
                              │ │ Layer    │ │
                              │ └────┬─────┘ │
                              │      ▼       │
                              │ ┌──────────┐ │
                              │ │ Update   │ │
                              │ │ Status   │ │
                              │ └──────────┘ │
                              └──────────────┘
```

## Database Schema

### Entity Relationship

```
templates (1) ──────< notifications (1) ──────< notification_deliveries (N)
                           │
user_preferences (1) ──────┘ (via user_id, no FK)
```

### Table: `notifications`

Stores the notification request. One record per API call.

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique identifier |
| user_id | VARCHAR(128) | Target user |
| idempotency_key | VARCHAR(256), unique | Client-provided deduplication key |
| priority | ENUM | critical, high, normal, low |
| template_id | UUID (FK → templates) | Optional template reference |
| payload | JSONB | Subject, body, and template variables |
| status | ENUM | Aggregated from child deliveries |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### Table: `notification_deliveries`

One record per channel per notification. Tracks individual delivery lifecycle.

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique identifier |
| notification_id | UUID (FK → notifications) | Parent notification |
| channel | ENUM | email, sms, push |
| status | ENUM | Per-channel delivery status |
| retry_count | INTEGER | Number of retry attempts |
| provider_response | JSONB | Raw provider response |
| error_message | TEXT | Last error on failure |
| sent_at | TIMESTAMP | When provider accepted |
| delivered_at | TIMESTAMP | When delivery confirmed |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### Table: `user_preferences`

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique identifier |
| user_id | VARCHAR(128), unique | User reference |
| email_enabled | BOOLEAN | Default: true |
| sms_enabled | BOOLEAN | Default: true |
| push_enabled | BOOLEAN | Default: true |

### Table: `templates`

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique identifier |
| name | VARCHAR(128), unique | Template identifier |
| subject | VARCHAR(512) | Subject with Jinja2 variables |
| body | TEXT | Body with Jinja2 variables |

## Failure Handling & Retries

### Retry Strategy
- **Mechanism**: Celery's built-in retry with `autoretry_for` exception handling
- **Backoff**: Exponential — approximately 2s, 4s, 8s between retries
- **Max Retries**: 3 attempts after the initial try (4 total)
- **On Exhaustion**: Delivery status is set to `FAILED`, error message is recorded

### Status Lifecycle
```
PENDING      → Record created in DB
QUEUED       → Task published to Celery queue
PROCESSING   → Worker picked up the task
SENT         → Provider accepted the message
DELIVERED    → Delivery confirmed (terminal)
FAILED       → All retries exhausted (terminal)
```

### Parent Notification Status Aggregation
The parent notification status is derived from its child deliveries:
- All `DELIVERED` → `DELIVERED`
- Any still in progress → `PROCESSING`
- All terminal, at least one `FAILED` → `FAILED`

### Dead Letter Queue (Future Enhancement)
In production, permanently failed tasks would be routed to a Dead Letter Queue for:
- Manual inspection and replay
- Alerting and monitoring
- Forensic analysis

This is documented but not implemented in the current scope.

## Scalability Considerations

### Current Design Supports
- **Horizontal scaling of workers**: Add more Celery workers to increase throughput
- **Database connection pooling**: SQLAlchemy async engine with configurable pool size
- **Priority processing**: Critical messages are processed before lower priorities
- **Async I/O**: FastAPI and SQLAlchemy async prevent thread blocking

### Production Scaling Path
- **Database**: Read replicas for GET endpoints, partitioning notifications by date
- **Queue**: Move from Redis to RabbitMQ or SQS for durability guarantees
- **Caching**: Cache user preferences in Redis to reduce DB reads
- **Sharding**: Shard notifications by user_id for horizontal DB scaling

## Trade-offs

| Decision | Trade-off |
|---|---|
| Redis for queues | Fast but less durable than RabbitMQ. Acceptable for this scope; production would use a persistent broker. |
| SQLite for tests | Simpler test setup, but some PostgreSQL-specific features (JSONB, enums) behave differently. Integration tests mock where needed. |
| Mock providers | No actual delivery, but exercises the full retry and status lifecycle. Configurable failure rate tests error paths. |
| Fixed-window rate limiting | Simpler than sliding window. Can allow brief bursts at window boundaries. Sufficient for this scope. |
| Sync Celery with async DB | Celery tasks run sync, so we create a new event loop per task. Acceptable overhead for this scale. |
