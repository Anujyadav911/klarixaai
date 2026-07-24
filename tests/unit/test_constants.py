import pytest

from app.core.constants import Channel, DeliveryStatus, Priority, PRIORITY_QUEUE_MAP, MAX_RETRIES
from app.core.exceptions import (
    NotificationNotFoundError,
    RateLimitExceededError,
    TemplateNotFoundError,
    AllChannelsOptedOutError,
    ProviderError,
    DuplicateNotificationError,
)


class TestEnums:
    def test_channel_values(self):
        assert Channel.EMAIL.value == "email"
        assert Channel.SMS.value == "sms"
        assert Channel.PUSH.value == "push"

    def test_priority_values(self):
        assert Priority.CRITICAL.value == "critical"
        assert Priority.HIGH.value == "high"
        assert Priority.NORMAL.value == "normal"
        assert Priority.LOW.value == "low"

    def test_delivery_status_values(self):
        assert DeliveryStatus.PENDING.value == "pending"
        assert DeliveryStatus.QUEUED.value == "queued"
        assert DeliveryStatus.PROCESSING.value == "processing"
        assert DeliveryStatus.SENT.value == "sent"
        assert DeliveryStatus.DELIVERED.value == "delivered"
        assert DeliveryStatus.FAILED.value == "failed"

    def test_priority_queue_map(self):
        assert PRIORITY_QUEUE_MAP[Priority.CRITICAL] == "critical"
        assert PRIORITY_QUEUE_MAP[Priority.HIGH] == "high"
        assert PRIORITY_QUEUE_MAP[Priority.NORMAL] == "normal"
        assert PRIORITY_QUEUE_MAP[Priority.LOW] == "low"

    def test_max_retries(self):
        assert MAX_RETRIES == 3


class TestExceptions:
    def test_notification_not_found(self):
        exc = NotificationNotFoundError("abc-123")
        assert exc.status_code == 404
        assert "abc-123" in exc.detail

    def test_rate_limit_exceeded(self):
        exc = RateLimitExceededError("user_1")
        assert exc.status_code == 429
        assert "user_1" in exc.detail

    def test_template_not_found(self):
        exc = TemplateNotFoundError("tmpl-1")
        assert exc.status_code == 404

    def test_all_channels_opted_out(self):
        exc = AllChannelsOptedOutError("user_1")
        assert exc.status_code == 422

    def test_provider_error(self):
        exc = ProviderError("email", "timeout")
        assert "email" in str(exc)

    def test_duplicate_notification(self):
        exc = DuplicateNotificationError("key-1", "id-1")
        assert exc.idempotency_key == "key-1"
        assert exc.existing_id == "id-1"
