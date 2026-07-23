import enum


class Channel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class Priority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


PRIORITY_QUEUE_MAP: dict[Priority, str] = {
    Priority.CRITICAL: "critical",
    Priority.HIGH: "high",
    Priority.NORMAL: "normal",
    Priority.LOW: "low",
}

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2
IDEMPOTENCY_KEY_TTL_SECONDS = 86400
