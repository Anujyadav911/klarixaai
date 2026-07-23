from fastapi import HTTPException, status


class NotificationNotFoundError(HTTPException):
    def __init__(self, notification_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found",
        )


class UserPreferencesNotFoundError(HTTPException):
    def __init__(self, user_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preferences for user {user_id} not found",
        )


class TemplateNotFoundError(HTTPException):
    def __init__(self, template_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found",
        )


class RateLimitExceededError(HTTPException):
    def __init__(self, user_id: str):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for user {user_id}",
        )


class DuplicateNotificationError(Exception):
    def __init__(self, idempotency_key: str, existing_id: str):
        self.idempotency_key = idempotency_key
        self.existing_id = existing_id
        super().__init__(f"Duplicate notification for idempotency key {idempotency_key}")


class ProviderError(Exception):
    def __init__(self, channel: str, message: str):
        self.channel = channel
        super().__init__(f"Provider error on {channel}: {message}")


class TemplateRenderError(Exception):
    def __init__(self, template_name: str, message: str):
        super().__init__(f"Failed to render template {template_name}: {message}")


class AllChannelsOptedOutError(HTTPException):
    def __init__(self, user_id: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"User {user_id} has opted out of all requested channels",
        )
