import os
import time
from abc import ABCMeta, abstractmethod

from . import tasks
from .dto import MessageDTO, MessageResultDTO
from .enums import MessageSendingStatus, MessageType


class MessageSender(metaclass=ABCMeta):
    """Абстрактный класс для отправки сообщений пользователям"""

    def __init__(self, message: MessageDTO):
        self._message = message

    @abstractmethod
    def send(self) -> MessageResultDTO:
        """Отправить сообщение"""
        pass


def get_message_sender(message_type: MessageType, message: MessageDTO) -> MessageSender | None:
    """Получить экземпляр для отправки сообщения пользователю"""
    if os.getenv('APP_DEBUG') == '1':
        return TestSender(message)

    match message_type:
        case MessageType.SMS:
            return SMSGorodSender(message)
        case MessageType.EMAIL:
            return EmailSender(message)
        case MessageType.CALL:
            return CallSender(message)
        case _:
            return None


class SMSGorodSender(MessageSender):
    """Отправитель смс сообщений (сторонний сервис sms gorod)"""

    api_url = os.getenv('SMSGOROD_API_URL')
    api_key = os.getenv('SMSGOROD_API_KEY')

    def send(self) -> MessageResultDTO:
        json_data = {
            'apiKey': self.api_key,
            'sms': [
                {
                    'channel': 'digit',
                    'text': self._message.content,
                    'phone': r.replace('+', ''),
                    'plannedAt': int(time.time())
                }
                for r in self._message.recipients
            ]
        }
        tasks.send_message.apply_async(args=(self.api_url, self._get_default_headers(), json_data))
        return MessageResultDTO(status=MessageSendingStatus.PENDING)

    def _get_default_headers(self) -> dict:
        return {}


class EmailSender(MessageSender):
    """Отправитель email сообщений"""

    def send(self) -> MessageResultDTO:
        pass


class CallSender(MessageSender):
    """Отправитель сообщений по телефонному звонку"""

    def send(self) -> MessageResultDTO:
        pass


class TestSender(MessageSender):
    """Отправитель-заглушка для тестирования"""

    def send(self) -> MessageResultDTO:
        print(self._message)
        return MessageResultDTO(status=MessageSendingStatus.DELIVERED)
