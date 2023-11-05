from dataclasses import dataclass

from apps.message.enums import MessageSendingStatus


@dataclass
class MessageDTO:
    """Абстрактное сообщение"""
    content: str
    recipients: list[str]


@dataclass
class MessageResultDTO:
    """Результат отправки сообщения"""
    status: MessageSendingStatus
    content: str | None = None
