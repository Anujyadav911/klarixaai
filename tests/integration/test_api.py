import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio


@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_health_check(self, client):
        with patch("app.api.health.engine") as mock_engine, \
             patch("app.api.health.get_redis_client", new_callable=AsyncMock) as mock_redis:

            mock_conn = AsyncMock()
            mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_conn.__aexit__ = AsyncMock(return_value=False)
            mock_conn.execute = AsyncMock()
            mock_engine.connect.return_value = mock_conn

            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_redis.return_value = mock_client

            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"


@pytest.mark.asyncio
class TestPreferencesAPI:
    async def test_set_preferences(self, client, sample_preference_payload):
        response = await client.post("/users/user_123/preferences", json=sample_preference_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user_123"
        assert data["email_enabled"] is True
        assert data["sms_enabled"] is False
        assert data["push_enabled"] is True

    async def test_get_preferences(self, client, sample_preference_payload):
        await client.post("/users/user_456/preferences", json=sample_preference_payload)
        response = await client.get("/users/user_456/preferences")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user_456"

    async def test_get_preferences_not_found(self, client):
        response = await client.get("/users/nonexistent/preferences")
        assert response.status_code == 404

    async def test_update_preferences(self, client):
        await client.post("/users/user_789/preferences", json={"email_enabled": True, "sms_enabled": True, "push_enabled": True})
        response = await client.post("/users/user_789/preferences", json={"email_enabled": False, "sms_enabled": False, "push_enabled": False})
        assert response.status_code == 200
        data = response.json()
        assert data["email_enabled"] is False
        assert data["sms_enabled"] is False
        assert data["push_enabled"] is False


@pytest.mark.asyncio
class TestNotificationsAPI:
    async def test_send_notification(self, client, sample_notification_payload):
        with patch("app.services.notification_service.check_rate_limit", new_callable=AsyncMock), \
             patch("app.services.notification_service.check_idempotency_key", new_callable=AsyncMock, return_value=None), \
             patch("app.services.notification_service.set_idempotency_key", new_callable=AsyncMock), \
             patch("app.worker.tasks.process_delivery.apply_async"):

            response = await client.post("/notifications", json=sample_notification_payload)
            assert response.status_code == 202
            data = response.json()
            assert data["user_id"] == "user_123"
            assert data["priority"] == "high"
            assert data["status"] in ["pending", "queued"]
            assert len(data["deliveries"]) == 2

    async def test_get_notification_by_id(self, client, sample_notification_payload):
        with patch("app.services.notification_service.check_rate_limit", new_callable=AsyncMock), \
             patch("app.services.notification_service.check_idempotency_key", new_callable=AsyncMock, return_value=None), \
             patch("app.services.notification_service.set_idempotency_key", new_callable=AsyncMock), \
             patch("app.worker.tasks.process_delivery.apply_async"):

            sample_notification_payload["idempotency_key"] = f"test-{uuid.uuid4().hex[:8]}"
            create_response = await client.post("/notifications", json=sample_notification_payload)
            notification_id = create_response.json()["id"]

            response = await client.get(f"/notifications/{notification_id}")
            assert response.status_code == 200
            assert response.json()["id"] == notification_id

    async def test_get_notification_not_found(self, client):
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/notifications/{fake_id}")
        assert response.status_code == 404

    async def test_get_user_notifications(self, client, sample_notification_payload):
        with patch("app.services.notification_service.check_rate_limit", new_callable=AsyncMock), \
             patch("app.services.notification_service.check_idempotency_key", new_callable=AsyncMock, return_value=None), \
             patch("app.services.notification_service.set_idempotency_key", new_callable=AsyncMock), \
             patch("app.worker.tasks.process_delivery.apply_async"):

            sample_notification_payload["idempotency_key"] = f"test-{uuid.uuid4().hex[:8]}"
            await client.post("/notifications", json=sample_notification_payload)

            response = await client.get("/users/user_123/notifications")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert data["total"] >= 1

    async def test_send_notification_invalid_payload(self, client):
        response = await client.post("/notifications", json={})
        assert response.status_code == 422

    async def test_send_notification_empty_channels(self, client):
        payload = {
            "user_id": "user_123",
            "channels": [],
            "priority": "normal",
        }
        response = await client.post("/notifications", json=payload)
        assert response.status_code == 422

    async def test_send_notification_respects_preferences(self, client):
        await client.post("/users/pref_user/preferences", json={
            "email_enabled": False,
            "sms_enabled": False,
            "push_enabled": False,
        })

        with patch("app.services.notification_service.check_rate_limit", new_callable=AsyncMock), \
             patch("app.services.notification_service.check_idempotency_key", new_callable=AsyncMock, return_value=None):

            payload = {
                "user_id": "pref_user",
                "channels": ["email", "sms"],
                "priority": "normal",
                "idempotency_key": f"test-{uuid.uuid4().hex[:8]}",
            }
            response = await client.post("/notifications", json=payload)
            assert response.status_code == 422

    async def test_idempotency_returns_existing(self, client, sample_notification_payload):
        idem_key = f"idem-{uuid.uuid4().hex[:8]}"
        sample_notification_payload["idempotency_key"] = idem_key

        with patch("app.services.notification_service.check_rate_limit", new_callable=AsyncMock), \
             patch("app.services.notification_service.check_idempotency_key", new_callable=AsyncMock, return_value=None), \
             patch("app.services.notification_service.set_idempotency_key", new_callable=AsyncMock), \
             patch("app.worker.tasks.process_delivery.apply_async"):

            first_response = await client.post("/notifications", json=sample_notification_payload)
            first_id = first_response.json()["id"]

        with patch("app.services.notification_service.check_rate_limit", new_callable=AsyncMock), \
             patch("app.services.notification_service.check_idempotency_key", new_callable=AsyncMock, return_value=first_id), \
             patch("app.services.notification_service.set_idempotency_key", new_callable=AsyncMock):

            second_response = await client.post("/notifications", json=sample_notification_payload)
            assert second_response.status_code == 202
            assert second_response.json()["id"] == first_id
