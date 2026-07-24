from app.core.constants import Channel
from app.providers.base import BaseProvider
from app.providers.email_provider import MockEmailProvider
from app.providers.sms_provider import MockSMSProvider
from app.providers.push_provider import MockPushProvider


def get_provider(channel: Channel) -> BaseProvider:
    providers: dict[Channel, BaseProvider] = {
        Channel.EMAIL: MockEmailProvider(),
        Channel.SMS: MockSMSProvider(),
        Channel.PUSH: MockPushProvider(),
    }
    return providers[channel]
