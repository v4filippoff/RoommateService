from django.db import transaction
from django.db.models import QuerySet, Q, Max

from .exceptions import ChatMessageException
from .models import ChatMessage
from ..user.models import User


class ChatMessageService:
    """Сервис для работы с сообщениями из чата"""

    def __init__(self, chat_message: ChatMessage):
        self._chat_message = chat_message

    @staticmethod
    @transaction.atomic
    def create(**chat_message_data) -> ChatMessage:
        """Создать сообщение в чате"""
        from apps.card.services import CardRequestService

        if chat_message_data['sender'] is None:
            chat_message = ChatMessage.objects.create(**chat_message_data)
        else:
            if chat_message_data['sender'] == chat_message_data['receiver']:
                raise ChatMessageException('Вы не можете отправить сообщение себе.')
            card_request = (CardRequestService.get_active_card_request_by_owner(user=chat_message_data['sender'], owner=chat_message_data['receiver']) or
                            CardRequestService.get_active_card_request_by_owner(user=chat_message_data['receiver'], owner=chat_message_data['sender']))
            if not card_request:
                raise ChatMessageException('Вы не можете отправить сообщение пользователю, т.к. никто из вас не подавал заявку на карточку.')
            chat_message = ChatMessage.objects.create(**chat_message_data, card=card_request.card)

        return chat_message

    @staticmethod
    def get_chats_last_messages(user: User) -> QuerySet[ChatMessage]:
        """Получить последние сообщения из чатов юзера"""
        last_messages = ChatMessage.objects.filter(Q(sender=user) | Q(receiver=user)).values('card').annotate(last_message_id=Max('id'))
        message_ids_sorted_by_created_date: set[int] = set(lm['last_message_id'] for lm in last_messages)
        return ChatMessage.objects.filter(id__in=message_ids_sorted_by_created_date).order_by('-id')

    def get_chat(self) -> QuerySet[ChatMessage]:
        """Получить чат по сообщению из него"""
        return ChatMessage.objects.filter(card=self._chat_message.card).order_by('-created_at')
