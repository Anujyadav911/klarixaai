import asyncio
import pytest

from app.providers.base import ProviderResponse
from app.providers.email_provider import MockEmailProvider
from app.providers.sms_provider import MockSMSProvider
from app.providers.push_provider import MockPushProvider
from app.providers import get_provider
from app.core.constants import Channel


class TestMockEmailProvider:
    @pytest.mark.asyncio
    async def test_send_returns_provider_response(self):
        provider = MockEmailProvider()
        response = await provider.send("user@test.com", "Subject", "Body")
        assert isinstance(response, ProviderResponse)
        assert isinstance(response.success, bool)

    @pytest.mark.asyncio
    async def test_successful_send_has_message_id(self):
        provider = MockEmailProvider()
        successes = 0
        for _ in range(20):
            response = await provider.send("user@test.com", "Subject", "Body")
            if response.success:
                assert response.provider_message_id.startswith("email-")
                assert response.raw_response["provider"] == "mock_email"
                successes += 1
        assert successes > 0


class TestMockSMSProvider:
    @pytest.mark.asyncio
    async def test_send_returns_provider_response(self):
        provider = MockSMSProvider()
        response = await provider.send("user_123", "Subject", "Body")
        assert isinstance(response, ProviderResponse)

    @pytest.mark.asyncio
    async def test_successful_send_has_sms_prefix(self):
        provider = MockSMSProvider()
        for _ in range(20):
            response = await provider.send("user_123", "Subject", "Body")
            if response.success:
                assert response.provider_message_id.startswith("sms-")
                break


class TestMockPushProvider:
    @pytest.mark.asyncio
    async def test_send_returns_provider_response(self):
        provider = MockPushProvider()
        response = await provider.send("user_123", "Subject", "Body")
        assert isinstance(response, ProviderResponse)

    @pytest.mark.asyncio
    async def test_successful_send_has_push_prefix(self):
        provider = MockPushProvider()
        for _ in range(20):
            response = await provider.send("user_123", "Subject", "Body")
            if response.success:
                assert response.provider_message_id.startswith("push-")
                break


class TestProviderFactory:
    def test_get_email_provider(self):
        provider = get_provider(Channel.EMAIL)
        assert isinstance(provider, MockEmailProvider)

    def test_get_sms_provider(self):
        provider = get_provider(Channel.SMS)
        assert isinstance(provider, MockSMSProvider)

    def test_get_push_provider(self):
        provider = get_provider(Channel.PUSH)
        assert isinstance(provider, MockPushProvider)
