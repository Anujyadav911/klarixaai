from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ProviderResponse:
    success: bool
    provider_message_id: str = ""
    raw_response: dict = field(default_factory=dict)
    error_message: str = ""


class BaseProvider(ABC):
    @abstractmethod
    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        metadata: dict | None = None,
    ) -> ProviderResponse:
        pass
