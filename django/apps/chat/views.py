from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .exceptions import ChatMessageException
from .models import ChatMessage
from .permissions import IsChatMessageSender, IsChatMessageSenderOrReceiver
from .serializers import CreateChatMessageSerializer, ShortChatMessageSerializer, ListChatSerializer, \
    MessageInChatSerializer
from .services import ChatMessageService
from ..user.permissions import IsFullRegistered


@extend_schema_view(
    create=extend_schema(
        summary='Отправка сообщения пользователю',
        request=CreateChatMessageSerializer,
        responses={201: ShortChatMessageSerializer}
    ),
    my_chats=extend_schema(
        summary='Посмотреть список собственных чатов',
        responses={200: ListChatSerializer}
    ),
    destroy=extend_schema(
        summary='Удаление отправленного сообщения',
    ),
    retrieve=extend_schema(
        summary='Просмотр всех сообщений в определенном чате',
        responses={200: MessageInChatSerializer}
    )
)
class ChatMessageViewSet(viewsets.GenericViewSet, mixins.DestroyModelMixin):
    """ViewSet для карточек"""
    queryset = ChatMessage.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        match self.action:
            case 'create':
                return CreateChatMessageSerializer
            case 'my_chats':
                return ListChatSerializer
            case 'retrieve':
                return MessageInChatSerializer

    def get_permissions(self):
        match self.action:
            case 'destroy':
                self.permission_classes = (IsAuthenticated, IsFullRegistered, IsChatMessageSender)
            case 'retrieve':
                self.permission_classes = (IsAuthenticated, IsFullRegistered, IsChatMessageSenderOrReceiver)
            case _:
                self.permission_classes = (IsAuthenticated, IsFullRegistered)
        return [permission() for permission in self.permission_classes]

    def create(self, request):
        """Создать сообщение в чате"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['sender'] = request.user
        try:
            chat_message = ChatMessageService.create(**serializer.validated_data)
        except ChatMessageException as exc:
            raise ValidationError(str(exc))
        return Response(ShortChatMessageSerializer(chat_message).data, status=status.HTTP_201_CREATED)

    @action(methods=['GET'], detail=False, url_path='my-chats', url_name='my_chats')
    def my_chats(self, request):
        """Список собственных чатов (последних сообщений)"""
        queryset = ChatMessageService.get_chats_last_messages(user=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk):
        """Детальный просмотр чата со всеми сообщениями"""
        chat_message_service = ChatMessageService(chat_message=self.get_object())
        serializer = self.get_serializer(chat_message_service.get_chat(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
